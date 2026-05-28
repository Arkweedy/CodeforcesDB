from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, ROOT, connect, init_db
from cfdb.tags import TagInput, add_alias, ensure_tag, seed_tags, slugify_tag


EXACT_RENAMES = {
    "communication": "paradigm/communication",
    "algorithm/meet-in-the-middle": "algorithm/search/meet-in-the-middle",
    "topic/scheduling": "trick/scheduling",
}

PREFIX_RENAMES = (
    ("algorithm/transform", "math/transform"),
    ("algorithm/dp", "dp"),
    ("algorithm/graph", "graph"),
    ("algorithm/string", "string"),
)

REMOVED_ROOTS = {"topic"}


def rename_tag(tag: str) -> str | None:
    normalized = slugify_tag(tag)
    if normalized in EXACT_RENAMES:
        return EXACT_RENAMES[normalized]
    for old, new in PREFIX_RENAMES:
        if normalized == old:
            return new
        if normalized.startswith(f"{old}/"):
            return f"{new}/{normalized[len(old) + 1:]}"
    if normalized in REMOVED_ROOTS:
        return None
    return normalized


def is_old_path(value: str) -> bool:
    normalized = slugify_tag(value)
    if normalized in EXACT_RENAMES or normalized in REMOVED_ROOTS:
        return True
    return any(normalized == old or normalized.startswith(f"{old}/") for old, _ in PREFIX_RENAMES)


def _renamed_db_tags(conn) -> dict[str, str | None]:  # type: ignore[no-untyped-def]
    rows = conn.execute("SELECT tag FROM tags ORDER BY tag").fetchall()
    renamed: dict[str, str | None] = {}
    for row in rows:
        old = row["tag"]
        new = rename_tag(old)
        if new != old:
            renamed[old] = new
    return renamed


def _ensure_target_from_source(conn, old_tag: str, new_tag: str) -> None:  # type: ignore[no-untyped-def]
    row = conn.execute("SELECT * FROM tags WHERE tag = ?", (old_tag,)).fetchone()
    if row is None:
        ensure_tag(conn, new_tag)
        return
    ensure_tag(
        conn,
        TagInput(
            new_tag,
            display_name=row["display_name"],
            description=row["description"],
            status=row["status"],
            created_from_problem=row["created_from_problem"],
            created_reason=row["created_reason"],
        ),
    )


def migrate_database(db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, int]:
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute("BEGIN")
        seed_tags(conn)
        renamed = _renamed_db_tags(conn)
        if not renamed:
            return {"tags": 0, "problem_tags": 0, "aliases": 0}

        for old_tag, new_tag in renamed.items():
            if new_tag is not None:
                _ensure_target_from_source(conn, old_tag, new_tag)

        copied_problem_tags = 0
        for old_tag, new_tag in renamed.items():
            if new_tag is None:
                continue
            before = conn.total_changes
            conn.execute(
                """
                INSERT OR IGNORE INTO problem_tags(
                    problem_uid, tag, importance, evidence, source, solution_variant_id, created_at
                )
                SELECT problem_uid, ?, importance, evidence, source, solution_variant_id, created_at
                FROM problem_tags
                WHERE tag = ?
                """,
                (new_tag, old_tag),
            )
            copied_problem_tags += conn.total_changes - before

        copied_aliases = 0
        for old_tag, new_tag in renamed.items():
            if new_tag is None:
                continue
            rows = conn.execute("SELECT alias FROM tag_aliases WHERE tag = ?", (old_tag,)).fetchall()
            for row in rows:
                alias = row["alias"]
                if is_old_path(alias):
                    continue
                before = conn.total_changes
                add_alias(conn, alias, new_tag)
                copied_aliases += conn.total_changes - before

        for old_tag in sorted(renamed, key=lambda item: item.count("/"), reverse=True):
            conn.execute("DELETE FROM tags WHERE tag = ?", (old_tag,))

        seed_tags(conn)
        return {
            "tags": sum(1 for target in renamed.values() if target is not None),
            "problem_tags": copied_problem_tags,
            "aliases": copied_aliases,
        }


def rewrite_payload(obj: Any) -> Any:
    if isinstance(obj, dict):
        rewritten: dict[str, Any] = {}
        for key, value in obj.items():
            if key in {"tag", "parent"} and isinstance(value, str):
                new_value = rename_tag(value)
                rewritten[key] = value if new_value is None else new_value
            elif key == "parents" and isinstance(value, list):
                rewritten[key] = [rename_tag(item) or item if isinstance(item, str) else item for item in value]
            else:
                rewritten[key] = rewrite_payload(value)
        return rewritten
    if isinstance(obj, list):
        return [rewrite_payload(item) for item in obj]
    return obj


def rewrite_review_payloads(reviews_dir: str | Path = ROOT / "reviews") -> int:
    changed = 0
    for path in sorted(Path(reviews_dir).glob("*.json")):
        original = path.read_text(encoding="utf-8")
        payload = json.loads(original)
        rewritten = rewrite_payload(payload)
        updated = json.dumps(rewritten, ensure_ascii=False, indent=2) + "\n"
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate tag taxonomy paths in SQLite and review payloads.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--reviews-dir", default=str(ROOT / "reviews"), help="Reviewed JSON directory.")
    parser.add_argument("--skip-db", action="store_true", help="Do not migrate SQLite.")
    parser.add_argument("--skip-reviews", action="store_true", help="Do not rewrite reviewed JSON files.")
    args = parser.parse_args()

    if not args.skip_db:
        stats = migrate_database(args.db)
        print(
            "migrated DB: "
            f"{stats['tags']} tags, {stats['problem_tags']} problem_tags, {stats['aliases']} aliases"
        )
    if not args.skip_reviews:
        changed = rewrite_review_payloads(args.reviews_dir)
        print(f"rewrote {changed} reviewed JSON files")


if __name__ == "__main__":
    main()
