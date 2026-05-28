from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect, init_db
from cfdb.reviewed import apply_reviewed_payload, load_payload, problem_label


def apply_file(db_path: str, json_path: str, min_rating: int = 1400) -> str:
    init_db(db_path)
    payload = load_payload(json_path)
    with connect(db_path) as conn:
        return apply_reviewed_payload(conn, payload, min_rating=min_rating)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply one AI-reviewed Codeforces problem JSON.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--min-rating", type=int, default=1400, help="Reject official ratings below this value.")
    parser.add_argument("reviewed_json", help="Path to reviewed problem JSON.")
    args = parser.parse_args()

    problem_uid = apply_file(args.db, args.reviewed_json, min_rating=args.min_rating)
    print(f"applied {problem_label(problem_uid)} from {args.reviewed_json}")


if __name__ == "__main__":
    main()

