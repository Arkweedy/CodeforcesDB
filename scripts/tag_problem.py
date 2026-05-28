from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect, init_db
from cfdb.reviewed import apply_reviewed_payload, load_payload, problem_label


def upsert_manual_annotation(db_path: str, annotation_path: str) -> None:
    init_db(db_path)
    payload = load_payload(annotation_path)
    with connect(db_path) as conn:
        problem_uid = apply_reviewed_payload(conn, payload)
    print(f"applied {problem_label(problem_uid)} from {annotation_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compatibility wrapper for apply_reviewed_problem.py."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("annotation_json", help="Path to reviewed problem JSON.")
    args = parser.parse_args()
    upsert_manual_annotation(args.db, args.annotation_json)


if __name__ == "__main__":
    main()
