from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass


ROOT_TAGS = {
    "algorithm": "Algorithm",
    "data-structure": "Data structure",
    "math": "Math",
    "paradigm": "Paradigm",
    "trick": "Trick",
    "implementation": "Implementation",
    "topic": "Topic",
}


OFFICIAL_TAG_MAP = {
    "2-sat": "algorithm/graph/2-sat",
    "binary search": "algorithm/search/binary-search",
    "bitmasks": "algorithm/bitmask",
    "brute force": "paradigm/brute-force",
    "chinese remainder theorem": "math/number-theory/chinese-remainder-theorem",
    "combinatorics": "math/combinatorics",
    "constructive algorithms": "paradigm/constructive",
    "data structures": "data-structure",
    "dfs and similar": "algorithm/graph/dfs",
    "divide and conquer": "algorithm/divide-and-conquer",
    "dp": "algorithm/dp",
    "dsu": "data-structure/dsu",
    "expression parsing": "implementation/parsing/expression",
    "fft": "algorithm/transform/fft",
    "flows": "algorithm/graph/flow",
    "games": "math/game-theory",
    "geometry": "math/geometry",
    "graph matchings": "algorithm/graph/matching",
    "graphs": "algorithm/graph",
    "greedy": "paradigm/greedy",
    "hashing": "algorithm/hashing",
    "implementation": "implementation",
    "interactive": "paradigm/interactive",
    "math": "math",
    "matrices": "math/linear-algebra/matrix",
    "meet-in-the-middle": "algorithm/meet-in-the-middle",
    "number theory": "math/number-theory",
    "probabilities": "math/probability",
    "schedules": "topic/scheduling",
    "shortest paths": "algorithm/graph/shortest-path",
    "sortings": "algorithm/sorting",
    "string suffix structures": "algorithm/string/suffix-structures",
    "strings": "algorithm/string",
    "ternary search": "algorithm/search/ternary-search",
    "trees": "algorithm/graph/tree",
    "two pointers": "algorithm/two-pointers",
}


COMMON_TAGS = {
    "algorithm/transform/fwt": {
        "display_name": "Fast Walsh-Hadamard transform",
        "description": "Subset or XOR/AND/OR convolution transform techniques.",
        "aliases": ["fwt", "fwht", "fast-walsh-transform", "xor-convolution"],
    },
    "algorithm/dp/digit-dp": {
        "display_name": "Digit DP",
        "description": "Dynamic programming over decimal or binary digit prefixes.",
        "aliases": ["digit dp", "digits-dp", "shuwei-dp"],
    },
    "algorithm/string/acam": {
        "display_name": "Aho-Corasick automaton",
        "description": "Multi-pattern string automaton, often combined with DP or graph transitions.",
        "aliases": ["acam", "ac automaton", "aho-corasick", "aho-corasick-automaton"],
    },
    "algorithm/dp/automaton-dp": {
        "display_name": "Automaton DP",
        "description": "Dynamic programming whose states include an automaton state.",
        "aliases": ["automaton dp", "dfa dp"],
    },
    "data-structure/monotonic-stack": {
        "display_name": "Monotonic stack",
        "description": "Stack that maintains monotonic order to find nearest greater/smaller elements or contribution ranges.",
        "aliases": ["monostack", "monotone stack"],
    },
    "math/inclusion-exclusion": {
        "display_name": "Inclusion-exclusion",
        "description": "Counting by adding and subtracting overlapping constraints.",
        "aliases": ["inclusion exclusion", "ie"],
    },
    "math/inclusion-exclusion/minmax": {
        "display_name": "Min-max inclusion-exclusion",
        "description": "Inclusion-exclusion identities involving minima, maxima, OR, AND, gcd, or lcm style aggregations.",
        "aliases": ["minmax inclusion exclusion", "min-max inclusion-exclusion"],
    },
    "trick/maintain-contribution": {
        "display_name": "Maintain contribution",
        "description": "Solve by maintaining each element/event contribution under updates or traversal.",
        "aliases": ["contribution maintenance"],
    },
}


@dataclass(frozen=True)
class TagInput:
    tag: str
    display_name: str | None = None
    description: str | None = None
    status: str = "candidate"
    created_from_problem: str | None = None
    created_reason: str | None = None


