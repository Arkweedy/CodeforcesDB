from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect, init_db
from cfdb.dedup import mark_division_duplicates
from cfdb.git_utils import commit_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Mark Div.1/Div.2 overlapping problems as Div.1 canonical.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--no-auto-commit", action="store_true")
    args = parser.parse_args()

    init_db(args.db)
    with connect(args.db) as conn:
        duplicates = mark_division_duplicates(conn)

    for item in duplicates:
        print(
            f"{item.alias_contest_id}{item.alias_problem_index} -> "
            f"{item.canonical_contest_id}{item.canonical_problem_index} ({item.title})"
        )
    print(f"division duplicates marked: {len(duplicates)}")

    if duplicates and not args.no_auto_commit:
        commit_paths(
            [Path(args.db)],
            f"dedupe Div1 Div2 overlaps ({len(duplicates)} aliases)",
            "Prefer Div.1 entries when Div.1 and Div.2 share the same problem.",
            Path(__file__).resolve().parents[1],
        )


if __name__ == "__main__":
    main()
