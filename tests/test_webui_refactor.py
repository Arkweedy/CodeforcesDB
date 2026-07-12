from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from cfdb.db import connect, init_db
from cfdb.user_state import connect_catalog_with_user, init_user_db, read_settings
from cfdb.web_app import create_app


class FakeCodeforcesClient:
    def __init__(self) -> None:
        self.calls = 0

    def user_status(self, handle: str, *, offset: int, count: int):  # type: ignore[no-untyped-def]
        self.calls += 1
        if offset > 1:
            return []
        return [
            {
                "id": 99,
                "verdict": "OK",
                "problem": {"contestId": 100, "index": "A"},
            },
            {
                "id": 98,
                "verdict": "WRONG_ANSWER",
                "problem": {"contestId": 100, "index": "B"},
            },
        ]


class IncrementalCodeforcesClient:
    def __init__(self) -> None:
        self.calls = 0
        self.fail = False

    def user_status(self, handle: str, *, offset: int, count: int):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.fail:
            raise RuntimeError("temporary sync failure")
        if self.calls == 1:
            return [
                {
                    "id": 99,
                    "verdict": "WRONG_ANSWER",
                    "problem": {"contestId": 100, "index": "A"},
                }
            ]
        return [
            {
                "id": 100,
                "verdict": "OK",
                "problem": {"contestId": 100, "index": "A"},
            },
            {
                "id": 99,
                "verdict": "WRONG_ANSWER",
                "problem": {"contestId": 100, "index": "A"},
            },
        ]


class AliasCodeforcesClient:
    def user_status(self, handle: str, *, offset: int, count: int):  # type: ignore[no-untyped-def]
        return [
            {
                "id": 101,
                "verdict": "OK",
                "problem": {"contestId": 101, "index": "A"},
            }
        ]


