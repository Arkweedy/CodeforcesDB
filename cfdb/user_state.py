from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .db import CfConnection, DEFAULT_DB_PATH, ROOT


DEFAULT_USER_DB_PATH = ROOT / "data" / "cfdb.user.sqlite"
PROGRESS_VALUES = {"unattempted", "attempted", "solved"}
PRIORITY_VALUES = {"critical", "high", "normal", "low"}

USER_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    codeforces_handle TEXT NOT NULL DEFAULT '',
    locale TEXT NOT NULL DEFAULT 'zh' CHECK (locale IN ('zh', 'en')),
    page_size INTEGER NOT NULL DEFAULT 50 CHECK (page_size IN (20, 50, 100)),
    density TEXT NOT NULL DEFAULT 'comfortable' CHECK (density IN ('comfortable', 'compact')),
    last_submission_id INTEGER,
    last_sync_at TEXT,
    last_sync_error TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS problem_user_state (
    problem_uid TEXT PRIMARY KEY,
    favorite INTEGER NOT NULL DEFAULT 0 CHECK (favorite IN (0, 1)),
    note TEXT NOT NULL DEFAULT '',
    manual_progress TEXT CHECK (
        manual_progress IN ('unattempted', 'attempted', 'solved') OR manual_progress IS NULL
    ),
    synced_progress TEXT CHECK (
        synced_progress IN ('unattempted', 'attempted', 'solved') OR synced_progress IS NULL
    ),
    priority TEXT CHECK (
        priority IN ('critical', 'high', 'normal', 'low') OR priority IS NULL
    ),
    progress_synced_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS migration_meta (
    key TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_state_favorite
    ON problem_user_state(favorite, problem_uid);
CREATE INDEX IF NOT EXISTS idx_user_state_progress
    ON problem_user_state(manual_progress, synced_progress, problem_uid);
CREATE INDEX IF NOT EXISTS idx_user_state_priority
    ON problem_user_state(priority, problem_uid);
"""


def resolve_user_db_path(path: str | Path | None = None) -> Path:
    return Path(path or os.environ.get("CFDB_USER_PATH", DEFAULT_USER_DB_PATH))


def connect_user(path: str | Path = DEFAULT_USER_DB_PATH) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, factory=CfConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_user_db(
    path: str | Path = DEFAULT_USER_DB_PATH,
    catalog_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    user_path = Path(path)
    with connect_user(user_path) as conn:
        conn.executescript(USER_SCHEMA)
        conn.execute("INSERT OR IGNORE INTO app_settings(id) VALUES (1)")

        migrated = conn.execute(
            "SELECT 1 FROM migration_meta WHERE key = 'legacy-main-user-state-v1'"
        ).fetchone()
        catalog = Path(catalog_path)
        user_state_is_empty = conn.execute(
            "SELECT 1 FROM problem_user_state LIMIT 1"
        ).fetchone() is None
        if migrated is None and user_state_is_empty and catalog.exists():
            catalog_uri = f"file:{catalog.resolve().as_posix()}?mode=ro"
            with sqlite3.connect(catalog_uri, uri=True, factory=CfConnection) as legacy:
                table = legacy.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='problem_user_state'"
                ).fetchone()
                if table:
                    rows = legacy.execute(
                        "SELECT problem_uid, favorite, note, updated_at FROM problem_user_state"
                    ).fetchall()
                    conn.executemany(
                        """
                        INSERT OR IGNORE INTO problem_user_state(
                            problem_uid, favorite, note, updated_at
                        ) VALUES (?, ?, ?, ?)
                        """,
                        rows,
                    )
            conn.execute(
                "INSERT INTO migration_meta(key) VALUES ('legacy-main-user-state-v1')"
            )


@contextmanager
def connect_catalog_with_user(
    catalog_path: str | Path,
    user_path: str | Path,
) -> Iterator[sqlite3.Connection]:
    catalog = Path(catalog_path)
    user = Path(user_path)
    init_user_db(user, catalog)
    uri = f"file:{catalog.resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("ATTACH DATABASE ? AS userdb", (str(user.resolve()),))
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def read_settings(path: str | Path) -> dict[str, object]:
    with connect_user(path) as conn:
        row = conn.execute("SELECT * FROM app_settings WHERE id = 1").fetchone()
    if row is None:
        raise RuntimeError("user settings were not initialized")
    return dict(row)


def update_settings(path: str | Path, changes: dict[str, object]) -> dict[str, object]:
    allowed = {"codeforces_handle", "locale", "page_size", "density"}
    unknown = set(changes) - allowed
    if unknown:
        raise ValueError(f"unsupported settings: {', '.join(sorted(unknown))}")

    with connect_user(path) as conn:
        current = conn.execute("SELECT * FROM app_settings WHERE id = 1").fetchone()
        if current is None:
            raise RuntimeError("user settings were not initialized")
        old_handle = str(current["codeforces_handle"])
        new_handle = str(changes.get("codeforces_handle", old_handle)).strip()
        normalized = dict(changes)
        if "codeforces_handle" in normalized:
            normalized["codeforces_handle"] = new_handle
        if normalized:
            assignments = ", ".join(f"{field} = ?" for field in normalized)
            conn.execute(
                f"UPDATE app_settings SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id=1",
                tuple(normalized.values()),
            )
        if new_handle != old_handle:
            conn.execute(
                """
                UPDATE problem_user_state
                SET synced_progress = NULL, progress_synced_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                """
            )
            conn.execute(
                """
                UPDATE app_settings
                SET last_submission_id=NULL, last_sync_at=NULL, last_sync_error=NULL
                WHERE id=1
                """
            )
        row = conn.execute("SELECT * FROM app_settings WHERE id = 1").fetchone()
    return dict(row) if row else {}


def user_state_dict(row: sqlite3.Row | None, problem_uid: str) -> dict[str, object]:
    if row is None:
        return {
            "problem_uid": problem_uid,
            "favorite": False,
            "note": "",
            "manual_progress": None,
            "synced_progress": None,
            "progress_status": "unattempted",
            "priority": None,
            "progress_synced_at": None,
            "updated_at": None,
        }
    manual = row["manual_progress"]
    synced = row["synced_progress"]
    return {
        "problem_uid": problem_uid,
        "favorite": bool(row["favorite"]),
        "note": row["note"],
        "manual_progress": manual,
        "synced_progress": synced,
        "progress_status": manual or synced or "unattempted",
        "priority": row["priority"],
        "progress_synced_at": row["progress_synced_at"],
        "updated_at": row["updated_at"],
    }


def read_user_state(conn: sqlite3.Connection, problem_uid: str) -> dict[str, object]:
    row = conn.execute(
        "SELECT * FROM userdb.problem_user_state WHERE problem_uid = ?",
        (problem_uid,),
    ).fetchone()
    return user_state_dict(row, problem_uid)


def patch_user_state(
    conn: sqlite3.Connection,
    problem_uid: str,
    changes: dict[str, object],
) -> dict[str, object]:
    allowed = {"favorite", "note", "manual_progress", "priority"}
    unknown = set(changes) - allowed
    if unknown:
        raise ValueError(f"unsupported user state: {', '.join(sorted(unknown))}")
    if "manual_progress" in changes:
        progress = changes["manual_progress"]
        if progress is not None and progress not in PROGRESS_VALUES:
            raise ValueError("invalid manual progress")
    if "priority" in changes:
        priority = changes["priority"]
        if priority is not None and priority not in PRIORITY_VALUES:
            raise ValueError("invalid priority")

    current_row = conn.execute(
        "SELECT * FROM userdb.problem_user_state WHERE problem_uid = ?",
        (problem_uid,),
    ).fetchone()
    current = user_state_dict(current_row, problem_uid)
    values = {
        "favorite": int(bool(changes.get("favorite", current["favorite"]))),
        "note": str(changes.get("note", current["note"])),
        "manual_progress": changes.get("manual_progress", current["manual_progress"]),
        "synced_progress": current["synced_progress"],
        "priority": changes.get("priority", current["priority"]),
        "progress_synced_at": current["progress_synced_at"],
    }
    conn.execute(
        """
        INSERT INTO userdb.problem_user_state(
            problem_uid, favorite, note, manual_progress, synced_progress,
            priority, progress_synced_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(problem_uid) DO UPDATE SET
            favorite=excluded.favorite,
            note=excluded.note,
            manual_progress=excluded.manual_progress,
            synced_progress=excluded.synced_progress,
            priority=excluded.priority,
            progress_synced_at=excluded.progress_synced_at,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            problem_uid,
            values["favorite"],
            values["note"],
            values["manual_progress"],
            values["synced_progress"],
            values["priority"],
            values["progress_synced_at"],
        ),
    )
    return read_user_state(conn, problem_uid)
