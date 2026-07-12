from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .codeforces import CodeforcesClient
from .db import CfConnection
from .user_state import connect_user, read_settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _problem_mapping(catalog_path: str | Path) -> dict[tuple[int, str], str]:
    mapping: dict[tuple[int, str], str] = {}
    catalog = Path(catalog_path)
    uri = f"file:{catalog.resolve().as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True, factory=CfConnection) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute(
            """
            SELECT contest_id, problem_index,
                   COALESCE(canonical_problem_uid, problem_uid) AS canonical_uid
            FROM problems
            """
        ):
            mapping[(int(row["contest_id"]), str(row["problem_index"]))] = str(
                row["canonical_uid"]
            )
        for row in conn.execute(
            """
            SELECT alias_contest_id, alias_problem_index, canonical_problem_uid
            FROM problem_aliases
            """
        ):
            mapping[(int(row["alias_contest_id"]), str(row["alias_problem_index"]))] = str(
                row["canonical_problem_uid"]
            )
    return mapping


def sync_codeforces_progress(
    catalog_path: str | Path,
    user_path: str | Path,
    *,
    full: bool = False,
    client: CodeforcesClient | None = None,
    progress: Callable[[int], None] | None = None,
) -> dict[str, object]:
    settings = read_settings(user_path)
    handle = str(settings["codeforces_handle"]).strip()
    if not handle:
        raise ValueError("Codeforces handle is not configured")

    api = client or CodeforcesClient(user_agent="cfdb-webui/1.0")
    cursor = None if full else settings.get("last_submission_id")
    submissions: list[dict[str, Any]] = []
    offset = 1
    batch_size = 1000
    newest_id = int(cursor) if cursor is not None else 0

    try:
        while True:
            batch = api.user_status(handle, offset=offset, count=batch_size)
            if not batch:
                break
            stop = False
            for submission in batch:
                submission_id = int(submission.get("id", 0))
                newest_id = max(newest_id, submission_id)
                if cursor is not None and submission_id <= int(cursor):
                    stop = True
                    break
                submissions.append(submission)
            if progress:
                progress(len(submissions))
            if stop or len(batch) < batch_size:
                break
            offset += batch_size
    except Exception as exc:
        with connect_user(user_path) as conn:
            conn.execute(
                "UPDATE app_settings SET last_sync_error=?, updated_at=CURRENT_TIMESTAMP WHERE id=1",
                (str(exc),),
            )
        raise

    mapping = _problem_mapping(catalog_path)
    updates: dict[str, str] = {}
    for submission in submissions:
        problem = submission.get("problem") or {}
        contest_id = problem.get("contestId")
        index = problem.get("index")
        if contest_id is None or not index:
            continue
        problem_uid = mapping.get((int(contest_id), str(index)))
        if not problem_uid:
            continue
        next_status = "solved" if submission.get("verdict") == "OK" else "attempted"
        if updates.get(problem_uid) != "solved":
            updates[problem_uid] = next_status

    synced_at = _now()
    with connect_user(user_path) as conn:
        if full:
            conn.execute(
                "UPDATE problem_user_state SET synced_progress=NULL, progress_synced_at=NULL"
            )
        for problem_uid, status in updates.items():
            row = conn.execute(
                "SELECT synced_progress FROM problem_user_state WHERE problem_uid=?",
                (problem_uid,),
            ).fetchone()
            if not full and row and row["synced_progress"] == "solved":
                status = "solved"
            conn.execute(
                """
                INSERT INTO problem_user_state(
                    problem_uid, synced_progress, progress_synced_at, updated_at
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(problem_uid) DO UPDATE SET
                    synced_progress=excluded.synced_progress,
                    progress_synced_at=excluded.progress_synced_at,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (problem_uid, status, synced_at),
            )
        conn.execute(
            """
            UPDATE app_settings
            SET last_submission_id=?, last_sync_at=?, last_sync_error=NULL,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=1
            """,
            (newest_id or None, synced_at),
        )

    return {
        "mode": "full" if full else "incremental",
        "handle": handle,
        "submissions_processed": len(submissions),
        "matched_problems": len(updates),
        "attempted": sum(status == "attempted" for status in updates.values()),
        "solved": sum(status == "solved" for status in updates.values()),
        "last_submission_id": newest_id or None,
        "last_sync_at": synced_at,
    }
