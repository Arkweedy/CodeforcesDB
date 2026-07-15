from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect


def main() -> None:
    parser = argparse.ArgumentParser(description="List problems that still need AI-reviewed tagging.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--min-rating", type=int, default=1400)
    parser.add_argument("--contest", type=int, help="Only list one contest id.")
    parser.add_argument("--contest-from", type=int, help="Inclusive lower contest id bound.")
    parser.add_argument("--contest-to", type=int, help="Inclusive upper contest id bound.")
    args = parser.parse_args()

    if args.contest is not None and (args.contest_from is not None or args.contest_to is not None):
        parser.error("--contest cannot be combined with --contest-from or --contest-to")
    if (
        args.contest_from is not None
        and args.contest_to is not None
        and args.contest_from > args.contest_to
    ):
        parser.error("--contest-from must not exceed --contest-to")

    filters: list[str] = []
    params: list[int] = [args.min_rating]
    if args.contest is not None:
        filters.append("p.contest_id = ?")
        params.append(args.contest)
    else:
        if args.contest_from is not None:
            filters.append("p.contest_id >= ?")
            params.append(args.contest_from)
        if args.contest_to is not None:
            filters.append("p.contest_id <= ?")
            params.append(args.contest_to)

    contest_filter = "".join(f"\n              AND {condition}" for condition in filters)
    params.append(args.limit)

    with connect(args.db) as conn:
        rows = conn.execute(
            f"""
            SELECT
                p.problem_uid, p.contest_id, p.problem_index, p.title, p.rating, p.rating_status,
                c.title AS contest_title, a.review_status
            FROM problems p
            JOIN contests c ON c.contest_id = p.contest_id
            LEFT JOIN problem_annotations a ON a.problem_uid = p.problem_uid
            WHERE COALESCE(a.review_status, 'raw') IN ('raw', 'auto_seeded', 'needs_manual_review')
              AND COALESCE(c.manual_override, '') <> 'manual_exclude'
              AND COALESCE(c.eligibility_status, 'eligible') <> 'excluded'
              AND COALESCE(c.extraction_status, '') <> 'excluded'
              AND (p.rating IS NULL OR p.rating >= ?)
              AND (p.canonical_problem_uid IS NULL OR p.canonical_problem_uid = p.problem_uid)
              {contest_filter}
            ORDER BY p.contest_id, p.problem_index
            LIMIT ?
            """,
            params,
        ).fetchall()

    for row in rows:
        rating = row["rating"] if row["rating"] is not None else row["rating_status"]
        print(
            f"{row['contest_id']}{row['problem_index']} [{rating}] "
            f"{row['title']} ({row['review_status'] or 'raw'})"
        )


if __name__ == "__main__":
    main()
