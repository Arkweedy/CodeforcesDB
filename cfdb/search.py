from __future__ import annotations

import json
import sqlite3
from typing import Iterable

from .tags import descendants, resolve_tag


DEFAULT_IMPORTANCE = ("primary", "secondary")


def _problem_set_for_tag(
    conn: sqlite3.Connection,
    tag: str,
    importance: Iterable[str],
) -> set[str]:
    expanded = descendants(conn, tag)
    placeholders = ",".join("?" for _ in expanded)
    imp = list(importance)
    imp_placeholders = ",".join("?" for _ in imp)
    rows = conn.execute(
        f"""
        SELECT DISTINCT problem_uid
        FROM problem_tags
        WHERE tag IN ({placeholders})
          AND importance IN ({imp_placeholders})
        """,
        (*expanded, *imp),
    ).fetchall()
    return {row["problem_uid"] for row in rows}


def search_problems(
    conn: sqlite3.Connection,
    rating_min: int | None = None,
    rating_max: int | None = None,
    tags: list[str] | None = None,
    exclude_tags: list[str] | None = None,
    importance: tuple[str, ...] = DEFAULT_IMPORTANCE,
    rating_statuses: tuple[str, ...] = ("official",),
    limit: int = 100,
) -> list[dict[str, object]]:
    params: list[object] = []
    where = []

    if rating_statuses:
        placeholders = ",".join("?" for _ in rating_statuses)
        where.append(f"p.rating_status IN ({placeholders})")
        params.extend(rating_statuses)

    if rating_min is not None:
        where.append("p.rating >= ?")
        params.append(rating_min)
    if rating_max is not None:
        where.append("p.rating <= ?")
        params.append(rating_max)

    where_sql = "WHERE " + " AND ".join(where) if where else ""
    rows = conn.execute(
        f"""
        SELECT p.problem_uid
        FROM problems p
        JOIN contests c ON c.contest_id = p.contest_id
        {where_sql}
        """,
        params,
    ).fetchall()
    candidates = {row["problem_uid"] for row in rows}

    for tag in tags or []:
        candidates &= _problem_set_for_tag(conn, resolve_tag(conn, tag), importance)

    for tag in exclude_tags or []:
        candidates -= _problem_set_for_tag(conn, resolve_tag(conn, tag), importance)

    if not candidates:
        return []

    placeholders = ",".join("?" for _ in candidates)
    result_rows = conn.execute(
        f"""
        SELECT
            p.problem_uid, p.contest_id, p.problem_index, p.title, p.rating,
            p.rating_status, p.canonical_url, c.title AS contest_title,
            c.start_time_utc
        FROM problems p
        JOIN contests c ON c.contest_id = p.contest_id
        WHERE p.problem_uid IN ({placeholders})
        ORDER BY
            CASE WHEN p.rating IS NULL THEN 1 ELSE 0 END,
            p.rating,
            p.contest_id,
            p.problem_index
        LIMIT ?
        """,
        (*candidates, limit),
    ).fetchall()

    results: list[dict[str, object]] = []
    for row in result_rows:
        tag_rows = conn.execute(
            """
            SELECT tag, importance, source
            FROM problem_tags
            WHERE problem_uid = ?
            ORDER BY
                CASE importance
                    WHEN 'primary' THEN 0
                    WHEN 'secondary' THEN 1
                    ELSE 2
                END,
                tag
            """,
            (row["problem_uid"],),
        ).fetchall()
        item = dict(row)
        item["tags"] = [dict(tag_row) for tag_row in tag_rows]
        results.append(item)
    return results


def format_text(results: list[dict[str, object]], show_tags: bool = False) -> str:
    lines: list[str] = []
    for item in results:
        rating = item["rating"] if item["rating"] is not None else item["rating_status"]
        lines.append(
            f"{item['contest_id']}{item['problem_index']} [{rating}] {item['title']} - {item['canonical_url']}"
        )
        if show_tags:
            tags = item.get("tags", [])
            if tags:
                formatted = ", ".join(f"{tag['tag']}:{tag['importance']}" for tag in tags)
                lines.append(f"  tags: {formatted}")
    return "\n".join(lines)


def format_json(results: list[dict[str, object]]) -> str:
    return json.dumps(results, ensure_ascii=False, indent=2)

