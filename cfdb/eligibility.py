from __future__ import annotations

from dataclasses import dataclass


EXCLUDED_PATTERNS = [
    ("kotlin heroes", "language-limited contest"),
    ("april fools", "joke contest"),
    ("marathon", "marathon or optimization contest"),
    ("huawei", "heuristic or optimization challenge"),
    ("challenge", "challenge or optimization style contest"),
    ("winter challenge", "challenge or optimization style contest"),
    ("ioi rules", "IOI-style contest with subtask scoring"),
    ("tact smart battle", "platform-specific smart contract contest"),
    ("ознакомительный", "familiarization or practice round"),
]

MANUAL_REVIEW_PATTERNS = [
    ("experimental", "special contest needs manual review"),
    ("testing round", "special contest needs manual review"),
    ("unknown language", "special contest needs manual review"),
]


@dataclass(frozen=True)
class Eligibility:
    status: str
    reason: str | None


def classify_contest(name: str, cf_type: str | None = None, manual_override: str | None = None) -> Eligibility:
    if manual_override == "manual_include":
        return Eligibility("eligible", "manual include")
    if manual_override == "manual_exclude":
        return Eligibility("excluded", "manual exclude")

    lower = name.lower()
    for pattern, reason in EXCLUDED_PATTERNS:
        if pattern in lower:
            return Eligibility("excluded", reason)

    for pattern, reason in MANUAL_REVIEW_PATTERNS:
        if pattern in lower:
            return Eligibility("needs_manual_review", reason)

    return Eligibility("eligible", None)
