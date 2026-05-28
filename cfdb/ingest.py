from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from .codeforces import CodeforcesClient
from .dedup import mark_division_duplicates
from .eligibility import classify_contest
from .normalize import normalize_problem_key, contest_uid
from .tags import TagInput, ensure_tag, map_official_tag


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def from_timestamp(seconds: int | None) -> datetime | None:
    if seconds is None:
        return None
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def upsert_ingestion_range(conn: sqlite3.Connection, start: int, end: int) -> None:
    lo, hi = sorted((start, end))
    for contest_id in range(lo, hi + 1):
        conn.execute(
            """
            INSERT INTO ingestion_queue(contest_id, status)
            VALUES (?, 'queued')
            ON CONFLICT(contest_id) DO UPDATE SET
                status = CASE
                    WHEN ingestion_queue.status IN ('done', 'in_progress') THEN ingestion_queue.status
                    ELSE 'queued'
                END,
                updated_at = CURRENT_TIMESTAMP
            """,
            (contest_id,),
        )


def _contest_type(name: str, cf_type: str | None) -> str:
    lower = name.lower()
    if "educational" in lower:
        return "educational"
    if "codeforces round" in lower or "codeforces global round" in lower:
        return "codeforces-round"
    if "good bye" in lower or "hello " in lower:
        return "seasonal-round"
    if cf_type:
        return cf_type.lower()
    return "unknown"


