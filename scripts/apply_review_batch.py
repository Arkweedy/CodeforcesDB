from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect, init_db
from cfdb.git_utils import commit_paths
from cfdb.reviewed import apply_reviewed_payload, load_payload, problem_label


def collect_json_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
        else:
            files.append(path)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply multiple AI-reviewed problem JSON files.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--min-rating", type=int, default=1400)
    parser.add_argument("--no-auto-commit", action="store_true")
    parser.add_argument("paths", nargs="+", help="Reviewed JSON files or directories containing JSON files.")
    args = parser.parse_args()

    files = collect_json_files(args.paths)
    if not files:
        raise SystemExit("no JSON files found")

    init_db(args.db)
    applied: list[str] = []
    with connect(args.db) as conn:
        for path in files:
            problem_uid = apply_reviewed_payload(conn, load_payload(path), min_rating=args.min_rating)
            label = problem_label(problem_uid)
            applied.append(label)
            print(f"applied {label} from {path}")

    if not args.no_auto_commit:
        labels = sorted(applied)
        subject = f"review CF problems {labels[0]}-{labels[-1]} ({len(labels)} problems)"
        body = "\n".join(
            [
                f"Problems reviewed: {len(labels)}",
                "Problem labels: " + ", ".join(labels),
            ]
        )
        commit_paths([Path(args.db)], subject, body, Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    main()

