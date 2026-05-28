from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cfdb.db import connect, init_db
from cfdb.normalize import parse_problem_ref
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


if __name__ == "__main__":
    unittest.main()
