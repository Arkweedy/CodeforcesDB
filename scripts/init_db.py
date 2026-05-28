from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the Codeforces SQLite database.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--no-seed-tags", action="store_true", help="Skip initial tag registry seed.")
    args = parser.parse_args()

    init_db(args.db, seed=not args.no_seed_tags)
    print(f"initialized {args.db}")


if __name__ == "__main__":
    main()
