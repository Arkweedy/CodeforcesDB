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
    args = parser.parse_args()

    with connect(args.db) as conn:
        rows = conn.execute(
            """
            SELECT
                p.problem_uid, p.contest_id, p.problem_index, p.title, p.rating, p.rating_status,
                c.title AS contest_title, a.review_status
            FROM problems p
            JOIN contests c ON c.contest_id = p.contest_id
            LEFT JOIN problem_annotations a ON a.problem_uid = p.problem_uid
            WHERE COALESCE(a.review_status, 'raw') IN ('raw', 'auto_seeded')
              AND (p.rating IS NULL OR p.rating >= ?)
              AND (p.canonical_problem_uid IS NULL OR p.canonical_problem_uid = p.problem_uid)
            ORDER BY p.contest_id, p.problem_index
            LIMIT ?
            """,
            (args.min_rating, args.limit),
        ).fetchall()

    for row in rows:
        rating = row["rating"] if row["rating"] is not None else row["rating_status"]
        print(
            f"{row['contest_id']}{row['problem_index']} [{rating}] "
            f"{row['title']} ({row['review_status'] or 'raw'})"
        )


if __name__ == "__main__":
    main()
