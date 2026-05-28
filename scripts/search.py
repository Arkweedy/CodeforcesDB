from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect
from cfdb.search import DEFAULT_IMPORTANCE, format_json, format_text, search_problems


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the Codeforces problem database.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--rating", nargs=2, type=int, metavar=("MIN", "MAX"))
    parser.add_argument("--tag", action="append", default=[], help="Required tag. Multiple tags are ANDed.")
    parser.add_argument("--exclude", action="append", default=[], help="Excluded tag.")
    parser.add_argument(
        "--importance",
        action="append",
        choices=("primary", "secondary", "incidental"),
        help="Importance levels to match. Defaults to primary + secondary.",
    )
    parser.add_argument(
        "--rating-status",
        action="append",
        choices=("official", "pending_cf_rating", "no_cf_rating", "unknown"),
        help="Rating statuses to include. Defaults to official only.",
    )
    parser.add_argument("--include-unrated", action="store_true", help="Include pending/no-rating/unknown problems.")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--show-tags", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    rating_min = rating_max = None
    if args.rating:
        rating_min, rating_max = args.rating

    importance = tuple(args.importance) if args.importance else DEFAULT_IMPORTANCE
    if args.rating_status:
        rating_statuses = tuple(args.rating_status)
    elif args.include_unrated:
        rating_statuses = ("official", "pending_cf_rating", "no_cf_rating", "unknown")
    else:
        rating_statuses = ("official",)

    with connect(args.db) as conn:
        results = search_problems(
            conn,
            rating_min=rating_min,
            rating_max=rating_max,
            tags=args.tag,
            exclude_tags=args.exclude,
            importance=importance,
            rating_statuses=rating_statuses,
            limit=args.limit,
        )

    if args.format == "json":
        print(format_json(results))
    else:
        print(format_text(results, show_tags=args.show_tags))


if __name__ == "__main__":
    main()
