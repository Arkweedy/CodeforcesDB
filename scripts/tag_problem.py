from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect, init_db
from cfdb.normalize import parse_problem_ref
from cfdb.tags import TagInput, ensure_tag, resolve_tag


def upsert_manual_annotation(db_path: str, annotation_path: str) -> None:
    payload = json.loads(open(annotation_path, "r", encoding="utf-8").read())
    key = parse_problem_ref(payload["problem"])
    problem_uid = key.problem_uid

    init_db(db_path)
    with connect(db_path) as conn:
        exists = conn.execute("SELECT 1 FROM problems WHERE problem_uid = ?", (problem_uid,)).fetchone()
        if not exists:
            raise ValueError(f"problem {problem_uid} is not in the database yet")

        annotation = payload.get("annotation", {})
        conn.execute(
            """
            INSERT INTO problem_annotations(
                problem_uid, summary, core_idea, complexity, confidence, review_status, last_reviewed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(problem_uid) DO UPDATE SET
                summary = excluded.summary,
                core_idea = excluded.core_idea,
                complexity = excluded.complexity,
                confidence = excluded.confidence,
                review_status = excluded.review_status,
                last_reviewed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                problem_uid,
                annotation.get("summary"),
                annotation.get("core_idea"),
                annotation.get("complexity"),
                annotation.get("confidence", "medium"),
                annotation.get("review_status", "reviewed"),
            ),
        )

        variant_ids: dict[str, int] = {}
        for variant in payload.get("solution_variants", []):
            conn.execute(
                """
                INSERT INTO solution_variants(
                    problem_uid, variant_name, summary, complexity, confidence, is_primary
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(problem_uid, variant_name) DO UPDATE SET
                    summary = excluded.summary,
                    complexity = excluded.complexity,
                    confidence = excluded.confidence,
                    is_primary = excluded.is_primary
                """,
                (
                    problem_uid,
                    variant["name"],
                    variant.get("summary"),
                    variant.get("complexity"),
                    variant.get("confidence", "medium"),
                    1 if variant.get("is_primary") else 0,
                ),
            )
            row = conn.execute(
                "SELECT id FROM solution_variants WHERE problem_uid = ? AND variant_name = ?",
                (problem_uid, variant["name"]),
            ).fetchone()
            variant_ids[variant["name"]] = int(row["id"])

        for item in payload.get("tags", []):
            tag = item["tag"]
            try:
                canonical = resolve_tag(conn, tag)
            except KeyError:
                canonical = ensure_tag(
                    conn,
                    TagInput(
                        tag,
                        display_name=item.get("display_name"),
                        description=item.get("description"),
                        status=item.get("status", "candidate"),
                        created_from_problem=problem_uid,
                        created_reason=item.get("created_reason", "Introduced by manual problem annotation."),
                    ),
                )

            variant_id = None
            if item.get("solution_variant"):
                variant_id = variant_ids.get(item["solution_variant"])
            conn.execute(
                """
                INSERT INTO problem_tags(
                    problem_uid, tag, importance, evidence, source, solution_variant_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(problem_uid, tag, importance, source) DO UPDATE SET
                    evidence = excluded.evidence,
                    solution_variant_id = excluded.solution_variant_id
                """,
                (
                    problem_uid,
                    canonical,
                    item.get("importance", "primary"),
                    item.get("evidence"),
                    item.get("source", "manual"),
                    variant_id,
                ),
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply a reviewed problem annotation JSON file.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("annotation_json", help="Path to a problem annotation JSON file.")
    args = parser.parse_args()
    upsert_manual_annotation(args.db, args.annotation_json)
    print(f"applied {args.annotation_json}")


if __name__ == "__main__":
    main()
