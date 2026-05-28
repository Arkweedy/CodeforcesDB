from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass


DIVISION_RE = re.compile(r"\bdiv\.?\s*([12])\b", re.IGNORECASE)


@dataclass(frozen=True)
class DuplicateProblem:
    alias_problem_uid: str
    canonical_problem_uid: str
    alias_contest_id: int
    alias_problem_index: str
    canonical_contest_id: int
    canonical_problem_index: str
    title: str


def contest_division(title: str) -> int | None:
    divisions = {int(match.group(1)) for match in DIVISION_RE.finditer(title)}
    if divisions == {1}:
        return 1
    if divisions == {2}:
        return 2
    return None


def division_pair_key(title: str, start_time_seconds: int | None) -> str | None:
    if contest_division(title) is None:
        return None
    base = title.lower()
    base = re.sub(r"\([^)]*\bdiv\.?\s*[12]\b[^)]*\)", "", base, flags=re.IGNORECASE)
    base = re.sub(r"\s+", " ", base).strip()
    if not base:
        return None
    return f"{base}|{start_time_seconds or 0}"


def problem_title_key(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def is_canonical_problem(row: sqlite3.Row) -> bool:
    canonical = row["canonical_problem_uid"] if "canonical_problem_uid" in row.keys() else None
    return canonical is None or canonical == row["problem_uid"]


def canonical_problem_uid(conn: sqlite3.Connection, problem_uid: str) -> str:
    row = conn.execute(
        "SELECT canonical_problem_uid FROM problems WHERE problem_uid = ?",
        (problem_uid,),
    ).fetchone()
    if row and row["canonical_problem_uid"]:
        return str(row["canonical_problem_uid"])
    return problem_uid


def find_division_duplicates(conn: sqlite3.Connection) -> list[DuplicateProblem]:
    contests = conn.execute(
        """
        SELECT contest_id, title, start_time_seconds
        FROM contests
        WHERE eligibility_status = 'eligible'
        """
    ).fetchall()

    groups: dict[str, dict[int, list[sqlite3.Row]]] = {}
    for contest in contests:
        division = contest_division(contest["title"])
        key = division_pair_key(contest["title"], contest["start_time_seconds"])
        if division is None or key is None:
            continue
        groups.setdefault(key, {}).setdefault(division, []).append(contest)

    duplicates: list[DuplicateProblem] = []
    for group in groups.values():
        for div1_contest in group.get(1, []):
            div1_rows = conn.execute(
                """
                SELECT problem_uid, contest_id, problem_index, title
                FROM problems
                WHERE contest_id = ?
                """,
                (div1_contest["contest_id"],),
            ).fetchall()
            div1_by_title = {problem_title_key(row["title"]): row for row in div1_rows}

            for div2_contest in group.get(2, []):
                div2_rows = conn.execute(
                    """
                    SELECT problem_uid, contest_id, problem_index, title
                    FROM problems
                    WHERE contest_id = ?
                    """,
                    (div2_contest["contest_id"],),
                ).fetchall()
                for alias in div2_rows:
                    canonical = div1_by_title.get(problem_title_key(alias["title"]))
                    if canonical is None:
                        continue
                    duplicates.append(
                        DuplicateProblem(
                            alias_problem_uid=alias["problem_uid"],
                            canonical_problem_uid=canonical["problem_uid"],
                            alias_contest_id=int(alias["contest_id"]),
                            alias_problem_index=alias["problem_index"],
                            canonical_contest_id=int(canonical["contest_id"]),
                            canonical_problem_index=canonical["problem_index"],
                            title=alias["title"],
                        )
                    )
    return duplicates


def mark_division_duplicates(conn: sqlite3.Connection) -> list[DuplicateProblem]:
    duplicates = find_division_duplicates(conn)
    for item in duplicates:
        conn.execute(
            """
            UPDATE problems
            SET canonical_problem_uid = ?, dedupe_status = 'duplicate_div2', updated_at = CURRENT_TIMESTAMP
            WHERE problem_uid = ?
            """,
            (item.canonical_problem_uid, item.alias_problem_uid),
        )
        conn.execute(
            """
            UPDATE problems
            SET canonical_problem_uid = NULL, dedupe_status = 'canonical', updated_at = CURRENT_TIMESTAMP
            WHERE problem_uid = ?
            """,
            (item.canonical_problem_uid,),
        )
        conn.execute(
            """
            INSERT INTO problem_aliases(
                alias_problem_uid, canonical_problem_uid, alias_contest_id, alias_problem_index, reason
            )
            VALUES (?, ?, ?, ?, 'div1_div2_overlap_prefer_div1')
            ON CONFLICT(alias_problem_uid) DO UPDATE SET
                canonical_problem_uid = excluded.canonical_problem_uid,
                reason = excluded.reason,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                item.alias_problem_uid,
                item.canonical_problem_uid,
                item.alias_contest_id,
                item.alias_problem_index,
            ),
        )

        alias_sources = conn.execute(
            """
            SELECT source_type, url, notes
            FROM problem_sources
            WHERE problem_uid = ?
            """,
            (item.alias_problem_uid,),
        ).fetchall()
        for source in alias_sources:
            source_type = "alias_" + source["source_type"]
            conn.execute(
                """
                INSERT INTO problem_sources(problem_uid, source_type, url, notes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(problem_uid, source_type, url) DO UPDATE SET
                    notes = COALESCE(excluded.notes, problem_sources.notes)
                """,
                (item.canonical_problem_uid, source_type, source["url"], source["notes"]),
            )

        alias_tags = conn.execute(
            """
            SELECT tag, importance, evidence
            FROM problem_tags
            WHERE problem_uid = ? AND source = 'cf_official'
            """,
            (item.alias_problem_uid,),
        ).fetchall()
        for tag in alias_tags:
            conn.execute(
                """
                INSERT OR IGNORE INTO problem_tags(problem_uid, tag, importance, evidence, source)
                VALUES (?, ?, ?, ?, 'cf_official_alias')
                """,
                (
                    item.canonical_problem_uid,
                    tag["tag"],
                    tag["importance"],
                    f"Alias {item.alias_contest_id}{item.alias_problem_index}: {tag['evidence']}",
                ),
            )

        conn.execute("DELETE FROM problem_tags WHERE problem_uid = ?", (item.alias_problem_uid,))
        conn.execute("DELETE FROM solution_variants WHERE problem_uid = ?", (item.alias_problem_uid,))
        conn.execute("DELETE FROM problem_annotations WHERE problem_uid = ?", (item.alias_problem_uid,))
        conn.execute("DELETE FROM rating_refresh_queue WHERE problem_uid = ?", (item.alias_problem_uid,))
    return duplicates


def canonical_problem_count(conn: sqlite3.Connection, start: int, end: int) -> int:
    lo, hi = sorted((start, end))
    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM problems
        WHERE contest_id BETWEEN ? AND ?
          AND (canonical_problem_uid IS NULL OR canonical_problem_uid = problem_uid)
        """,
        (lo, hi),
    ).fetchone()
    return int(row["count"])
