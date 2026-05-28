from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect, init_db


ACTIONABLE_STATUSES = {
    "not_in_db",
    "needs_manual_review",
    "failed",
    "unextracted",
    "pending_review",
}


def _fetch_by_id(conn, query: str, params: tuple[Any, ...]) -> dict[int, dict[str, Any]]:
    rows = conn.execute(query, params).fetchall()
    return {int(row["contest_id"]): dict(row) for row in rows}


def _effective_eligibility(contest: dict[str, Any]) -> str:
    if contest.get("manual_override") == "manual_include":
        return "eligible"
    if contest.get("manual_override") == "manual_exclude":
        return "excluded"
    return str(contest.get("eligibility_status") or "needs_manual_review")


def _status_for(contest: dict[str, Any] | None, counts: dict[str, Any]) -> str:
    if contest is None:
        return "not_in_db"

    eligibility = _effective_eligibility(contest)
    extraction_status = contest.get("extraction_status")
    if eligibility == "excluded" or extraction_status == "excluded":
        return "excluded"
    if eligibility == "needs_manual_review":
        return "needs_manual_review"
    if extraction_status == "failed":
        return "failed"
    if extraction_status != "problems_loaded":
        return "unextracted"
    if int(counts.get("pending_review", 0) or 0) > 0:
        return "pending_review"
    return "complete"


def _action_for(status: str) -> str:
    return {
        "not_in_db": "bootstrap",
        "needs_manual_review": "inspect",
        "failed": "retry_bootstrap",
        "unextracted": "bootstrap",
        "pending_review": "ai_review",
        "excluded": "-",
        "complete": "-",
    }[status]


def contest_status_rows(
    db_path: str | Path = DEFAULT_DB_PATH,
    start: int = 1,
    end: int = 1,
    min_rating: int = 1400,
) -> list[dict[str, Any]]:
    """Return per-contest coverage status rows for an inclusive contest id range."""

    init_db(db_path)
    lo, hi = sorted((start, end))
    with connect(db_path) as conn:
        contests = _fetch_by_id(
            conn,
            """
            SELECT
                contest_id, title, eligibility_status, manual_override, exclusion_reason,
                extraction_status, start_time_utc
            FROM contests
            WHERE contest_id BETWEEN ? AND ?
            """,
            (lo, hi),
        )
        queues = _fetch_by_id(
            conn,
            """
            SELECT contest_id, status AS queue_status, last_error
            FROM ingestion_queue
            WHERE contest_id BETWEEN ? AND ?
            """,
            (lo, hi),
        )
        counts = _fetch_by_id(
            conn,
            """
            SELECT
                p.contest_id,
                COUNT(*) AS tracked_problems,
                SUM(CASE
                    WHEN COALESCE(a.review_status, 'raw') IN ('reviewed', 'verified')
                    THEN 1 ELSE 0
                END) AS reviewed_problems,
                SUM(CASE
                    WHEN COALESCE(a.review_status, 'raw') IN ('raw', 'auto_seeded')
                     AND (p.rating IS NULL OR p.rating >= ?)
                    THEN 1 ELSE 0
                END) AS pending_review,
                SUM(CASE
                    WHEN p.rating_status = 'pending_cf_rating'
                    THEN 1 ELSE 0
                END) AS pending_rating
            FROM problems p
            LEFT JOIN problem_annotations a ON a.problem_uid = p.problem_uid
            WHERE p.contest_id BETWEEN ? AND ?
              AND (p.canonical_problem_uid IS NULL OR p.canonical_problem_uid = p.problem_uid)
            GROUP BY p.contest_id
            """,
            (min_rating, lo, hi),
        )

    rows: list[dict[str, Any]] = []
    for contest_id in range(lo, hi + 1):
        contest = contests.get(contest_id)
        queue = queues.get(contest_id, {})
        row_counts = counts.get(contest_id, {})
        status = _status_for(contest, row_counts)
        rows.append(
            {
                "contest_id": contest_id,
                "status": status,
                "action": _action_for(status),
                "queue_status": queue.get("queue_status") or "-",
                "extraction_status": (contest or {}).get("extraction_status") or "-",
                "eligibility_status": _effective_eligibility(contest) if contest else "-",
                "tracked_problems": int(row_counts.get("tracked_problems", 0) or 0),
                "reviewed_problems": int(row_counts.get("reviewed_problems", 0) or 0),
                "pending_review": int(row_counts.get("pending_review", 0) or 0),
                "pending_rating": int(row_counts.get("pending_rating", 0) or 0),
                "title": (contest or {}).get("title") or "",
                "exclusion_reason": (contest or {}).get("exclusion_reason") or "",
                "last_error": queue.get("last_error") or "",
            }
        )
    return rows


def format_rows(rows: list[dict[str, Any]]) -> str:
    headers = [
        "contest",
        "status",
        "action",
        "queue",
        "extract",
        "elig",
        "tracked",
        "reviewed",
        "pending",
        "rating?",
        "title",
    ]
    data = [
        [
            str(row["contest_id"]),
            str(row["status"]),
            str(row["action"]),
            str(row["queue_status"]),
            str(row["extraction_status"]),
            str(row["eligibility_status"]),
            str(row["tracked_problems"]),
            str(row["reviewed_problems"]),
            str(row["pending_review"]),
            str(row["pending_rating"]),
            str(row["title"]),
        ]
        for row in rows
    ]
    widths = [
        max(len(headers[index]), *(len(item[index]) for item in data)) if data else len(header)
        for index, header in enumerate(headers)
    ]
    lines = [
        "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)),
        "  ".join("-" * width for width in widths),
    ]
    for item in data:
        lines.append("  ".join(value.ljust(widths[index]) for index, value in enumerate(item)))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List contest coverage states: missing, unextracted, pending review, or complete."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--start", type=int, required=True, help="First contest id, inclusive.")
    parser.add_argument("--end", type=int, required=True, help="Last contest id, inclusive.")
    parser.add_argument("--min-rating", type=int, default=1400, help="Minimum rating counted as pending review.")
    parser.add_argument("--only-actionable", action="store_true", help="Hide complete and excluded rows.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    rows = contest_status_rows(args.db, args.start, args.end, min_rating=args.min_rating)
    if args.only_actionable:
        rows = [row for row in rows if row["status"] in ACTIONABLE_STATUSES]

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(format_rows(rows))


if __name__ == "__main__":
    main()
