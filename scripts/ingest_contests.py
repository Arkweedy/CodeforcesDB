from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.codeforces import CodeforcesClient
from cfdb.db import DEFAULT_DB_PATH, connect, init_db
from cfdb.dedup import canonical_problem_count, mark_division_duplicates
from cfdb.git_utils import commit_paths
from cfdb.ingest import find_contest_meta, ingest_contest, upsert_ingestion_range


def auto_commit_database(
    db_path: str,
    start: int,
    end: int,
    results: list[dict[str, Any]],
    problem_count: int | None = None,
    duplicate_count: int = 0,
) -> None:
    script_root = Path(__file__).resolve().parents[1]
    lo, hi = sorted((start, end))
    done = sum(1 for item in results if item["status"] == "done")
    skipped = sum(1 for item in results if item["status"] == "skipped")
    failed = sum(1 for item in results if item["status"] == "failed")
    problems = problem_count
    if problems is None:
        problems = sum(int(item.get("problems", 0)) for item in results if item["status"] == "done")
    subject = f"ingest CF contests {lo}-{hi} ({problems} problems)"
    body = "\n".join(
        [
            f"Range: {lo}-{hi}",
            f"Contests done: {done}",
            f"Contests skipped: {skipped}",
            f"Contests failed: {failed}",
            f"Problems ingested: {problems}",
            f"Div1/Div2 duplicates aliased: {duplicate_count}",
        ]
    )
    commit_paths([Path(db_path)], subject, body, script_root)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Codeforces contests into the local database.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--start", type=int, required=True, help="First contest id.")
    parser.add_argument("--end", type=int, required=True, help="Last contest id.")
    parser.add_argument("--pending-days", type=int, default=45, help="Days after contest start to keep unrated problems pending.")
    parser.add_argument("--min-rating", type=int, default=1400, help="Skip officially rated problems below this rating.")
    parser.add_argument("--delay", type=float, default=2.1, help="Delay between Codeforces API calls.")
    parser.add_argument("--no-auto-commit", action="store_true", help="Do not commit the database after ingestion.")
    args = parser.parse_args()

    init_db(args.db)
    client = CodeforcesClient(delay_seconds=args.delay)
    contests = client.contest_list(gym=False)

    results: list[dict[str, Any]] = []
    canonical_count = 0
    duplicate_count = 0
    with connect(args.db) as conn:
        upsert_ingestion_range(conn, args.start, args.end)
        for contest_id in range(min(args.start, args.end), max(args.start, args.end) + 1):
            try:
                meta = find_contest_meta(contests, contest_id)
                result = ingest_contest(
                    conn,
                    client,
                    contest_id,
                    meta,
                    pending_days=args.pending_days,
                    min_rating=args.min_rating,
                )
                print(f"{contest_id}: {result['status']} ({result['problems']} problems)")
                results.append(result)
            except Exception as exc:  # noqa: BLE001
                conn.execute(
                    """
                    UPDATE ingestion_queue
                    SET status = 'failed', last_error = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE contest_id = ?
                    """,
                    (str(exc), contest_id),
                )
                conn.execute(
                    """
                    UPDATE contests
                    SET extraction_status = 'failed', updated_at = CURRENT_TIMESTAMP
                    WHERE contest_id = ?
                    """,
                    (contest_id,),
                )
                print(f"{contest_id}: failed: {exc}")
                results.append({"contest_id": contest_id, "status": "failed", "problems": 0, "error": str(exc)})
        duplicates = mark_division_duplicates(conn)
        duplicate_count = len(duplicates)
        canonical_count = canonical_problem_count(conn, args.start, args.end)

    if not args.no_auto_commit:
        auto_commit_database(args.db, args.start, args.end, results, canonical_count, duplicate_count)


if __name__ == "__main__":
    main()
