from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect, init_db
from cfdb.tags import TagInput, add_alias, ensure_tag


def main() -> None:
    parser = argparse.ArgumentParser(description="Add or update a tag in the registry.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("tag", help="Canonical tag path, e.g. algorithm/string/acam.")
    parser.add_argument("--display-name")
    parser.add_argument("--description")
    parser.add_argument("--status", choices=("candidate", "active", "deprecated"), default="candidate")
    parser.add_argument("--alias", action="append", default=[])
    parser.add_argument("--created-from-problem")
    parser.add_argument("--created-reason")
    args = parser.parse_args()

    init_db(args.db)
    with connect(args.db) as conn:
        canonical = ensure_tag(
            conn,
            TagInput(
                args.tag,
                display_name=args.display_name,
                description=args.description,
                status=args.status,
                created_from_problem=args.created_from_problem,
                created_reason=args.created_reason,
            ),
        )
        for alias in args.alias:
            add_alias(conn, alias, canonical)
    print(canonical)


if __name__ == "__main__":
    main()