def slugify_tag(value: str) -> str:
    text = value.strip().lower()
    text = text.replace("_", "-")
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9/\-]+", "", text)
    text = re.sub(r"-+", "-", text)
    text = re.sub(r"/+", "/", text)
    return text.strip("-/")


def map_official_tag(value: str) -> str:
    return OFFICIAL_TAG_MAP.get(value.strip().lower(), slugify_tag(value))


def ensure_tag(conn: sqlite3.Connection, tag_input: TagInput | str) -> str:
    if isinstance(tag_input, str):
        item = TagInput(slugify_tag(tag_input))
    else:
        item = tag_input

    tag = slugify_tag(item.tag)
    if not tag:
        raise ValueError("tag must not be empty")

    parts = tag.split("/")
    prefixes = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]

    for prefix in prefixes:
        status = "active" if prefix in ROOT_TAGS or prefix != tag else item.status
        display_name = ROOT_TAGS.get(prefix)
        if prefix == tag:
            display_name = item.display_name or display_name
        conn.execute(
            """
            INSERT INTO tags(tag, display_name, description, status, created_from_problem, created_reason)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(tag) DO UPDATE SET
                display_name = COALESCE(excluded.display_name, tags.display_name),
                description = COALESCE(excluded.description, tags.description),
                status = CASE
                    WHEN tags.status = 'active' THEN tags.status
                    ELSE excluded.status
                END,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                prefix,
                display_name,
                item.description if prefix == tag else None,
                status,
                item.created_from_problem if prefix == tag else None,
                item.created_reason if prefix == tag else None,
            ),
        )

    for parent, child in zip(prefixes, prefixes[1:]):
        conn.execute(
            "INSERT OR IGNORE INTO tag_edges(parent_tag, child_tag) VALUES (?, ?)",
            (parent, child),
        )

    return tag


def add_alias(conn: sqlite3.Connection, alias: str, tag: str) -> None:
    canonical = ensure_tag(conn, tag)
    conn.execute(
        """
        INSERT INTO tag_aliases(alias, tag) VALUES (?, ?)
        ON CONFLICT(alias) DO UPDATE SET tag = excluded.tag
        """,
        (slugify_tag(alias), canonical),
    )


def resolve_tag(conn: sqlite3.Connection, value: str) -> str:
    candidate = slugify_tag(value)
    row = conn.execute("SELECT tag FROM tags WHERE tag = ?", (candidate,)).fetchone()
    if row:
        return row["tag"]

    row = conn.execute("SELECT tag FROM tag_aliases WHERE alias = ?", (candidate,)).fetchone()
    if row:
        return row["tag"]

    official = map_official_tag(value)
    row = conn.execute("SELECT tag FROM tags WHERE tag = ?", (official,)).fetchone()
    if row:
        return row["tag"]

    row = conn.execute("SELECT tag FROM tag_aliases WHERE alias = ?", (slugify_tag(official),)).fetchone()
    if row:
        return row["tag"]

    raise KeyError(f"unknown tag or alias: {value}")


def descendants(conn: sqlite3.Connection, tag: str) -> list[str]:
    canonical = resolve_tag(conn, tag)
    rows = conn.execute(
        """
        WITH RECURSIVE tag_tree(tag) AS (
            SELECT ?
            UNION
            SELECT child_tag
            FROM tag_edges
            JOIN tag_tree ON tag_edges.parent_tag = tag_tree.tag
        )
        SELECT tag FROM tag_tree
        """,
        (canonical,),
    ).fetchall()
    return [row["tag"] for row in rows]


def seed_tags(conn: sqlite3.Connection) -> None:
    for root, display_name in ROOT_TAGS.items():
        ensure_tag(conn, TagInput(root, display_name=display_name, status="active"))

    for official, tag in OFFICIAL_TAG_MAP.items():
        ensure_tag(
            conn,
            TagInput(
                tag,
                display_name=tag.split("/")[-1].replace("-", " ").title(),
                description=f"Mapped from Codeforces official tag: {official}.",
                status="active",
            ),
        )
        add_alias(conn, official, tag)

    for tag, meta in COMMON_TAGS.items():
        ensure_tag(
            conn,
            TagInput(
                tag,
                display_name=meta.get("display_name"),
                description=meta.get("description"),
                status="active",
            ),
        )
        for alias in meta.get("aliases", []):
            add_alias(conn, alias, tag)

