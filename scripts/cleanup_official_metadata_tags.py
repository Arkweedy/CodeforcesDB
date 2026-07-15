from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, connect, init_db


EVIDENCE_PREFIX = "Codeforces official tag: *"
DESCRIPTION_PREFIX = "Mapped from Codeforces official tag: *"


def cleanup_official_metadata_tags(db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, int]:
    init_db(db_path)
    removed_problem_tags = 0
    removed_tags = 0

    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT problem_uid, tag, source, evidence
            FROM problem_tags
            WHERE source = 'cf_official'
            """
        ).fetchall()
        metadata_rows = [row for row in rows if (row["evidence"] or "").startswith(EVIDENCE_PREFIX)]
        candidate_tags = {row["tag"] for row in metadata_rows}

        for row in metadata_rows:
            cursor = conn.execute(
                """
                DELETE FROM problem_tags
                WHERE problem_uid = ? AND tag = ? AND source = ? AND evidence = ?
                """,
                (row["problem_uid"], row["tag"], row["source"], row["evidence"]),
            )
            removed_problem_tags += cursor.rowcount

        for tag in sorted(candidate_tags):
            row = conn.execute("SELECT description FROM tags WHERE tag = ?", (tag,)).fetchone()
            if row is None or not (row["description"] or "").startswith(DESCRIPTION_PREFIX):
                continue
            references = conn.execute(
                """
                SELECT
                    EXISTS(SELECT 1 FROM problem_tags WHERE tag = ?) OR
                    EXISTS(SELECT 1 FROM tag_edges WHERE parent_tag = ? OR child_tag = ?) OR
                    EXISTS(SELECT 1 FROM tag_aliases WHERE tag = ?)
                """,
                (tag, tag, tag, tag),
            ).fetchone()[0]
            if not references:
                removed_tags += conn.execute("DELETE FROM tags WHERE tag = ?", (tag,)).rowcount

    return {"problem_tags": removed_problem_tags, "tags": removed_tags}


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove Codeforces *metadata pseudo-tags from taxonomy.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    args = parser.parse_args()
    result = cleanup_official_metadata_tags(args.db)
    print(f"removed {result['problem_tags']} problem tag mappings and {result['tags']} orphan tags")


if __name__ == "__main__":
    main()
