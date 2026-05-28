from __future__ import annotations

import sqlite3
from pathlib import Path

from .tags import seed_tags


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT / "data" / "cfdb.sqlite"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


class CfConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):  # type: ignore[no-untyped-def]
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()
        return False


def connect(path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, factory=CfConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def migrate_db(conn: sqlite3.Connection) -> None:
    annotation_columns = _columns(conn, "problem_annotations")
    if "constraints_text" not in annotation_columns:
        conn.execute("ALTER TABLE problem_annotations ADD COLUMN constraints_text TEXT")
    if "tricks_json" not in annotation_columns:
        conn.execute("ALTER TABLE problem_annotations ADD COLUMN tricks_json TEXT NOT NULL DEFAULT '[]'")

    problem_columns = _columns(conn, "problems")
    if "canonical_problem_uid" not in problem_columns:
        conn.execute("ALTER TABLE problems ADD COLUMN canonical_problem_uid TEXT")
    if "dedupe_status" not in problem_columns:
        conn.execute("ALTER TABLE problems ADD COLUMN dedupe_status TEXT NOT NULL DEFAULT 'canonical'")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_problems_canonical ON problems(canonical_problem_uid, dedupe_status)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS problem_user_state (
            problem_uid TEXT PRIMARY KEY REFERENCES problems(problem_uid) ON DELETE CASCADE,
            favorite INTEGER NOT NULL DEFAULT 0 CHECK (favorite IN (0, 1)),
            note TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_problem_user_state_favorite ON problem_user_state(favorite, problem_uid)"
    )


def init_db(path: str | Path = DEFAULT_DB_PATH, seed: bool = True) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        migrate_db(conn)
        if seed:
            seed_tags(conn)
