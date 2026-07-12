from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from .tags import descendants, resolve_tag


@dataclass
class SearchOptions:
    rating_min: int | None = None
    rating_max: int | None = None
    rating_statuses: tuple[str, ...] = ()
    importance: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    exclude_tags: tuple[str, ...] = ()
    tag_mode: str = "and"
    favorite: str = "any"
    progress_statuses: tuple[str, ...] = ()
    priorities: tuple[str, ...] = ()
    query: str | None = None
    sort_by: str = "rating"
    sort_order: str = "asc"
    limit: int = 50
    offset: int = 0


def _load_catalog(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            p.problem_uid, p.contest_id, p.problem_index, p.title, p.rating,
            p.rating_status, p.canonical_url, p.problemset_url,
            c.title AS contest_title, c.start_time_utc,
            COALESCE(us.favorite, 0) AS favorite,
            us.manual_progress, us.synced_progress, us.priority,
            COALESCE(us.manual_progress, us.synced_progress, 'unattempted') AS progress_status
        FROM problems p
        JOIN contests c ON c.contest_id = p.contest_id
        LEFT JOIN problem_annotations a ON a.problem_uid = p.problem_uid
        LEFT JOIN userdb.problem_user_state us ON us.problem_uid = p.problem_uid
        WHERE (p.canonical_problem_uid IS NULL OR p.canonical_problem_uid = p.problem_uid)
          AND COALESCE(a.review_status, 'raw') <> 'excluded'
          AND COALESCE(c.eligibility_status, 'eligible') <> 'excluded'
        """
    ).fetchall()
    by_uid = {str(row["problem_uid"]): dict(row) for row in rows}
    for item in by_uid.values():
        item["label"] = f"{item['contest_id']}{item['problem_index']}"
        item["favorite"] = bool(item["favorite"])
        item["tags"] = []

    tag_rows = conn.execute(
        """
        SELECT pt.problem_uid, pt.tag, pt.importance, pt.source
        FROM problem_tags pt
        WHERE pt.problem_uid IN (
            SELECT problem_uid FROM problems
            WHERE canonical_problem_uid IS NULL OR canonical_problem_uid = problem_uid
        )
        ORDER BY pt.problem_uid,
            CASE pt.importance WHEN 'primary' THEN 0 WHEN 'secondary' THEN 1 ELSE 2 END,
            pt.tag, pt.source
        """
    ).fetchall()
    for row in tag_rows:
        item = by_uid.get(str(row["problem_uid"]))
        if item is not None:
            item["tags"].append(
                {
                    "tag": row["tag"],
                    "importance": row["importance"],
                    "source": row["source"],
                }
            )
    return list(by_uid.values())


def _expanded_filters(
    conn: sqlite3.Connection, options: SearchOptions
) -> tuple[list[set[str]], list[set[str]]]:
    def expand(tag: str) -> set[str]:
        canonical = resolve_tag(conn, tag)
        return set(descendants(conn, canonical))

    return ([expand(tag) for tag in options.tags], [expand(tag) for tag in options.exclude_tags])


def _matcher(
    conn: sqlite3.Connection,
    options: SearchOptions,
):
    include_sets, exclude_sets = _expanded_filters(conn, options)
    importance = set(options.importance) or {"primary", "secondary", "incidental"}
    rating_statuses = set(options.rating_statuses)
    progress_statuses = set(options.progress_statuses)
    priorities = set(options.priorities)
    query = (options.query or "").strip().casefold()

    def matches(
        item: dict[str, Any],
        *,
        skip: str | None = None,
        skip_tags: bool = False,
    ) -> bool:
        rating = item["rating"]
        if options.rating_min is not None and (rating is None or rating < options.rating_min):
            return False
        if options.rating_max is not None and (rating is None or rating > options.rating_max):
            return False
        if rating_statuses and item["rating_status"] not in rating_statuses:
            return False
        if query:
            haystack = " ".join(
                str(item[field])
                for field in ("problem_uid", "label", "title", "contest_title")
            ).casefold()
            if query not in haystack:
                return False

        if skip != "favorite":
            if options.favorite == "favorite" and not item["favorite"]:
                return False
            if options.favorite == "not_favorite" and item["favorite"]:
                return False
        if skip != "progress" and progress_statuses:
            if item["progress_status"] not in progress_statuses:
                return False
        if skip != "priority" and priorities:
            priority = item["priority"] or "unassigned"
            if priority not in priorities:
                return False

        if not skip_tags:
            item_tags = {
                str(tag["tag"])
                for tag in item["tags"]
                if tag["importance"] in importance
            }
            if include_sets:
                hits = [bool(item_tags & tag_set) for tag_set in include_sets]
                if options.tag_mode == "and" and not all(hits):
                    return False
                if options.tag_mode == "or" and not any(hits):
                    return False
            if any(item_tags & tag_set for tag_set in exclude_sets):
                return False
        return True

    return matches


def _sort_items(items: list[dict[str, Any]], options: SearchOptions) -> list[dict[str, Any]]:
    allowed = {"problem", "title", "rating", "progress", "priority", "favorite"}
    sort_by = options.sort_by if options.sort_by in allowed else "rating"
    descending = options.sort_order == "desc"
    priority_rank = {"critical": 0, "high": 1, "normal": 2, "low": 3, None: 4}
    progress_rank = {"unattempted": 0, "attempted": 1, "solved": 2}

    def stable_key(item: dict[str, Any]) -> tuple[int, str]:
        return (int(item["contest_id"]), str(item["problem_index"]))

    ordered = sorted(items, key=stable_key)
    if sort_by == "problem":
        return list(reversed(ordered)) if descending else ordered
    if sort_by == "title":
        return sorted(ordered, key=lambda item: str(item["title"]).casefold(), reverse=descending)
    if sort_by == "favorite":
        return sorted(ordered, key=lambda item: int(item["favorite"]), reverse=descending)
    if sort_by == "progress":
        return sorted(
            ordered,
            key=lambda item: progress_rank.get(str(item["progress_status"]), 3),
            reverse=descending,
        )
    if sort_by == "priority":
        return sorted(
            ordered,
            key=lambda item: priority_rank.get(item["priority"], 4),
            reverse=descending,
        )

    rated = [item for item in ordered if item["rating"] is not None]
    unrated = [item for item in ordered if item["rating"] is None]
    rated.sort(key=lambda item: int(item["rating"]), reverse=descending)
    return rated + unrated


def _summary(items: list[dict[str, Any]]) -> dict[str, int | None]:
    ratings = [int(item["rating"]) for item in items if item["rating"] is not None]
    return {
        "total": len(items),
        "solved": sum(item["progress_status"] == "solved" for item in items),
        "attempted": sum(item["progress_status"] == "attempted" for item in items),
        "unattempted": sum(item["progress_status"] == "unattempted" for item in items),
        "favorites": sum(bool(item["favorite"]) for item in items),
        "max_rating": max(ratings) if ratings else None,
    }


def _facet_counts(
    conn: sqlite3.Connection,
    catalog: list[dict[str, Any]],
    options: SearchOptions,
    matches,
) -> dict[str, Any]:
    favorite_base = [item for item in catalog if matches(item, skip="favorite")]
    progress_base = [item for item in catalog if matches(item, skip="progress")]
    priority_base = [item for item in catalog if matches(item, skip="priority")]
    tag_base = [item for item in catalog if matches(item, skip_tags=True)]

    parents: dict[str, set[str]] = defaultdict(set)
    for row in conn.execute("SELECT parent_tag, child_tag FROM tag_edges"):
        parents[str(row["child_tag"])].add(str(row["parent_tag"]))

    ancestor_cache: dict[str, set[str]] = {}

    def ancestors(tag: str, path: set[str] | None = None) -> set[str]:
        if tag in ancestor_cache:
            return ancestor_cache[tag]
        seen = set(path or ())
        if tag in seen:
            return {tag}
        seen.add(tag)
        result = {tag}
        for parent in parents.get(tag, set()):
            result.update(ancestors(parent, seen))
        ancestor_cache[tag] = result
        return result

    importance = set(options.importance) or {"primary", "secondary", "incidental"}
    tag_counts: Counter[str] = Counter()
    for item in tag_base:
        visible: set[str] = set()
        for tag in item["tags"]:
            if tag["importance"] in importance:
                visible.update(ancestors(str(tag["tag"])))
        tag_counts.update(visible)

    return {
        "favorite": {
            "all": len(favorite_base),
            "favorite": sum(bool(item["favorite"]) for item in favorite_base),
            "not_favorite": sum(not bool(item["favorite"]) for item in favorite_base),
        },
        "progress": {
            value: sum(item["progress_status"] == value for item in progress_base)
            for value in ("unattempted", "attempted", "solved")
        },
        "priority": {
            value: sum((item["priority"] or "unassigned") == value for item in priority_base)
            for value in ("critical", "high", "normal", "low", "unassigned")
        },
        "tag_counts": dict(tag_counts),
    }


def search_catalog(conn: sqlite3.Connection, options: SearchOptions) -> dict[str, Any]:
    catalog = _load_catalog(conn)
    matches = _matcher(conn, options)
    filtered = [item for item in catalog if matches(item)]
    ordered = _sort_items(filtered, options)
    limit = max(1, min(options.limit, 100))
    offset = max(0, options.offset)
    return {
        "items": ordered[offset : offset + limit],
        "total": len(ordered),
        "limit": limit,
        "offset": offset,
        "summary": _summary(filtered),
        "facets": _facet_counts(conn, catalog, options, matches),
        "_filtered": filtered,
    }


def analytics_catalog(
    conn: sqlite3.Connection,
    options: SearchOptions,
    *,
    scope: str,
) -> dict[str, Any]:
    applied = SearchOptions() if scope == "global" else options
    result = search_catalog(conn, applied)
    items = result.pop("_filtered")
    rating_counts: Counter[int] = Counter()
    tag_counts: Counter[str] = Counter()
    for item in items:
        if item["rating"] is not None:
            rating_counts[(int(item["rating"]) // 100) * 100] += 1
        tag_counts.update(
            {
                str(tag["tag"])
                for tag in item["tags"]
                if tag["importance"] in {"primary", "secondary"}
            }
        )
    return {
        "scope": scope,
        "summary": result["summary"],
        "rating_buckets": [
            {"rating": rating, "count": rating_counts[rating]}
            for rating in sorted(rating_counts)
        ],
        "progress": [
            {"name": name, "count": int(result["summary"][name])}
            for name in ("unattempted", "attempted", "solved")
        ],
        "priority": [
            {"name": name, "count": int(result["facets"]["priority"][name])}
            for name in ("critical", "high", "normal", "low", "unassigned")
        ],
        "top_tags": [
            {"tag": tag, "count": count} for tag, count in tag_counts.most_common(15)
        ],
    }