def upsert_contest(conn: sqlite3.Connection, contest: dict[str, Any]) -> str:
    contest_id = int(contest["id"])
    name = contest["name"]
    existing = conn.execute(
        "SELECT manual_override FROM contests WHERE contest_id = ?", (contest_id,)
    ).fetchone()
    manual_override = existing["manual_override"] if existing else None
    eligibility = classify_contest(name, contest.get("type"), manual_override)
    start_dt = from_timestamp(contest.get("startTimeSeconds"))
    status = "excluded" if eligibility.status == "excluded" else "metadata_loaded"
    conn.execute(
        """
        INSERT INTO contests(
            contest_id, contest_uid, title, phase, cf_type, start_time_seconds, start_time_utc,
            duration_seconds, contest_type, eligibility_status, manual_override,
            exclusion_reason, extraction_status, last_checked_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(contest_id) DO UPDATE SET
            title = excluded.title,
            phase = excluded.phase,
            cf_type = excluded.cf_type,
            start_time_seconds = excluded.start_time_seconds,
            start_time_utc = excluded.start_time_utc,
            duration_seconds = excluded.duration_seconds,
            contest_type = excluded.contest_type,
            eligibility_status = excluded.eligibility_status,
            exclusion_reason = excluded.exclusion_reason,
            extraction_status = CASE
                WHEN contests.extraction_status = 'problems_loaded' AND excluded.extraction_status <> 'excluded'
                    THEN contests.extraction_status
                ELSE excluded.extraction_status
            END,
            last_checked_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            contest_id,
            contest_uid(contest_id),
            name,
            contest.get("phase"),
            contest.get("type"),
            contest.get("startTimeSeconds"),
            iso_utc(start_dt),
            contest.get("durationSeconds"),
            _contest_type(name, contest.get("type")),
            eligibility.status,
            manual_override,
            eligibility.reason,
            status,
        ),
    )
    return eligibility.status


def rating_state(problem: dict[str, Any], contest: sqlite3.Row, pending_days: int) -> tuple[int | None, str, str | None, str | None]:
    now = utc_now()
    if problem.get("rating") is not None:
        return int(problem["rating"]), "official", "codeforces", None

    start_seconds = contest["start_time_seconds"]
    start = from_timestamp(start_seconds) if start_seconds else None
    if start and now - start <= timedelta(days=pending_days):
        return None, "pending_cf_rating", None, iso_utc(now + timedelta(days=7))
    return None, "no_cf_rating", None, None


def upsert_problem(
    conn: sqlite3.Connection,
    problem: dict[str, Any],
    contest: sqlite3.Row,
    pending_days: int,
    min_rating: int = 1400,
) -> str | None:
    key = normalize_problem_key(problem["contestId"], problem["index"])
    if problem.get("rating") is not None and int(problem["rating"]) < min_rating:
        conn.execute("DELETE FROM problems WHERE problem_uid = ?", (key.problem_uid,))
        conn.execute("DELETE FROM rating_refresh_queue WHERE problem_uid = ?", (key.problem_uid,))
        return None

    official_tags = list(problem.get("tags", []))
    rating, status, source, next_check = rating_state(problem, contest, pending_days)
    conn.execute(
        """
        INSERT INTO problems(
            problem_uid, contest_id, problem_index, title, problem_type, points,
            rating, rating_status, rating_source, rating_last_checked_at, next_rating_check_at,
            canonical_url, problemset_url, official_tags_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
        ON CONFLICT(problem_uid) DO UPDATE SET
            title = excluded.title,
            problem_type = excluded.problem_type,
            points = excluded.points,
            rating = excluded.rating,
            rating_status = excluded.rating_status,
            rating_source = excluded.rating_source,
            rating_last_checked_at = CURRENT_TIMESTAMP,
            next_rating_check_at = excluded.next_rating_check_at,
            canonical_url = excluded.canonical_url,
            problemset_url = excluded.problemset_url,
            official_tags_json = excluded.official_tags_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            key.problem_uid,
            key.contest_id,
            key.index,
            problem["name"],
            problem.get("type"),
            problem.get("points"),
            rating,
            status,
            source,
            next_check,
            key.canonical_url,
            key.problemset_url,
            json.dumps(official_tags, ensure_ascii=True),
        ),
    )

    for source_type, url in (("canonical", key.canonical_url), ("problemset", key.problemset_url)):
        conn.execute(
            """
            INSERT OR IGNORE INTO problem_sources(problem_uid, source_type, url)
            VALUES (?, ?, ?)
            """,
            (key.problem_uid, source_type, url),
        )

    if status == "pending_cf_rating" and next_check:
        conn.execute(
            """
            INSERT INTO rating_refresh_queue(problem_uid, contest_id, problem_index, next_check_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(problem_uid) DO UPDATE SET
                next_check_at = excluded.next_check_at,
                status = 'queued',
                updated_at = CURRENT_TIMESTAMP
            """,
            (key.problem_uid, key.contest_id, key.index, next_check),
        )
    else:
        conn.execute("DELETE FROM rating_refresh_queue WHERE problem_uid = ?", (key.problem_uid,))

    if official_tags:
        summary = "Pending detailed review. Auto-seeded from Codeforces official tags: " + ", ".join(official_tags)
    else:
        summary = "Pending detailed review. No Codeforces official tags were available."
    conn.execute(
        """
        INSERT INTO problem_annotations(problem_uid, summary, confidence, review_status)
        VALUES (?, ?, 'low', 'auto_seeded')
        ON CONFLICT(problem_uid) DO NOTHING
        """,
        (key.problem_uid, summary),
    )

    for official_tag in official_tags:
        canonical_tag = map_official_tag(official_tag)
        ensure_tag(
            conn,
            TagInput(
                canonical_tag,
                display_name=canonical_tag.split("/")[-1].replace("-", " ").title(),
                description=f"Mapped from Codeforces official tag: {official_tag}.",
                status="active",
            ),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO problem_tags(problem_uid, tag, importance, evidence, source)
            VALUES (?, ?, 'secondary', ?, 'cf_official')
            """,
            (key.problem_uid, canonical_tag, f"Codeforces official tag: {official_tag}."),
        )

    return key.problem_uid


def ingest_contest(
    conn: sqlite3.Connection,
    client: CodeforcesClient,
    contest_id: int,
    contest_meta: dict[str, Any],
    pending_days: int = 45,
    min_rating: int = 1400,
) -> dict[str, Any]:
    conn.execute(
        """
        UPDATE ingestion_queue
        SET status = 'in_progress', last_error = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE contest_id = ?
        """,
        (contest_id,),
    )
    eligibility_status = upsert_contest(conn, contest_meta)
    if eligibility_status != "eligible":
        conn.execute(
            """
            UPDATE ingestion_queue
            SET status = 'skipped', updated_at = CURRENT_TIMESTAMP
            WHERE contest_id = ?
            """,
            (contest_id,),
        )
        return {"contest_id": contest_id, "status": "skipped", "problems": 0}

    standings = client.contest_standings(contest_id)
    contest_row = conn.execute("SELECT * FROM contests WHERE contest_id = ?", (contest_id,)).fetchone()
    problem_count = 0
    for problem in standings.get("problems", []):
        if int(problem.get("contestId", contest_id)) != contest_id:
            continue
        problem_uid = upsert_problem(conn, problem, contest_row, pending_days, min_rating=min_rating)
        if problem_uid is not None:
            problem_count += 1

    conn.execute(
        """
        UPDATE contests
        SET extraction_status = 'problems_loaded', updated_at = CURRENT_TIMESTAMP
        WHERE contest_id = ?
        """,
        (contest_id,),
    )
    conn.execute(
        """
        UPDATE ingestion_queue
        SET status = 'done', last_error = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE contest_id = ?
        """,
        (contest_id,),
    )
    mark_division_duplicates(conn)
    return {"contest_id": contest_id, "status": "done", "problems": problem_count}


def find_contest_meta(contests: list[dict[str, Any]], contest_id: int) -> dict[str, Any]:
    for contest in contests:
        if int(contest["id"]) == contest_id:
            return contest
    raise KeyError(f"contest {contest_id} not found in Codeforces contest.list")
