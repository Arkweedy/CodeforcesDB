from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cfdb.db import connect, init_db
from cfdb.dedup import canonical_problem_uid, duplicate_alias_count, mark_division_duplicates
from cfdb.eligibility import classify_contest
from cfdb.ingest import ingest_contest, upsert_ingestion_range
from cfdb.normalize import parse_problem_ref
from cfdb.reviewed import ReviewedPayloadError, apply_reviewed_payload
from cfdb.search import search_problems
from cfdb.tags import descendants, resolve_tag
from scripts.check_tag_translations import extract_full_tag_translations, missing_translations
from scripts.list_missing_contests import contest_status_rows
from scripts.make_review_template import build_template


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
                self.assertEqual(resolve_tag(conn, "acam"), "string/acam")
                self.assertIn("dp/digit-dp", descendants(conn, "dp"))

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
                        ('cf_problem:1:A', 'string/acam', 'primary', 'synthetic', 'manual'),
                        ('cf_problem:1:A', 'dp/automaton-dp', 'primary', 'synthetic', 'manual')
                    """
                )
                results = search_problems(conn, tags=["acam", "dp"])
                self.assertEqual([item["problem_uid"] for item in results], ["cf_problem:1:A"])

    def test_or_tag_search_and_favorite_filter(self) -> None:
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
                    VALUES
                        ('cf_problem:1:A', 1, 'A', 'DP Only', 1800, 'official',
                         'https://codeforces.com/contest/1/problem/A',
                         'https://codeforces.com/problemset/problem/1/A'),
                        ('cf_problem:1:B', 1, 'B', 'Geometry Only', 1900, 'official',
                         'https://codeforces.com/contest/1/problem/B',
                         'https://codeforces.com/problemset/problem/1/B')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problem_tags(problem_uid, tag, importance, evidence, source)
                    VALUES
                        ('cf_problem:1:A', 'dp', 'primary', 'synthetic', 'manual'),
                        ('cf_problem:1:B', 'math/geometry', 'primary', 'synthetic', 'manual')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problem_user_state(problem_uid, favorite, note)
                    VALUES ('cf_problem:1:B', 1, 'remember this')
                    """
                )
                results = search_problems(
                    conn,
                    tags=["dp", "math/geometry"],
                    tag_mode="or",
                )
                self.assertEqual(
                    [item["problem_uid"] for item in results],
                    ["cf_problem:1:A", "cf_problem:1:B"],
                )
                favorite_results = search_problems(conn, tag_mode="or", favorite_only=True)
                self.assertEqual([item["problem_uid"] for item in favorite_results], ["cf_problem:1:B"])

    def test_search_omits_excluded_contests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            with connect(db) as conn:
                conn.execute(
                    """
                    INSERT INTO contests(contest_id, contest_uid, title, eligibility_status, extraction_status)
                    VALUES
                        (1, 'cf_contest:1', 'Eligible Contest', 'eligible', 'problems_loaded'),
                        (2, 'cf_contest:2', 'Excluded Contest', 'excluded', 'excluded')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problems(
                        problem_uid, contest_id, problem_index, title, rating, rating_status,
                        canonical_url, problemset_url
                    )
                    VALUES
                        ('cf_problem:1:A', 1, 'A', 'Visible DP', 1800, 'official',
                         'https://codeforces.com/contest/1/problem/A',
                         'https://codeforces.com/problemset/problem/1/A'),
                        ('cf_problem:2:A', 2, 'A', 'Hidden DP', 1800, 'official',
                         'https://codeforces.com/contest/2/problem/A',
                         'https://codeforces.com/problemset/problem/2/A')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problem_tags(problem_uid, tag, importance, evidence, source)
                    VALUES
                        ('cf_problem:1:A', 'dp', 'primary', 'synthetic', 'manual'),
                        ('cf_problem:2:A', 'dp', 'primary', 'synthetic', 'manual')
                    """
                )

                results = search_problems(conn, tags=["dp"])
                self.assertEqual([item["problem_uid"] for item in results], ["cf_problem:1:A"])

    def test_ingest_falls_back_to_problemset_when_standings_fails(self) -> None:
        class FakeClient:
            def contest_standings(self, contest_id: int) -> dict[str, object]:
                raise RuntimeError("standings response failed")

            def problemset_problems(self) -> dict[str, object]:
                return {
                    "problems": [
                        {
                            "contestId": 77,
                            "index": "B",
                            "name": "Keep Me",
                            "rating": 1800,
                            "tags": ["dp"],
                        },
                        {
                            "contestId": 78,
                            "index": "A",
                            "name": "Other Contest",
                            "rating": 1800,
                            "tags": ["math"],
                        },
                    ]
                }

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            with connect(db) as conn:
                upsert_ingestion_range(conn, 77, 77)
                result = ingest_contest(
                    conn,
                    FakeClient(),  # type: ignore[arg-type]
                    77,
                    {
                        "id": 77,
                        "name": "Codeforces Round 77 (Div. 3)",
                        "phase": "FINISHED",
                        "type": "ICPC",
                        "startTimeSeconds": 1700000000,
                        "durationSeconds": 7200,
                    },
                )
                self.assertEqual(result, {"contest_id": 77, "status": "done", "problems": 1})
                problem = conn.execute(
                    "SELECT title, rating, rating_status FROM problems WHERE problem_uid = 'cf_problem:77:B'"
                ).fetchone()
                self.assertEqual(dict(problem), {"title": "Keep Me", "rating": 1800, "rating_status": "official"})

    def test_ioi_rules_contest_is_excluded(self) -> None:
        eligibility = classify_contest(
            "XIX Open Olympiad in Informatics - Final Stage, Day 1 (Unrated, Online Mirror, IOI rules)"
        )
        self.assertEqual(eligibility.status, "excluded")
        self.assertIn("IOI-style", eligibility.reason or "")

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
                    "tag": "dp",
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
                results = search_problems(conn, rating_min=1800, rating_max=1800, tags=["dp"])
                self.assertEqual([item["problem_uid"] for item in results], [problem_uid])

    def test_reviewed_payload_replaces_bootstrap_official_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            payload = self.reviewed_payload()
            with connect(db) as conn:
                conn.execute(
                    """
                    INSERT INTO contests(contest_id, contest_uid, title, eligibility_status, extraction_status)
                    VALUES (2, 'cf_contest:2', 'Synthetic Contest', 'eligible', 'problems_loaded')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problems(
                        problem_uid, contest_id, problem_index, title, rating, rating_status,
                        canonical_url, problemset_url
                    )
                    VALUES (
                        'cf_problem:2:B', 2, 'B', 'Bootstrap Tags', 1800, 'official',
                        'https://codeforces.com/contest/2/problem/B',
                        'https://codeforces.com/problemset/problem/2/B'
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problem_tags(problem_uid, tag, importance, evidence, source)
                    VALUES
                        ('cf_problem:2:B', 'graph/tree', 'secondary', 'Codeforces official tag: trees.', 'cf_official'),
                        ('cf_problem:2:B', 'algorithm/search/binary-search', 'secondary', 'Codeforces official tag: binary search.', 'cf_official')
                    """
                )

                problem_uid = apply_reviewed_payload(conn, payload)
                rows = conn.execute(
                    "SELECT tag, source FROM problem_tags WHERE problem_uid = ? ORDER BY tag",
                    (problem_uid,),
                ).fetchall()
                self.assertEqual([(row["tag"], row["source"]) for row in rows], [("dp", "ai_reviewed")])
                self.assertEqual(search_problems(conn, tags=["graph/tree"]), [])

    def test_excluded_payload_does_not_require_tags_or_appear_in_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            payload = self.reviewed_payload()
            payload["problem"]["index"] = "G"
            payload["problem"]["title"] = "Output Only"
            payload["annotation"]["review_status"] = "excluded"
            payload["annotation"]["summary"] = "Non-standard fixed-output problem."
            payload["annotation"]["core_idea"] = "Excluded from the ICPC-style searchable set."
            payload["solution_variants"] = []
            payload["tags"] = []
            with connect(db) as conn:
                problem_uid = apply_reviewed_payload(conn, payload)
                annotation = conn.execute(
                    "SELECT review_status FROM problem_annotations WHERE problem_uid = ?",
                    (problem_uid,),
                ).fetchone()
                self.assertEqual(annotation["review_status"], "excluded")
                results = search_problems(conn, rating_min=1800, rating_max=1800)
                self.assertEqual(results, [])

    def test_review_template_includes_luogu_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            with connect(db) as conn:
                conn.execute(
                    """
                    INSERT INTO contests(contest_id, contest_uid, title, eligibility_status, extraction_status)
                    VALUES (2170, 'cf_contest:2170', 'Synthetic Contest', 'eligible', 'problems_loaded')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problems(
                        problem_uid, contest_id, problem_index, title, rating, rating_status,
                        canonical_url, problemset_url, official_tags_json
                    )
                    VALUES (
                        'cf_problem:2170:E', 2170, 'E', 'Template Problem', 2100, 'official',
                        'https://codeforces.com/contest/2170/problem/E',
                        'https://codeforces.com/problemset/problem/2170/E',
                        '["dp"]'
                    )
                    """
                )

            template = build_template(str(db), "2170E")
            candidates = template["reference_candidates"]
            self.assertEqual(candidates[0]["source_type"], "luogu_solution")
            self.assertEqual(
                candidates[0]["url"],
                "https://www.luogu.com.cn/problem/solution/CF2170E",
            )

    def test_reviewed_payload_accepts_luogu_solution_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            payload = self.reviewed_payload()
            payload["sources"].append(
                {
                    "source_type": "luogu_solution",
                    "url": "https://www.luogu.com.cn/problem/solution/CF2B",
                    "notes": "Used as an additional solution cross-check.",
                }
            )
            with connect(db) as conn:
                problem_uid = apply_reviewed_payload(conn, payload)
                row = conn.execute(
                    """
                    SELECT notes
                    FROM problem_sources
                    WHERE problem_uid = ? AND source_type = 'luogu_solution'
                    """,
                    (problem_uid,),
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertIn("cross-check", row["notes"])

    def test_tag_translation_checker_reports_missing_full_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            i18n = Path(tmp) / "i18n.ts"
            i18n.write_text(
                'const FULL_TAG_TEXT_ZH: Record<string, string> = {\n'
                '  "algorithm": "算法",\n'
                '  "dp": "动态规划"\n'
                "};\n",
                encoding="utf-8",
            )
            translated = extract_full_tag_translations(i18n)
            self.assertEqual(translated, {"algorithm", "dp"})
            self.assertEqual(
                missing_translations(["algorithm", "dp", "trick/new"], translated),
                ["trick/new"],
            )

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
                        ('cf_problem:100:A', 'dp', 'primary', 'div1', 'manual'),
                        ('cf_problem:101:C', 'dp', 'primary', 'div2', 'manual')
                    """
                )

                duplicates = mark_division_duplicates(conn)
                self.assertEqual(len(duplicates), 1)
                self.assertEqual(duplicate_alias_count(duplicates, 101, 101), 1)
                self.assertEqual(duplicate_alias_count(duplicates, 102, 110), 0)
                self.assertEqual(duplicate_alias_count(duplicates, 101, 100), 1)
                self.assertEqual(canonical_problem_uid(conn, "cf_problem:101:C"), "cf_problem:100:A")
                results = search_problems(conn, tags=["dp"])
                self.assertEqual([item["problem_uid"] for item in results], ["cf_problem:100:A"])

    def test_div1_div2_overlap_moves_reviewed_alias_to_div1(self) -> None:
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
                    INSERT INTO problem_annotations(problem_uid, summary, constraints_text, core_idea, complexity, confidence, review_status)
                    VALUES
                        ('cf_problem:100:A', 'raw', 'raw', 'raw', 'raw', 'low', 'auto_seeded'),
                        ('cf_problem:101:C', 'reviewed summary', 'constraints', 'core idea', 'O(n)', 'high', 'reviewed')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO solution_variants(problem_uid, variant_name, summary, complexity, confidence, is_primary)
                    VALUES ('cf_problem:101:C', 'main', 'variant summary', 'O(n)', 'high', 1)
                    """
                )
                variant_id = conn.execute(
                    """
                    SELECT id FROM solution_variants
                    WHERE problem_uid = 'cf_problem:101:C' AND variant_name = 'main'
                    """
                ).fetchone()["id"]
                conn.execute(
                    """
                    INSERT INTO problem_tags(problem_uid, tag, importance, evidence, source, solution_variant_id)
                    VALUES
                        ('cf_problem:100:A', 'math', 'primary', 'official clue', 'cf_official', NULL),
                        ('cf_problem:101:C', 'dp', 'primary', 'reviewed evidence', 'ai_reviewed', ?)
                    """,
                    (variant_id,),
                )

                duplicates = mark_division_duplicates(conn)
                self.assertEqual(len(duplicates), 1)
                self.assertEqual(canonical_problem_uid(conn, "cf_problem:101:C"), "cf_problem:100:A")

                annotation = conn.execute(
                    """
                    SELECT summary, review_status
                    FROM problem_annotations
                    WHERE problem_uid = 'cf_problem:100:A'
                    """
                ).fetchone()
                self.assertEqual(annotation["summary"], "reviewed summary")
                self.assertEqual(annotation["review_status"], "reviewed")

                canonical_tag = conn.execute(
                    """
                    SELECT pt.tag, pt.evidence, pt.source, sv.variant_name
                    FROM problem_tags pt
                    LEFT JOIN solution_variants sv ON sv.id = pt.solution_variant_id
                    WHERE pt.problem_uid = 'cf_problem:100:A'
                    """
                ).fetchone()
                self.assertEqual(canonical_tag["tag"], "dp")
                self.assertEqual(canonical_tag["evidence"], "reviewed evidence")
                self.assertEqual(canonical_tag["source"], "ai_reviewed")
                self.assertEqual(canonical_tag["variant_name"], "main")

                alias_counts = conn.execute(
                    """
                    SELECT
                        (SELECT COUNT(*) FROM problem_annotations WHERE problem_uid = 'cf_problem:101:C') AS annotations,
                        (SELECT COUNT(*) FROM solution_variants WHERE problem_uid = 'cf_problem:101:C') AS variants,
                        (SELECT COUNT(*) FROM problem_tags WHERE problem_uid = 'cf_problem:101:C') AS tags
                    """
                ).fetchone()
                self.assertEqual(dict(alias_counts), {"annotations": 0, "variants": 0, "tags": 0})

    def test_list_missing_contests_reports_coverage_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            with connect(db) as conn:
                conn.execute(
                    """
                    INSERT INTO contests(contest_id, contest_uid, title, eligibility_status, extraction_status)
                    VALUES
                        (10, 'cf_contest:10', 'Needs Review', 'eligible', 'problems_loaded'),
                        (11, 'cf_contest:11', 'Queued Contest', 'eligible', 'queued'),
                        (12, 'cf_contest:12', 'Excluded Contest', 'excluded', 'excluded'),
                        (14, 'cf_contest:14', 'Complete Contest', 'eligible', 'problems_loaded'),
                        (15, 'cf_contest:15', 'Manual Check', 'needs_manual_review', 'metadata_loaded'),
                        (16, 'cf_contest:16', 'Failed Contest', 'eligible', 'failed')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO ingestion_queue(contest_id, status)
                    VALUES (11, 'queued'), (16, 'failed')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problems(
                        problem_uid, contest_id, problem_index, title, rating, rating_status,
                        canonical_url, problemset_url
                    )
                    VALUES
                        ('cf_problem:10:A', 10, 'A', 'Reviewed', 1500, 'official',
                         'https://codeforces.com/contest/10/problem/A',
                         'https://codeforces.com/problemset/problem/10/A'),
                        ('cf_problem:10:B', 10, 'B', 'Pending', 1600, 'official',
                         'https://codeforces.com/contest/10/problem/B',
                         'https://codeforces.com/problemset/problem/10/B'),
                        ('cf_problem:10:C', 10, 'C', 'Too Easy', 1300, 'official',
                         'https://codeforces.com/contest/10/problem/C',
                         'https://codeforces.com/problemset/problem/10/C'),
                        ('cf_problem:10:D', 10, 'D', 'Excluded', 1700, 'official',
                         'https://codeforces.com/contest/10/problem/D',
                         'https://codeforces.com/problemset/problem/10/D'),
                        ('cf_problem:14:A', 14, 'A', 'Done', 1800, 'official',
                         'https://codeforces.com/contest/14/problem/A',
                         'https://codeforces.com/problemset/problem/14/A')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO problem_annotations(problem_uid, review_status)
                    VALUES
                        ('cf_problem:10:A', 'reviewed'),
                        ('cf_problem:10:B', 'auto_seeded'),
                        ('cf_problem:10:C', 'auto_seeded'),
                        ('cf_problem:10:D', 'excluded'),
                        ('cf_problem:14:A', 'reviewed')
                    """
                )

            rows = {row["contest_id"]: row for row in contest_status_rows(db, 10, 16)}
            self.assertEqual(rows[10]["status"], "pending_review")
            self.assertEqual(rows[10]["tracked_problems"], 4)
            self.assertEqual(rows[10]["reviewed_problems"], 1)
            self.assertEqual(rows[10]["pending_review"], 1)
            self.assertEqual(rows[11]["status"], "unextracted")
            self.assertEqual(rows[12]["status"], "excluded")
            self.assertEqual(rows[13]["status"], "not_in_db")
            self.assertEqual(rows[14]["status"], "complete")
            self.assertEqual(rows[15]["status"], "needs_manual_review")
            self.assertEqual(rows[16]["status"], "failed")

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

    def test_web_api_tags_search_detail_and_user_state(self) -> None:
        from fastapi.testclient import TestClient

        from cfdb.web_app import create_app

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            init_db(db)
            with connect(db) as conn:
                apply_reviewed_payload(conn, self.reviewed_payload())

            client = TestClient(create_app(db))
            tags = client.get("/api/tags")
            self.assertEqual(tags.status_code, 200)
            self.assertTrue(any(item["tag"] == "algorithm" for item in tags.json()))

            search = client.get("/api/search", params={"tags": "dp", "tag_mode": "and"})
            self.assertEqual(search.status_code, 200)
            self.assertEqual(search.json()["items"][0]["problem_uid"], "cf_problem:2:B")

            detail = client.get("/api/problems/cf_problem:2:B")
            self.assertEqual(detail.status_code, 200)
            self.assertEqual(detail.json()["annotation"]["review_status"], "reviewed")

            state = client.patch(
                "/api/problems/cf_problem:2:B/user-state",
                json={"favorite": True, "note": "practice later"},
            )
            self.assertEqual(state.status_code, 200)
            self.assertTrue(state.json()["favorite"])

            favorite = client.get("/api/search", params={"favorite_only": "true"})
            self.assertEqual(favorite.status_code, 200)
            self.assertEqual(favorite.json()["items"][0]["problem_uid"], "cf_problem:2:B")


if __name__ == "__main__":
    unittest.main()
