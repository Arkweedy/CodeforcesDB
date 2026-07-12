from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, ROOT


def extract_full_tag_translations(i18n_path: str | Path) -> set[str]:
    path = Path(i18n_path)
    source = path.read_text(encoding="utf-8")
    if path.suffix.lower() != ".json":
        # Compatibility for older callers and archived WebUI sources. The live
        # translation catalogue is JSON; this branch is intentionally read-only.
        return set(re.findall(r'^\s*"([^"]+)"\s*:', source, flags=re.MULTILINE))
    payload = json.loads(source)
    if not isinstance(payload, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in payload.items()
    ):
        raise ValueError(f"expected a string-to-string JSON object in {i18n_path}")
    return set(payload)


def db_tags(db_path: str | Path) -> list[str]:
    path = Path(db_path)
    uri = f"file:{path.resolve().as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        rows = conn.execute("SELECT tag FROM tags ORDER BY tag").fetchall()
    return [str(row[0]) for row in rows]


def missing_translations(tags: list[str], translated_tags: set[str]) -> list[str]:
    return [tag for tag in tags if tag not in translated_tags]


def main() -> None:
    parser = argparse.ArgumentParser(description="List DB tags missing full Chinese WebUI translations.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument(
        "--i18n",
        default=str(ROOT / "web" / "src" / "i18n" / "tags.zh.json"),
        help="Path to the WebUI full-tag Chinese translation JSON.",
    )
    args = parser.parse_args()

    missing = missing_translations(db_tags(args.db), extract_full_tag_translations(args.i18n))
    if not missing:
        print("all DB tags have full Chinese translations")
        return

    print("missing full Chinese translations:")
    for tag in missing:
        print(f"- {tag}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
