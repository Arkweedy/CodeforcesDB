from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect, init_db
from cfdb.normalize import parse_problem_ref


def build_template(db_path: str, problem_ref: str) -> dict[str, object]:
    init_db(db_path)
    key = parse_problem_ref(problem_ref)
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                p.*, c.title AS contest_title
            FROM problems p
            JOIN contests c ON c.contest_id = p.contest_id
            WHERE p.problem_uid = ?
            """,
            (key.problem_uid,),
        ).fetchone()
    if row is None:
        raise ValueError(f"{key.problem_uid} is not in the database; add metadata first or create JSON manually")

    official_tags = json.loads(row["official_tags_json"] or "[]")
    return {
        "contest": {
            "contest_id": row["contest_id"],
            "title": row["contest_title"],
        },
        "problem": {
            "contest_id": row["contest_id"],
            "index": row["problem_index"],
            "title": row["title"],
            "rating": row["rating"],
            "rating_status": row["rating_status"],
            "official_tags": official_tags,
        },
        "sources": [
            {
                "source_type": "statement",
                "url": row["canonical_url"],
                "notes": "题面与约束。",
            }
        ],
        "annotation": {
            "summary": "",
            "constraints": "",
            "core_idea": "",
            "complexity": "",
            "tricks": [],
            "confidence": "medium",
            "review_status": "reviewed",
        },
        "solution_variants": [
            {
                "name": "main",
                "summary": "",
                "complexity": "",
                "confidence": "medium",
                "is_primary": True,
            }
        ],
        "tags": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an AI-reviewed JSON template for one problem.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--out", help="Write JSON template to this path instead of stdout.")
    parser.add_argument("problem", help="Problem ref, e.g. 2170E or a Codeforces URL.")
    args = parser.parse_args()

    template = build_template(args.db, args.problem)
    text = json.dumps(template, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()

