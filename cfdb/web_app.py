from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .codeforces import CodeforcesApiError, CodeforcesClient
from .db import DEFAULT_DB_PATH, ROOT, init_db
from .progress_sync import sync_codeforces_progress
from .user_state import (
    connect_catalog_with_user,
    init_user_db,
    patch_user_state,
    read_settings,
    read_user_state,
    resolve_user_db_path,
    update_settings,
)
from .web_models import (
    AnalyticsModel,
    ProblemDetailModel,
    SearchResponseModel,
    SettingsModel,
    SettingsPatch,
    SyncRequest,
    SyncResultModel,
    TagNodeModel,
    UserStateModel,
    UserStatePatch,
)
from .web_search import SearchOptions, analytics_catalog, search_catalog


CANONICAL_SQL = "(p.canonical_problem_uid IS NULL OR p.canonical_problem_uid = p.problem_uid)"


def _json_list(value: str | None) -> list[object]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _expand_query_values(values: list[str] | None) -> tuple[str, ...]:
    expanded: list[str] = []
    for value in values or []:
        expanded.extend(item.strip() for item in value.split(",") if item.strip())
    return tuple(expanded)


def _display_name(tag: str, explicit: str | None) -> str:
    return explicit or tag.rsplit("/", 1)[-1].replace("-", " ").title()


def _tag_tree(conn, counts: dict[str, int]) -> list[dict[str, object]]:  # type: ignore[no-untyped-def]
    tag_rows = conn.execute(
        "SELECT tag, display_name, description, status FROM tags ORDER BY tag"
    ).fetchall()
    edge_rows = conn.execute(
        "SELECT parent_tag, child_tag FROM tag_edges ORDER BY parent_tag, child_tag"
    ).fetchall()
    tags = {str(row["tag"]): dict(row) for row in tag_rows}
    children: dict[str, list[str]] = {tag: [] for tag in tags}
    incoming: set[str] = set()
    for edge in edge_rows:
        parent = str(edge["parent_tag"])
        child = str(edge["child_tag"])
        if parent in tags and child in tags:
            children[parent].append(child)
            incoming.add(child)

    def build(tag: str, path: set[str]) -> dict[str, object]:
        row = tags[tag]
        return {
            "tag": tag,
            "display_name": _display_name(tag, row.get("display_name")),
            "description": row.get("description") or "",
            "status": row.get("status") or "candidate",
            "problem_count": int(counts.get(tag, 0)),
            "children": [
                build(child, {*path, tag})
                for child in children.get(tag, [])
                if child not in path
            ],
        }

    return [build(tag, set()) for tag in sorted(tags) if tag not in incoming]


def _problem_detail(conn, problem_uid: str) -> dict[str, object] | None:  # type: ignore[no-untyped-def]
    row = conn.execute(
        f"""
        SELECT
            p.*, c.title AS contest_title, c.start_time_utc,
            a.summary, a.constraints_text, a.core_idea, a.complexity,
            a.tricks_json, a.confidence, a.review_status, a.last_reviewed_at
        FROM problems p
        JOIN contests c ON c.contest_id = p.contest_id
        LEFT JOIN problem_annotations a ON a.problem_uid = p.problem_uid
        WHERE p.problem_uid = ? AND {CANONICAL_SQL}
        """,
        (problem_uid,),
    ).fetchone()
    if row is None:
        return None

    tag_rows = conn.execute(
        """
        SELECT pt.tag, pt.importance, pt.evidence, pt.source,
               sv.variant_name AS solution_variant
        FROM problem_tags pt
        LEFT JOIN solution_variants sv ON sv.id = pt.solution_variant_id
        WHERE pt.problem_uid = ?
        ORDER BY CASE pt.importance
            WHEN 'primary' THEN 0 WHEN 'secondary' THEN 1 ELSE 2 END,
            pt.tag, pt.source
        """,
        (problem_uid,),
    ).fetchall()
    variant_rows = conn.execute(
        """
        SELECT variant_name, summary, complexity, confidence, is_primary
        FROM solution_variants WHERE problem_uid = ?
        ORDER BY is_primary DESC, variant_name
        """,
        (problem_uid,),
    ).fetchall()
    source_rows = conn.execute(
        """
        SELECT source_type, url, fetched_at, notes
        FROM problem_sources WHERE problem_uid = ?
        ORDER BY source_type, url
        """,
        (problem_uid,),
    ).fetchall()
    alias_rows = conn.execute(
        """
        SELECT alias_problem_uid, alias_contest_id, alias_problem_index, reason
        FROM problem_aliases WHERE canonical_problem_uid = ?
        ORDER BY alias_contest_id, alias_problem_index
        """,
        (problem_uid,),
    ).fetchall()

    return {
        "problem_uid": row["problem_uid"],
        "contest_id": row["contest_id"],
        "problem_index": row["problem_index"],
        "label": f"{row['contest_id']}{row['problem_index']}",
        "title": row["title"],
        "contest_title": row["contest_title"],
        "start_time_utc": row["start_time_utc"],
        "rating": row["rating"],
        "rating_status": row["rating_status"],
        "canonical_url": row["canonical_url"],
        "problemset_url": row["problemset_url"],
        "official_tags": _json_list(row["official_tags_json"]),
        "annotation": {
            "summary": row["summary"] or "",
            "constraints": row["constraints_text"] or "",
            "core_idea": row["core_idea"] or "",
            "complexity": row["complexity"] or "",
            "tricks": _json_list(row["tricks_json"]),
            "confidence": row["confidence"],
            "review_status": row["review_status"],
            "last_reviewed_at": row["last_reviewed_at"],
        },
        "tags": [dict(tag_row) for tag_row in tag_rows],
        "solution_variants": [
            {**dict(variant), "is_primary": bool(variant["is_primary"])}
            for variant in variant_rows
        ],
        "sources": [dict(source) for source in source_rows],
        "aliases": [dict(alias) for alias in alias_rows],
        "user_state": read_user_state(conn, problem_uid),
    }


