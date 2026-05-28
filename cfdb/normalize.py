from __future__ import annotations

import re
from dataclasses import dataclass


CONTEST_URL_RE = re.compile(
    r"codeforces\.com/(?:contest|gym)/(?P<contest_id>\d+)/problem/(?P<index>[A-Za-z0-9]+)"
)
PROBLEMSET_URL_RE = re.compile(
    r"codeforces\.com/problemset/problem/(?P<contest_id>\d+)/(?P<index>[A-Za-z0-9]+)"
)


@dataclass(frozen=True)
class ProblemKey:
    contest_id: int
    index: str

    @property
    def contest_uid(self) -> str:
        return f"cf_contest:{self.contest_id}"

    @property
    def problem_uid(self) -> str:
        return f"cf_problem:{self.contest_id}:{self.index}"

    @property
    def canonical_url(self) -> str:
        return f"https://codeforces.com/contest/{self.contest_id}/problem/{self.index}"

    @property
    def problemset_url(self) -> str:
        return f"https://codeforces.com/problemset/problem/{self.contest_id}/{self.index}"


def normalize_problem_key(contest_id: int | str, index: str) -> ProblemKey:
    idx = str(index).strip().upper()
    if not idx:
        raise ValueError("problem index must not be empty")
    return ProblemKey(int(contest_id), idx)


def parse_problem_ref(value: str) -> ProblemKey:
    text = value.strip()
    for pattern in (CONTEST_URL_RE, PROBLEMSET_URL_RE):
        match = pattern.search(text)
        if match:
            return normalize_problem_key(match.group("contest_id"), match.group("index"))

    compact = re.fullmatch(r"(?P<contest_id>\d+)[/_:-]?(?P<index>[A-Za-z][A-Za-z0-9]*)", text)
    if compact:
        return normalize_problem_key(compact.group("contest_id"), compact.group("index"))

    raise ValueError(f"cannot parse Codeforces problem reference: {value!r}")


def contest_uid(contest_id: int | str) -> str:
    return f"cf_contest:{int(contest_id)}"

