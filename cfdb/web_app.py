from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db import DEFAULT_DB_PATH, ROOT, connect, init_db
from .search import DEFAULT_IMPORTANCE, DEFAULT_RATING_STATUSES, search_problems
from .tags import descendants


CANONICAL_SQL = "(p.canonical_problem_uid IS NULL OR p.canonical_problem_uid = p.problem_uid)"


class UserStateInput(BaseModel):
    favorite: bool = False
    note: str = ""


def _json_list(value: str | None) -> list[object]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _expand_query_values(values: list[str] | None) -> list[str]:
    expanded: list[str] = []
    for value in values or []:
        expanded.extend(item.strip() for item in value.split(",") if item.strip())
    return expanded


def _display_name(tag: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    return tag.rsplit("/", 1)[-1].replace("-", " ").title()


def _tag_problem_count(conn, tag: str) -> int:  # type: ignore[no-untyped-def]
    expanded = descendants(conn, tag)
    placeholders = ",".join("?" for _ in expanded)
    row = conn.execute(
        f"""
        SELECT COUNT(DISTINCT p.problem_uid) AS count
        FROM problems p
        JOIN problem_tags pt ON pt.problem_uid = p.problem_uid
        WHERE {CANONICAL_SQL}
          AND pt.importance IN ('primary', 'secondary')
          AND pt.tag IN ({placeholders})
        """,
        expanded,
    ).fetchone()
    return int(row["count"])


def _tag_tree(conn) -> list[dict[str, object]]:  # type: ignore[no-untyped-def]
    tag_rows = conn.execute(
        "SELECT tag, display_name, description, status FROM tags ORDER BY tag"
    ).fetchall()
    edge_rows = conn.execute(
        "SELECT parent_tag, child_tag FROM tag_edges ORDER BY parent_tag, child_tag"
    ).fetchall()
    tags = {row["tag"]: dict(row) for row in tag_rows}
    children: dict[str, list[str]] = {tag: [] for tag in tags}
    incoming: set[str] = set()
    for edge in edge_rows:
        if edge["parent_tag"] in tags and edge["child_tag"] in tags:
            children.setdefault(edge["parent_tag"], []).append(edge["child_tag"])
            incoming.add(edge["child_tag"])

    def build(tag: str, path: set[str]) -> dict[str, object]:
        row = tags[tag]
        next_path = {*path, tag}
        child_nodes = [
            build(child, next_path)
            for child in children.get(tag, [])
            if child not in path
        ]
        return {
            "tag": tag,
            "display_name": _display_name(tag, row.get("display_name")),
            "description": row.get("description") or "",
            "status": row.get("status"),
            "problem_count": _tag_problem_count(conn, tag),
            "children": child_nodes,
        }

    roots = [tag for tag in sorted(tags) if tag not in incoming]
    return [build(tag, set()) for tag in roots]


def _problem_detail(conn, problem_uid: str) -> dict[str, object] | None:  # type: ignore[no-untyped-def]
    row = conn.execute(
        f"""
        SELECT
            p.*, c.title AS contest_title, c.start_time_utc,
            a.summary, a.constraints_text, a.core_idea, a.complexity,
            a.tricks_json, a.confidence, a.review_status, a.last_reviewed_at,
            COALESCE(us.favorite, 0) AS favorite,
            COALESCE(us.note, '') AS note,
            us.updated_at AS user_state_updated_at
        FROM problems p
        JOIN contests c ON c.contest_id = p.contest_id
        LEFT JOIN problem_annotations a ON a.problem_uid = p.problem_uid
        LEFT JOIN problem_user_state us ON us.problem_uid = p.problem_uid
        WHERE p.problem_uid = ?
          AND {CANONICAL_SQL}
        """,
        (problem_uid,),
    ).fetchone()
    if row is None:
        return None

    tag_rows = conn.execute(
        """
        SELECT pt.tag, pt.importance, pt.evidence, pt.source, sv.variant_name AS solution_variant
        FROM problem_tags pt
        LEFT JOIN solution_variants sv ON sv.id = pt.solution_variant_id
        WHERE pt.problem_uid = ?
        ORDER BY
            CASE pt.importance
                WHEN 'primary' THEN 0
                WHEN 'secondary' THEN 1
                ELSE 2
            END,
            pt.tag,
            pt.source
        """,
        (problem_uid,),
    ).fetchall()
    variant_rows = conn.execute(
        """
        SELECT variant_name, summary, complexity, confidence, is_primary
        FROM solution_variants
        WHERE problem_uid = ?
        ORDER BY is_primary DESC, variant_name
        """,
        (problem_uid,),
    ).fetchall()
    source_rows = conn.execute(
        """
        SELECT source_type, url, fetched_at, notes
        FROM problem_sources
        WHERE problem_uid = ?
        ORDER BY source_type, url
        """,
        (problem_uid,),
    ).fetchall()
    alias_rows = conn.execute(
        """
        SELECT alias_problem_uid, alias_contest_id, alias_problem_index, reason
        FROM problem_aliases
        WHERE canonical_problem_uid = ?
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
            {
                **dict(variant_row),
                "is_primary": bool(variant_row["is_primary"]),
            }
            for variant_row in variant_rows
        ],
        "sources": [dict(source_row) for source_row in source_rows],
        "aliases": [dict(alias_row) for alias_row in alias_rows],
        "user_state": {
            "favorite": bool(row["favorite"]),
            "note": row["note"],
            "updated_at": row["user_state_updated_at"],
        },
    }


def create_app(db_path: str | Path | None = None) -> FastAPI:
    database_path = Path(db_path or os.environ.get("CFDB_PATH", DEFAULT_DB_PATH))
    init_db(database_path)
    app = FastAPI(title="Codeforces Problem Database")
    app.state.db_path = database_path
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/stats")
    def stats() -> dict[str, int]:
        with connect(app.state.db_path) as conn:
            canonical = conn.execute(
                f"SELECT COUNT(*) AS count FROM problems p WHERE {CANONICAL_SQL}"
            ).fetchone()["count"]
            reviewed = conn.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM problem_annotations a
                JOIN problems p ON p.problem_uid = a.problem_uid
                WHERE {CANONICAL_SQL} AND a.review_status = 'reviewed'
                """
            ).fetchone()["count"]
            tags = conn.execute("SELECT COUNT(*) AS count FROM tags").fetchone()["count"]
            favorites = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM problem_user_state us
                JOIN problems p ON p.problem_uid = us.problem_uid
                WHERE us.favorite = 1
                  AND (p.canonical_problem_uid IS NULL OR p.canonical_problem_uid = p.problem_uid)
                """
            ).fetchone()["count"]
        return {
            "canonical_problems": int(canonical),
            "reviewed_problems": int(reviewed),
            "tags": int(tags),
            "favorites": int(favorites),
        }

    @app.get("/api/tags")
    def tags() -> list[dict[str, object]]:
        with connect(app.state.db_path) as conn:
            return _tag_tree(conn)

    @app.get("/api/search")
    def search(
        rating_min: int | None = None,
        rating_max: int | None = None,
        rating_status: Annotated[list[str] | None, Query()] = None,
        importance: Annotated[list[str] | None, Query()] = None,
        tags: Annotated[list[str] | None, Query()] = None,
        exclude: Annotated[list[str] | None, Query()] = None,
        tag_mode: str = "and",
        favorite_only: bool = False,
        q: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, object]:
        rating_statuses = tuple(_expand_query_values(rating_status)) or DEFAULT_RATING_STATUSES
        importance_values = tuple(_expand_query_values(importance)) or DEFAULT_IMPORTANCE
        selected_tags = _expand_query_values(tags)
        excluded_tags = _expand_query_values(exclude)
        with connect(app.state.db_path) as conn:
            items = search_problems(
                conn,
                rating_min=rating_min,
                rating_max=rating_max,
                tags=selected_tags,
                exclude_tags=excluded_tags,
                importance=importance_values,
                rating_statuses=rating_statuses,
                tag_mode=tag_mode,
                query_text=q,
                favorite_only=favorite_only,
                limit=max(1, min(limit, 500)),
                offset=max(0, offset),
            )
        for item in items:
            item["label"] = f"{item['contest_id']}{item['problem_index']}"
            item["favorite"] = bool(item.get("favorite"))
        return {"items": items, "limit": limit, "offset": offset}

    @app.get("/api/problems/{problem_uid:path}")
    def problem(problem_uid: str) -> dict[str, object]:
        with connect(app.state.db_path) as conn:
            detail = _problem_detail(conn, problem_uid)
        if detail is None:
            raise HTTPException(status_code=404, detail="problem not found")
        return detail

    @app.patch("/api/problems/{problem_uid:path}/user-state")
    def update_user_state(problem_uid: str, state: UserStateInput) -> dict[str, object]:
        with connect(app.state.db_path) as conn:
            exists = conn.execute(
                f"SELECT 1 FROM problems p WHERE p.problem_uid = ? AND {CANONICAL_SQL}",
                (problem_uid,),
            ).fetchone()
            if exists is None:
                raise HTTPException(status_code=404, detail="problem not found")
            conn.execute(
                """
                INSERT INTO problem_user_state(problem_uid, favorite, note, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(problem_uid) DO UPDATE SET
                    favorite = excluded.favorite,
                    note = excluded.note,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (problem_uid, 1 if state.favorite else 0, state.note),
            )
            detail = _problem_detail(conn, problem_uid)
        if detail is None:
            raise HTTPException(status_code=404, detail="problem not found")
        return detail["user_state"]  # type: ignore[return-value]

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
