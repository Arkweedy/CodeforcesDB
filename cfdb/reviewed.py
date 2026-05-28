from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .dedup import canonical_problem_uid
from .normalize import normalize_problem_key, contest_uid
from .tags import TagInput, add_alias, ensure_tag, resolve_tag, slugify_tag


ALLOWED_CONFIDENCE = {"low", "medium", "high"}
ALLOWED_IMPORTANCE = {"primary", "secondary", "incidental"}
ALLOWED_RATING_STATUS = {"official", "pending_cf_rating", "no_cf_rating", "unknown"}
ALLOWED_REVIEW_STATUS = {"reviewed", "verified"}
REVIEWED_TAG_SOURCES = {"manual", "ai_reviewed"}


class ReviewedPayloadError(ValueError):
    pass


def load_payload(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _require_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ReviewedPayloadError(f"{key} must be an object")
    return value


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewedPayloadError(f"{field} must be a non-empty string")
    return value.strip()


def _as_list(value: Any, field: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ReviewedPayloadError(f"{field} must be a list")
    return value


def _canonical_problem_ref(problem: dict[str, Any]) -> tuple[int, str, str, str, str]:
    contest_id = int(problem["contest_id"])
    index = _require_text(problem["index"], "problem.index").upper()
    key = normalize_problem_key(contest_id, index)
    return contest_id, index, key.problem_uid, key.canonical_url, key.problemset_url


def _validate_rating(problem: dict[str, Any], min_rating: int) -> None:
    status = problem.get("rating_status", "official" if problem.get("rating") is not None else "unknown")
    if status not in ALLOWED_RATING_STATUS:
        raise ReviewedPayloadError(f"invalid rating_status: {status}")

    rating = problem.get("rating")
    if status == "official":
        if not isinstance(rating, int):
            raise ReviewedPayloadError("official rating_status requires integer problem.rating")
        if rating < min_rating:
            raise ReviewedPayloadError(f"official rating below {min_rating} is not allowed")
    elif rating is not None:
        raise ReviewedPayloadError("problem.rating may be set only when rating_status is official")


def _validate_annotation(annotation: dict[str, Any]) -> None:
    for field in ("summary", "constraints", "core_idea", "complexity"):
        _require_text(annotation.get(field), f"annotation.{field}")
    confidence = annotation.get("confidence", "medium")
    if confidence not in ALLOWED_CONFIDENCE:
        raise ReviewedPayloadError(f"invalid annotation.confidence: {confidence}")
    review_status = annotation.get("review_status", "reviewed")
    if review_status not in ALLOWED_REVIEW_STATUS:
        raise ReviewedPayloadError(f"review_status must be reviewed or verified, got {review_status}")
    tricks = annotation.get("tricks", [])
    if not isinstance(tricks, list) or any(not isinstance(item, str) or not item.strip() for item in tricks):
        raise ReviewedPayloadError("annotation.tricks must be a list of non-empty strings")


def _validate_variants(variants: list[Any]) -> set[str]:
    names: set[str] = set()
    for idx, item in enumerate(variants):
        if not isinstance(item, dict):
            raise ReviewedPayloadError(f"solution_variants[{idx}] must be an object")
        name = _require_text(item.get("name"), f"solution_variants[{idx}].name")
        if name in names:
            raise ReviewedPayloadError(f"duplicate solution variant: {name}")
        names.add(name)
        _require_text(item.get("summary"), f"solution_variants[{idx}].summary")
        _require_text(item.get("complexity"), f"solution_variants[{idx}].complexity")
        confidence = item.get("confidence", "medium")
        if confidence not in ALLOWED_CONFIDENCE:
            raise ReviewedPayloadError(f"invalid solution_variants[{idx}].confidence: {confidence}")
    return names


def _validate_sources(sources: list[Any]) -> None:
    if not sources:
        raise ReviewedPayloadError("at least one source is required")
    has_statement = False
    for idx, item in enumerate(sources):
        if not isinstance(item, dict):
            raise ReviewedPayloadError(f"sources[{idx}] must be an object")
        source_type = _require_text(item.get("source_type"), f"sources[{idx}].source_type")
        _require_text(item.get("url"), f"sources[{idx}].url")
        _require_text(item.get("notes"), f"sources[{idx}].notes")
        if source_type == "statement":
            has_statement = True
    if not has_statement:
        raise ReviewedPayloadError("at least one statement source is required")


def _tag_exists(conn: sqlite3.Connection, tag: str) -> bool:
    row = conn.execute("SELECT 1 FROM tags WHERE tag = ?", (slugify_tag(tag),)).fetchone()
    if row:
        return True
    alias = conn.execute("SELECT 1 FROM tag_aliases WHERE alias = ?", (slugify_tag(tag),)).fetchone()
    return alias is not None


def _parents(item: dict[str, Any]) -> list[str]:
    values: list[str] = []
    if item.get("parent"):
        values.append(_require_text(item.get("parent"), "tag.parent"))
    for parent in _as_list(item.get("parents"), "tag.parents"):
        values.append(_require_text(parent, "tag.parents[]"))
    return values


def _validate_tags(conn: sqlite3.Connection, tags: list[Any], variant_names: set[str]) -> None:
    if not tags:
        raise ReviewedPayloadError("at least one reviewed tag is required")
    has_primary = False
    for idx, item in enumerate(tags):
        if not isinstance(item, dict):
            raise ReviewedPayloadError(f"tags[{idx}] must be an object")
        tag = _require_text(item.get("tag"), f"tags[{idx}].tag")
        importance = item.get("importance", "primary")
        if importance not in ALLOWED_IMPORTANCE:
            raise ReviewedPayloadError(f"invalid tags[{idx}].importance: {importance}")
        evidence = item.get("evidence")
        if importance == "primary":
            has_primary = True
            _require_text(evidence, f"tags[{idx}].evidence")
        variant = item.get("solution_variant")
        if variant and variant not in variant_names:
            raise ReviewedPayloadError(f"tags[{idx}] references unknown solution_variant: {variant}")

        if not _tag_exists(conn, tag):
            _require_text(item.get("description"), f"new tag {tag}.description")
            _require_text(item.get("created_reason"), f"new tag {tag}.created_reason")
            if not _parents(item):
                raise ReviewedPayloadError(f"new tag {tag} requires parent or parents")
    if not has_primary:
        raise ReviewedPayloadError("at least one primary tag is required")


def validate_payload(conn: sqlite3.Connection, payload: dict[str, Any], min_rating: int = 1400) -> None:
    contest = _require_mapping(payload, "contest")
    problem = _require_mapping(payload, "problem")
    annotation = _require_mapping(payload, "annotation")
    _require_text(contest.get("title"), "contest.title")
    int(contest["contest_id"])
    int(problem["contest_id"])
    if int(contest["contest_id"]) != int(problem["contest_id"]):
        raise ReviewedPayloadError("contest.contest_id and problem.contest_id must match")
    _require_text(problem.get("index"), "problem.index")
    _require_text(problem.get("title"), "problem.title")
    _validate_rating(problem, min_rating)
    _validate_annotation(annotation)
    variants = _as_list(payload.get("solution_variants"), "solution_variants")
    variant_names = _validate_variants(variants)
    _validate_sources(_as_list(payload.get("sources"), "sources"))
    _validate_tags(conn, _as_list(payload.get("tags"), "tags"), variant_names)


def _upsert_contest(conn: sqlite3.Connection, contest: dict[str, Any]) -> None:
    contest_id = int(contest["contest_id"])
    conn.execute(
        """
        INSERT INTO contests(
            contest_id, contest_uid, title, eligibility_status, extraction_status, last_checked_at
        )
        VALUES (?, ?, ?, 'eligible', 'problems_loaded', CURRENT_TIMESTAMP)
        ON CONFLICT(contest_id) DO UPDATE SET
            title = excluded.title,
            eligibility_status = CASE
                WHEN contests.manual_override = 'manual_exclude' THEN contests.eligibility_status
                ELSE 'eligible'
            END,
            extraction_status = 'problems_loaded',
            last_checked_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        """,
        (contest_id, contest_uid(contest_id), contest["title"]),
    )


def _upsert_problem(conn: sqlite3.Connection, problem: dict[str, Any]) -> str:
    contest_id, index, problem_uid, canonical_url, problemset_url = _canonical_problem_ref(problem)
    target_uid = canonical_problem_uid(conn, problem_uid)
    if target_uid != problem_uid:
        for source_type, url in (("alias_contest", canonical_url), ("alias_problemset", problemset_url)):
            conn.execute(
                "INSERT OR IGNORE INTO problem_sources(problem_uid, source_type, url) VALUES (?, ?, ?)",
                (target_uid, source_type, url),
            )
        return target_uid

    rating_status = problem.get("rating_status", "official" if problem.get("rating") is not None else "unknown")
    rating = problem.get("rating") if rating_status == "official" else None
    official_tags = _as_list(problem.get("official_tags"), "problem.official_tags")
    conn.execute(
        """
        INSERT INTO problems(
            problem_uid, contest_id, problem_index, title, problem_type, points,
            rating, rating_status, rating_source, rating_last_checked_at, canonical_url,
            problemset_url, official_tags_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
        ON CONFLICT(problem_uid) DO UPDATE SET
            title = excluded.title,
            problem_type = excluded.problem_type,
            points = excluded.points,
            rating = excluded.rating,
            rating_status = excluded.rating_status,
            rating_source = excluded.rating_source,
            rating_last_checked_at = CURRENT_TIMESTAMP,
            canonical_url = excluded.canonical_url,
            problemset_url = excluded.problemset_url,
            official_tags_json = excluded.official_tags_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            problem_uid,
            contest_id,
            index,
            problem["title"],
            problem.get("problem_type"),
            problem.get("points"),
            rating,
            rating_status,
            "codeforces" if rating_status == "official" else None,
            canonical_url,
            problemset_url,
            json.dumps(official_tags, ensure_ascii=True),
        ),
    )
    for source_type, url in (("canonical", canonical_url), ("problemset", problemset_url)):
        conn.execute(
            "INSERT OR IGNORE INTO problem_sources(problem_uid, source_type, url) VALUES (?, ?, ?)",
            (problem_uid, source_type, url),
        )
    return problem_uid


def _upsert_sources(conn: sqlite3.Connection, problem_uid: str, sources: list[Any]) -> None:
    for idx, item in enumerate(sources):
        if not isinstance(item, dict):
            raise ReviewedPayloadError(f"sources[{idx}] must be an object")
        source_type = _require_text(item.get("source_type"), f"sources[{idx}].source_type")
        url = _require_text(item.get("url"), f"sources[{idx}].url")
        conn.execute(
            """
            INSERT INTO problem_sources(problem_uid, source_type, url, fetched_at, notes)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            ON CONFLICT(problem_uid, source_type, url) DO UPDATE SET
                fetched_at = CURRENT_TIMESTAMP,
                notes = excluded.notes
            """,
            (problem_uid, source_type, url, item.get("notes")),
        )


def _upsert_annotation(conn: sqlite3.Connection, problem_uid: str, annotation: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO problem_annotations(
            problem_uid, summary, constraints_text, core_idea, complexity, tricks_json,
            confidence, review_status, last_reviewed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(problem_uid) DO UPDATE SET
            summary = excluded.summary,
            constraints_text = excluded.constraints_text,
            core_idea = excluded.core_idea,
            complexity = excluded.complexity,
            tricks_json = excluded.tricks_json,
            confidence = excluded.confidence,
            review_status = excluded.review_status,
            last_reviewed_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            problem_uid,
            annotation["summary"],
            annotation["constraints"],
            annotation["core_idea"],
            annotation["complexity"],
            json.dumps(annotation.get("tricks", []), ensure_ascii=False),
            annotation.get("confidence", "medium"),
            annotation.get("review_status", "reviewed"),
        ),
    )


def _upsert_variants(conn: sqlite3.Connection, problem_uid: str, variants: list[Any]) -> dict[str, int]:
    variant_ids: dict[str, int] = {}
    for item in variants:
        conn.execute(
            """
            INSERT INTO solution_variants(problem_uid, variant_name, summary, complexity, confidence, is_primary)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(problem_uid, variant_name) DO UPDATE SET
                summary = excluded.summary,
                complexity = excluded.complexity,
                confidence = excluded.confidence,
                is_primary = excluded.is_primary
            """,
            (
                problem_uid,
                item["name"],
                item["summary"],
                item["complexity"],
                item.get("confidence", "medium"),
                1 if item.get("is_primary") else 0,
            ),
        )
        row = conn.execute(
            "SELECT id FROM solution_variants WHERE problem_uid = ? AND variant_name = ?",
            (problem_uid, item["name"]),
        ).fetchone()
        variant_ids[item["name"]] = int(row["id"])
    return variant_ids


def _ensure_reviewed_tag(conn: sqlite3.Connection, item: dict[str, Any], problem_uid: str) -> str:
    try:
        return resolve_tag(conn, item["tag"])
    except KeyError:
        canonical = ensure_tag(
            conn,
            TagInput(
                item["tag"],
                display_name=item.get("display_name"),
                description=item.get("description"),
                status=item.get("status", "candidate"),
                created_from_problem=problem_uid,
                created_reason=item.get("created_reason"),
            ),
        )
        for alias in _as_list(item.get("aliases"), "tag.aliases"):
            add_alias(conn, _require_text(alias, "tag.aliases[]"), canonical)
        for parent in _parents(item):
            parent_tag = ensure_tag(conn, parent)
            conn.execute(
                "INSERT OR IGNORE INTO tag_edges(parent_tag, child_tag) VALUES (?, ?)",
                (parent_tag, canonical),
            )
        return canonical


def _upsert_tags(
    conn: sqlite3.Connection,
    problem_uid: str,
    tags: list[Any],
    variant_ids: dict[str, int],
) -> None:
    placeholders = ",".join("?" for _ in REVIEWED_TAG_SOURCES)
    conn.execute(
        f"DELETE FROM problem_tags WHERE problem_uid = ? AND source IN ({placeholders})",
        (problem_uid, *sorted(REVIEWED_TAG_SOURCES)),
    )
    for item in tags:
        canonical = _ensure_reviewed_tag(conn, item, problem_uid)
        variant_id = variant_ids.get(item.get("solution_variant")) if item.get("solution_variant") else None
        conn.execute(
            """
            INSERT INTO problem_tags(problem_uid, tag, importance, evidence, source, solution_variant_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                problem_uid,
                canonical,
                item.get("importance", "primary"),
                item.get("evidence"),
                item.get("source", "ai_reviewed"),
                variant_id,
            ),
        )


def apply_reviewed_payload(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    min_rating: int = 1400,
) -> str:
    validate_payload(conn, payload, min_rating=min_rating)
    contest = payload["contest"]
    problem = payload["problem"]
    _upsert_contest(conn, contest)
    problem_uid = _upsert_problem(conn, problem)
    _upsert_sources(conn, problem_uid, _as_list(payload.get("sources"), "sources"))
    _upsert_annotation(conn, problem_uid, payload["annotation"])
    variant_ids = _upsert_variants(conn, problem_uid, _as_list(payload.get("solution_variants"), "solution_variants"))
    _upsert_tags(conn, problem_uid, _as_list(payload.get("tags"), "tags"), variant_ids)
    return problem_uid


def problem_label(problem_uid: str) -> str:
    parts = problem_uid.split(":")
    if len(parts) == 3:
        return f"{parts[1]}{parts[2]}"
    return problem_uid