def _options(
    *,
    rating_min: int | None,
    rating_max: int | None,
    rating_status: list[str] | None,
    importance: list[str] | None,
    tags: list[str] | None,
    exclude: list[str] | None,
    tag_mode: str,
    favorite: str,
    progress_status: list[str] | None,
    priority: list[str] | None,
    q: str | None,
    sort_by: str,
    sort_order: str,
    limit: int,
    offset: int,
) -> SearchOptions:
    if tag_mode not in {"and", "or"}:
        raise HTTPException(status_code=422, detail="tag_mode must be and/or")
    if favorite not in {"any", "favorite", "not_favorite"}:
        raise HTTPException(status_code=422, detail="invalid favorite filter")
    if sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=422, detail="invalid sort order")
    return SearchOptions(
        rating_min=rating_min,
        rating_max=rating_max,
        rating_statuses=_expand_query_values(rating_status),
        importance=_expand_query_values(importance),
        tags=_expand_query_values(tags),
        exclude_tags=_expand_query_values(exclude),
        tag_mode=tag_mode,
        favorite=favorite,
        progress_statuses=_expand_query_values(progress_status),
        priorities=_expand_query_values(priority),
        query=q,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )


def _public_search_result(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if not key.startswith("_")}


def create_app(
    db_path: str | Path | None = None,
    user_db_path: str | Path | None = None,
    codeforces_client: CodeforcesClient | None = None,
) -> FastAPI:
    database_path = Path(db_path or os.environ.get("CFDB_PATH", DEFAULT_DB_PATH))
    if not database_path.exists():
        init_db(database_path)
    user_path = (
        Path(user_db_path)
        if user_db_path is not None
        else (
            database_path.with_name(f"{database_path.stem}.user.sqlite")
            if db_path is not None
            else resolve_user_db_path()
        )
    )
    init_user_db(user_path, database_path)

    app = FastAPI(title="Codeforces Problem Database")
    app.state.db_path = database_path
    app.state.user_db_path = user_path
    app.state.codeforces_client = codeforces_client
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/stats")
    def stats() -> dict[str, int]:
        with connect_catalog_with_user(database_path, user_path) as conn:
            result = search_catalog(conn, SearchOptions())
            reviewed = conn.execute(
                f"""
                SELECT COUNT(*) AS count FROM problem_annotations a
                JOIN problems p ON p.problem_uid=a.problem_uid
                WHERE {CANONICAL_SQL} AND a.review_status='reviewed'
                """
            ).fetchone()["count"]
            tag_count = conn.execute("SELECT COUNT(*) AS count FROM tags").fetchone()["count"]
        return {
            "canonical_problems": int(result["summary"]["total"]),
            "reviewed_problems": int(reviewed),
            "tags": int(tag_count),
            "favorites": int(result["summary"]["favorites"]),
        }

    @app.get("/api/tags", response_model=list[TagNodeModel])
    def tags_route() -> list[dict[str, object]]:
        with connect_catalog_with_user(database_path, user_path) as conn:
            result = search_catalog(
                conn, SearchOptions(importance=("primary", "secondary"))
            )
            return _tag_tree(conn, result["facets"]["tag_counts"])

    @app.get("/api/search", response_model=SearchResponseModel)
    def search_route(
        rating_min: int | None = None,
        rating_max: int | None = None,
        rating_status: Annotated[list[str] | None, Query()] = None,
        importance: Annotated[list[str] | None, Query()] = None,
        tags: Annotated[list[str] | None, Query()] = None,
        exclude: Annotated[list[str] | None, Query()] = None,
        tag_mode: str = "and",
        favorite: str = "any",
        progress_status: Annotated[list[str] | None, Query()] = None,
        priority: Annotated[list[str] | None, Query()] = None,
        q: str | None = None,
        sort_by: str = "rating",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        options = _options(
            rating_min=rating_min,
            rating_max=rating_max,
            rating_status=rating_status,
            importance=importance,
            tags=tags,
            exclude=exclude,
            tag_mode=tag_mode,
            favorite=favorite,
            progress_status=progress_status,
            priority=priority,
            q=q,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
        with connect_catalog_with_user(database_path, user_path) as conn:
            return _public_search_result(search_catalog(conn, options))

    @app.get("/api/analytics", response_model=AnalyticsModel)
    def analytics_route(
        scope: str = "current",
        rating_min: int | None = None,
        rating_max: int | None = None,
        rating_status: Annotated[list[str] | None, Query()] = None,
        importance: Annotated[list[str] | None, Query()] = None,
        tags: Annotated[list[str] | None, Query()] = None,
        exclude: Annotated[list[str] | None, Query()] = None,
        tag_mode: str = "and",
        favorite: str = "any",
        progress_status: Annotated[list[str] | None, Query()] = None,
        priority: Annotated[list[str] | None, Query()] = None,
        q: str | None = None,
    ) -> dict[str, Any]:
        if scope not in {"current", "global"}:
            raise HTTPException(status_code=422, detail="scope must be current/global")
        options = _options(
            rating_min=rating_min,
            rating_max=rating_max,
            rating_status=rating_status,
            importance=importance,
            tags=tags,
            exclude=exclude,
            tag_mode=tag_mode,
            favorite=favorite,
            progress_status=progress_status,
            priority=priority,
            q=q,
            sort_by="rating",
            sort_order="asc",
            limit=50,
            offset=0,
        )
        with connect_catalog_with_user(database_path, user_path) as conn:
            return analytics_catalog(conn, options, scope=scope)

    @app.get("/api/problems/{problem_uid:path}", response_model=ProblemDetailModel)
    def problem_route(problem_uid: str) -> dict[str, object]:
        with connect_catalog_with_user(database_path, user_path) as conn:
            detail = _problem_detail(conn, problem_uid)
        if detail is None:
            raise HTTPException(status_code=404, detail="problem not found")
        return detail

    @app.patch(
        "/api/problems/{problem_uid:path}/user-state",
        response_model=UserStateModel,
    )
    def update_user_state_route(problem_uid: str, state: UserStatePatch) -> dict[str, object]:
        with connect_catalog_with_user(database_path, user_path) as conn:
            exists = conn.execute(
                f"SELECT 1 FROM problems p WHERE p.problem_uid=? AND {CANONICAL_SQL}",
                (problem_uid,),
            ).fetchone()
            if exists is None:
                raise HTTPException(status_code=404, detail="problem not found")
            try:
                return patch_user_state(
                    conn, problem_uid, state.model_dump(exclude_unset=True)
                )
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/settings", response_model=SettingsModel)
    def settings_route() -> dict[str, object]:
        return read_settings(user_path)

    @app.patch("/api/settings", response_model=SettingsModel)
    def update_settings_route(settings: SettingsPatch) -> dict[str, object]:
        try:
            return update_settings(
                user_path,
                settings.model_dump(exclude_unset=True, exclude_none=True),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/sync/codeforces", response_model=SyncResultModel)
    def sync_route(request: SyncRequest) -> dict[str, object]:
        try:
            return sync_codeforces_progress(
                database_path,
                user_path,
                full=request.full,
                client=app.state.codeforces_client,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except CodeforcesApiError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except OSError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    dist_dir = ROOT / "web" / "dist"
    if dist_dir.exists():
        assets_dir = dist_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            target = dist_dir / path
            if path and target.exists() and target.is_file():
                return FileResponse(target)
            return FileResponse(dist_dir / "index.html")

    return app


app = create_app()
