from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect


def main() -> None:
    parser = argparse.ArgumentParser(description="List eligible contests that have not been fully extracted.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    with connect(args.db) as conn:
        rows = conn.execute(
            """
            SELECT contest_id, title, start_time_utc, extraction_status
            FROM contests
            WHERE eligibility_status = 'eligible'
              AND extraction_status <> 'problems_loaded'
            ORDER BY start_time_seconds ASC, contest_id ASC
            LIMIT ?
            """,
            (args.limit,),
        ).fetchall()
    for row in rows:
        print(f"{row['contest_id']}: {row['start_time_utc']} {row['extraction_status']} {row['title']}")


if __name__ == "__main__":
    main()