class WebUiRefactorTests(unittest.TestCase):
    def seed(self, db: Path) -> None:
        init_db(db, seed=False)
        with connect(db) as conn:
            conn.execute(
                """
                INSERT INTO contests(
                    contest_id, contest_uid, title, eligibility_status, extraction_status
                ) VALUES (100, 'cf_contest:100', 'Round 100', 'eligible', 'problems_loaded')
                """
            )
            conn.executemany(
                """
                INSERT INTO problems(
                    problem_uid, contest_id, problem_index, title, rating, rating_status,
                    canonical_url, problemset_url
                ) VALUES (?, 100, ?, ?, ?, 'official', ?, ?)
                """,
                [
                    (
                        "cf_problem:100:A", "A", "Alpha", 1500,
                        "https://codeforces.com/contest/100/problem/A",
                        "https://codeforces.com/problemset/problem/100/A",
                    ),
                    (
                        "cf_problem:100:B", "B", "Beta", 1900,
                        "https://codeforces.com/contest/100/problem/B",
                        "https://codeforces.com/problemset/problem/100/B",
                    ),
                ],
            )
            conn.executemany(
                "INSERT INTO problem_annotations(problem_uid, review_status) VALUES (?, 'reviewed')",
                [("cf_problem:100:A",), ("cf_problem:100:B",)],
            )
            conn.execute(
                "INSERT INTO tags(tag, display_name, status) VALUES ('dp', 'DP', 'active')"
            )
            conn.executemany(
                """
                INSERT INTO problem_tags(problem_uid, tag, importance, source)
                VALUES (?, 'dp', ?, 'ai_reviewed')
                """,
                [("cf_problem:100:A", "primary"), ("cf_problem:100:B", "secondary")],
            )

    def test_overlay_search_partial_patch_and_facets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "catalog.sqlite"
            user = root / "user.sqlite"
            self.seed(db)
            client = TestClient(create_app(db, user))

            search = client.get("/api/search", params={"limit": 20})
            self.assertEqual(search.status_code, 200)
            body = search.json()
            self.assertEqual(body["total"], 2)
            self.assertEqual(body["summary"]["unattempted"], 2)
            self.assertEqual(body["facets"]["tag_counts"]["dp"], 2)

            state = client.patch(
                "/api/problems/cf_problem:100:A/user-state",
                json={"favorite": True, "manual_progress": "solved", "priority": "critical"},
            )
            self.assertEqual(state.status_code, 200)
            self.assertTrue(state.json()["favorite"])
            self.assertEqual(state.json()["progress_status"], "solved")

            note = client.patch(
                "/api/problems/cf_problem:100:A/user-state",
                json={"note": "keep favorite"},
            )
            self.assertTrue(note.json()["favorite"])
            self.assertEqual(note.json()["note"], "keep favorite")

            filtered = client.get(
                "/api/search",
                params={"favorite": "favorite", "progress_status": "solved"},
            ).json()
            self.assertEqual(filtered["total"], 1)
            self.assertEqual(filtered["items"][0]["priority"], "critical")

            with connect(db) as conn:
                self.assertEqual(
                    conn.execute("SELECT COUNT(*) FROM problem_user_state").fetchone()[0],
                    0,
                )

    def test_settings_and_manual_codeforces_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "catalog.sqlite"
            user = root / "user.sqlite"
            self.seed(db)
            fake = FakeCodeforcesClient()
            client = TestClient(create_app(db, user, fake))  # type: ignore[arg-type]

            settings = client.patch(
                "/api/settings", json={"codeforces_handle": "tourist", "page_size": 20}
            )
            self.assertEqual(settings.status_code, 200)
            self.assertEqual(settings.json()["page_size"], 20)

            result = client.post("/api/sync/codeforces", json={"full": True})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["matched_problems"], 2)
            self.assertEqual(fake.calls, 1)

            search = client.get("/api/search", params={"sort_by": "progress"}).json()
            states = {item["problem_uid"]: item["progress_status"] for item in search["items"]}
            self.assertEqual(states["cf_problem:100:A"], "solved")
            self.assertEqual(states["cf_problem:100:B"], "attempted")

            analytics = client.get("/api/analytics", params={"scope": "global"})
            self.assertEqual(analytics.status_code, 200)
            self.assertEqual(analytics.json()["summary"]["total"], 2)
            self.assertIsNone(read_settings(user)["last_sync_error"])

    def test_legacy_state_is_copied_without_deleting_catalog_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "catalog.sqlite"
            user = root / "user.sqlite"
            self.seed(db)
            with connect(db) as conn:
                conn.execute(
                    "INSERT INTO problem_user_state(problem_uid, favorite, note) VALUES (?, 1, 'legacy')",
                    ("cf_problem:100:A",),
                )
            init_user_db(user, db)
            with connect_catalog_with_user(db, user) as conn:
                copied = conn.execute(
                    "SELECT favorite, note FROM userdb.problem_user_state WHERE problem_uid=?",
                    ("cf_problem:100:A",),
                ).fetchone()
                self.assertEqual((copied["favorite"], copied["note"]), (1, "legacy"))
            with connect(db) as conn:
                self.assertEqual(
                    conn.execute("SELECT COUNT(*) FROM problem_user_state").fetchone()[0],
                    1,
                )

    def test_incremental_sync_and_failure_preserve_last_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "catalog.sqlite"
            user = root / "user.sqlite"
            self.seed(db)
            fake = IncrementalCodeforcesClient()
            client = TestClient(create_app(db, user, fake))  # type: ignore[arg-type]
            client.patch("/api/settings", json={"codeforces_handle": "tourist"})

            first = client.post("/api/sync/codeforces", json={"full": True})
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.json()["last_submission_id"], 99)
            self.assertEqual(
                client.get("/api/search").json()["items"][0]["progress_status"],
                "attempted",
            )

            second = client.post("/api/sync/codeforces", json={"full": False})
            self.assertEqual(second.status_code, 200)
            self.assertEqual(second.json()["submissions_processed"], 1)
            self.assertEqual(second.json()["last_submission_id"], 100)
            before_failure = read_settings(user)

            fake.fail = True
            failed = client.post("/api/sync/codeforces", json={"full": False})
            self.assertEqual(failed.status_code, 502)
            after_failure = read_settings(user)
            self.assertEqual(after_failure["last_sync_at"], before_failure["last_sync_at"])
            self.assertEqual(after_failure["last_submission_id"], 100)
            self.assertIn("temporary sync failure", str(after_failure["last_sync_error"]))
            state = client.get("/api/search").json()["items"][0]
            self.assertEqual(state["synced_progress"], "solved")

    def test_alias_sync_manual_override_and_handle_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "catalog.sqlite"
            user = root / "user.sqlite"
            self.seed(db)
            with connect(db) as conn:
                conn.execute(
                    """
                    INSERT INTO problem_aliases(
                        alias_problem_uid, canonical_problem_uid,
                        alias_contest_id, alias_problem_index, reason
                    ) VALUES ('cf_problem:101:A', 'cf_problem:100:A', 101, 'A', 'shared')
                    """
                )
            client = TestClient(create_app(db, user, AliasCodeforcesClient()))  # type: ignore[arg-type]
            client.patch("/api/settings", json={"codeforces_handle": "first"})
            client.patch(
                "/api/problems/cf_problem:100:A/user-state",
                json={
                    "favorite": True,
                    "note": "preserve me",
                    "manual_progress": "attempted",
                    "priority": "high",
                },
            )
            synced = client.post("/api/sync/codeforces", json={"full": True})
            self.assertEqual(synced.status_code, 200)
            state = client.get("/api/problems/cf_problem:100:A").json()["user_state"]
            self.assertEqual(state["synced_progress"], "solved")
            self.assertEqual(state["progress_status"], "attempted")

            restored = client.patch(
                "/api/problems/cf_problem:100:A/user-state",
                json={"manual_progress": None},
            ).json()
            self.assertEqual(restored["progress_status"], "solved")
            client.patch(
                "/api/problems/cf_problem:100:A/user-state",
                json={"manual_progress": "attempted"},
            )
            client.patch("/api/settings", json={"codeforces_handle": "second"})
            changed = client.get("/api/problems/cf_problem:100:A").json()["user_state"]
            self.assertIsNone(changed["synced_progress"])
            self.assertEqual(changed["progress_status"], "attempted")
            self.assertTrue(changed["favorite"])
            self.assertEqual(changed["note"], "preserve me")
            self.assertEqual(changed["priority"], "high")


if __name__ == "__main__":
    unittest.main()
