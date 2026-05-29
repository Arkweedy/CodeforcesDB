from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cfdb.db import DEFAULT_DB_PATH, ROOT


FULL_TAG_BLOCK_RE = re.compile(
    r"const\s+FULL_TAG_TEXT_ZH\s*:\s*Record<string,\s*string>\s*=\s*\{(?P<body>.*?)\n\};",
    re.DOTALL,
)
TAG_KEY_RE = re.compile(r'^\s*"([^"]+)"\s*:', re.MULTILINE)


def extract_full_tag_translations(i18n_path: str | Path) -> set[str]:
    text = Path(i18n_path).read_text(encoding="utf-8")
    match = FULL_TAG_BLOCK_RE.search(text)
    if match is None:
        raise ValueError(f"cannot find FULL_TAG_TEXT_ZH block in {i18n_path}")
    return set(TAG_KEY_RE.findall(match.group("body")))


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
        default=str(ROOT / "web" / "src" / "i18n.ts"),
        help="Path to WebUI i18n.ts.",
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
