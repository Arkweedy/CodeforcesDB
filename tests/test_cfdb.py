from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cfdb.db import connect, init_db
from cfdb.dedup import canonical_problem_uid, mark_division_duplicates
from cfdb.normalize import parse_problem_ref
from cfdb.reviewed import ReviewedPayloadError, apply_reviewed_payload
from cfdb.search import search_problems
from cfdb.tags import descendants, resolve_tag


class CfDbTests(unittest.TestCase):
    def test_problem_url_normalization(self) -> None:
        a = parse_problem_ref("https://codeforces.com/problemset/problem/2231/A")
        b = parse_problem_ref("https://codeforces.com/contest/2231/problem/A")
        self.assertEqual(a, b)
        self.assertEqual(a.problem_uid, "cf_problem:2231:A")
        self.assertEqual(a.contest_uid, "cf_contest:2231")

    def test_tag_alias_and_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            with connect(db) as conn:
                self.assertEqual(resolve_tag(conn, "acam"), "algorithm/string/acam")
                self.assertIn("algorithm/dp/digit-dp", descendants(conn, "algorithm/dp"))

    def test_aggregate_tag_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            with connect(db) as conn:
                conn.execute(
                    """
                    INSERT INTO contests(contest_id, contest_uid, title, eligibility_status, extraction_status)
                    VALUES (1, 'cf_contest:1', 'Synthetic Contest', 'eligible', 'problems_loaded')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problems(
                        problem_uid, contest_id, problem_index, title, rating, rating_status,
                        canonical_url, problemset_url
                    )
                    VALUES (
                        'cf_problem:1:A', 1, 'A', 'ACAM DP', 2300, 'official',
                        'https://codeforces.com/contest/1/problem/A',
                        'https://codeforces.com/problemset/problem/1/A'
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problem_tags(problem_uid, tag, importance, evidence, source)
                    VALUES
                        ('cf_problem:1:A', 'algorithm/string/acam', 'primary', 'synthetic', 'manual'),
                        ('cf_problem:1:A', 'algorithm/dp/automaton-dp', 'primary', 'synthetic', 'manual')
                    """
                )
                results = search_problems(conn, tags=["acam", "algorithm/dp"])
                self.assertEqual([item["problem_uid"] for item in results], ["cf_problem:1:A"])

    def reviewed_payload(self) -> dict[str, object]:
        return {
            "contest": {"contest_id": 2, "title": "Synthetic Contest"},
            "problem": {
                "contest_id": 2,
                "index": "B",
                "title": "Reviewed DP",
                "rating": 1800,
                "rating_status": "official",
                "official_tags": ["dp"],
            },
            "sources": [
                {
                    "source_type": "statement",
                    "url": "https://codeforces.com/contest/2/problem/B",
                    "notes": "Statement and constraints.",
                },
                {
                    "source_type": "editorial",
                    "url": "https://codeforces.com/blog/entry/example",
                    "notes": "Confirms the DP transition.",
                },
            ],
            "annotation": {
                "summary": "Synthetic reviewed problem.",
                "constraints": "n is small enough for DP.",
                "core_idea": "Build a DP over prefixes.",
                "complexity": "O(n^2)",
                "tricks": ["prefix state"],
                "confidence": "high",
                "review_status": "reviewed",
            },
            "solution_variants": [
                {
                    "name": "main",
                    "summary": "Prefix DP.",
                    "complexity": "O(n^2)",
                    "confidence": "high",
                    "is_primary": True,
                }
            ],
            "tags": [
                {
                    "tag": "algorithm/dp",
                    "importance": "primary",
                    "evidence": "The state transition is the solution core.",
                    "solution_variant": "main",
                }
            ],
        }

    def test_reviewed_payload_can_create_problem(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            with connect(db) as conn:
                problem_uid = apply_reviewed_payload(conn, self.reviewed_payload())
                self.assertEqual(problem_uid, "cf_problem:2:B")
                annotation = conn.execute(
                    "SELECT review_status, constraints_text, tricks_json FROM problem_annotations WHERE problem_uid = ?",
                    (problem_uid,),
                ).fetchone()
                self.assertEqual(annotation["review_status"], "reviewed")
                self.assertEqual(annotation["constraints_text"], "n is small enough for DP.")
                self.assertIn("prefix state", annotation["tricks_json"])
                results = search_problems(conn, rating_min=1800, rating_max=1800, tags=["algorithm/dp"])
                self.assertEqual([item["problem_uid"] for item in results], [problem_uid])

    def test_reviewed_payload_rejects_primary_without_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            payload = self.reviewed_payload()
            payload["tags"][0]["evidence"] = ""
            with connect(db) as conn:
                with self.assertRaises(ReviewedPayloadError):
                    apply_reviewed_payload(conn, payload)

    def test_reviewed_payload_rejects_new_tag_without_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            payload = self.reviewed_payload()
            payload["tags"] = [
                {
                    "tag": "trick/synthetic-new-observation",
                    "importance": "primary",
                    "evidence": "This observation is the solution core.",
                    "description": "A synthetic reusable observation.",
                    "created_reason": "Existing tags are too broad.",
                    "solution_variant": "main",
                }
            ]
            with connect(db) as conn:
                with self.assertRaises(ReviewedPayloadError):
                    apply_reviewed_payload(conn, payload)

    def test_reviewed_payload_rejects_low_rating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            payload = self.reviewed_payload()
            payload["problem"]["rating"] = 1300
            with connect(db) as conn:
                with self.assertRaises(ReviewedPayloadError):
                    apply_reviewed_payload(conn, payload)

    def test_div1_div2_overlap_prefers_div1_in_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            with connect(db) as conn:
                conn.execute(
                    """
                    INSERT INTO contests(contest_id, contest_uid, title, start_time_seconds, eligibility_status, extraction_status)
                    VALUES
                        (100, 'cf_contest:100', 'Codeforces Round 50 (Div. 1)', 12345, 'eligible', 'problems_loaded'),
                        (101, 'cf_contest:101', 'Codeforces Round 50 (Div. 2)', 12345, 'eligible', 'problems_loaded')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problems(
                        problem_uid, contest_id, problem_index, title, rating, rating_status,
                        canonical_url, problemset_url
                    )
                    VALUES
                        ('cf_problem:100:A', 100, 'A', 'Shared Problem', 1900, 'official',
                         'https://codeforces.com/contest/100/problem/A',
                         'https://codeforces.com/problemset/problem/100/A'),
                        ('cf_problem:101:C', 101, 'C', 'Shared Problem', 1900, 'official',
                         'https://codeforces.com/contest/101/problem/C',
                         'https://codeforces.com/problemset/problem/101/C')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problem_tags(problem_uid, tag, importance, evidence, source)
                    VALUES
                        ('cf_problem:100:A', 'algorithm/dp', 'primary', 'div1', 'manual'),
                        ('cf_problem:101:C', 'algorithm/dp', 'primary', 'div2', 'manual')
                    """
                )

                duplicates = mark_division_duplicates(conn)
                self.assertEqual(len(duplicates), 1)
                self.assertEqual(canonical_problem_uid(conn, "cf_problem:101:C"), "cf_problem:100:A")
                results = search_problems(conn, tags=["algorithm/dp"])
                self.assertEqual([item["problem_uid"] for item in results], ["cf_problem:100:A"])

    def test_reviewed_payload_redirects_duplicate_to_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            payload = self.reviewed_payload()
            payload["contest"] = {"contest_id": 101, "title": "Codeforces Round 50 (Div. 2)"}
            payload["problem"]["contest_id"] = 101
            payload["problem"]["index"] = "C"
            payload["problem"]["title"] = "Shared Problem"

            with connect(db) as conn:
                conn.execute(
                    """
                    INSERT INTO contests(contest_id, contest_uid, title, start_time_seconds, eligibility_status, extraction_status)
                    VALUES
                        (100, 'cf_contest:100', 'Codeforces Round 50 (Div. 1)', 12345, 'eligible', 'problems_loaded'),
                        (101, 'cf_contest:101', 'Codeforces Round 50 (Div. 2)', 12345, 'eligible', 'problems_loaded')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problems(
                        problem_uid, contest_id, problem_index, title, rating, rating_status,
                        canonical_url, problemset_url
                    )
                    VALUES
                        ('cf_problem:100:A', 100, 'A', 'Shared Problem', 1900, 'official',
                         'https://codeforces.com/contest/100/problem/A',
                         'https://codeforces.com/problemset/problem/100/A'),
                        ('cf_problem:101:C', 101, 'C', 'Shared Problem', 1900, 'official',
                         'https://codeforces.com/contest/101/problem/C',
                         'https://codeforces.com/problemset/problem/101/C')
                    """
                )
                mark_division_duplicates(conn)
                problem_uid = apply_reviewed_payload(conn, payload)
                self.assertEqual(problem_uid, "cf_problem:100:A")
                annotation = conn.execute(
                    "SELECT review_status FROM problem_annotations WHERE problem_uid = ?",
                    ("cf_problem:100:A",),
                ).fetchone()
                self.assertEqual(annotation["review_status"], "reviewed")


if __name__ == "__main__":
    unittest.main()
