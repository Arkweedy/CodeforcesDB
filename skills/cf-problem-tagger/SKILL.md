---
name: cf-problem-tagger
description: Use when a Codex agent must AI-review Codeforces problems for this repository: read statements, inspect editorials or common solution sources, reason about the solution, assign fine-grained hierarchical algorithm/trick tags, and write reviewed JSON into the local SQLite database.
metadata:
  short-description: AI-review Codeforces problems and tag them
---

# CF Problem Tagger

This skill is the primary workflow for adding high-quality Codeforces problem tags to this repository. It is not a scraper. The agent must analyze each problem before writing reviewed data.

## Operating Model

- The user or an automation wakes Codex with a contest/problem range.
- Use repository scripts only for deterministic work: listing pending problems, generating templates, validating JSON, applying JSON, and committing database changes.
- Do the intelligence in the conversation: read the statement, check editorials or common solution sources, reason through the core idea, then decide tags.
- The old API ingestion script is only metadata/bootstrap. Official Codeforces tags are candidate clues, never a reviewed result by themselves.

## Required Per-Problem Review

For every reviewed problem:

1. Normalize identity by `contest_id + index`; URL is never identity.
2. Check whether the problem is a Div.1/Div.2 overlap alias. If the same round has both Div.1 and Div.2 entries, and the problem title appears in both, the Div.1 entry is canonical. Treat the Div.2 entry only as an alias/source.
3. Read the statement and constraints.
4. Check normal solution sources when available: Codeforces editorial, Luogu, reliable blogs, accepted code, or your own derivation.
5. Write the decisive idea, not just a vague category.
6. Record materially different solution variants.
7. Assign tags with importance:
   - `primary`: essential to the main solution.
   - `secondary`: important supporting technique.
   - `incidental`: implementation detail that should not match default search.
8. Every `primary` tag must have evidence.
9. Apply the reviewed JSON with repository scripts and verify search results.

If sources are missing or the solution is inferred, lower `confidence` and say so in source notes.

Templates may include `reference_candidates`, including Luogu solution pages such as `https://www.luogu.com.cn/problem/solution/CF2231F`. Treat these as suggestions only: move a candidate into `sources` only after actually consulting it.

## Div.1 / Div.2 Overlap Rule

Some Codeforces rounds have simultaneous Div.1 and Div.2 contests with shared problems, for example Div.1 A equals Div.2 C/D. These must not appear as separate searchable problems.

- If both Div.1 and Div.2 contain the same problem title in the same round/start time, the Div.1 problem is canonical.
- The Div.2 problem remains only as an alias/source URL.
- Do not create a separate reviewed result for the Div.2 alias.
- If a user asks to review the Div.2 entry, resolve it to the Div.1 canonical problem before writing tags.
- Store or preserve Div.2 URLs as alias sources so either URL can still be traced back.

## Tag Rules

Prefer existing tags or aliases. Create a new tag only when it improves future retrieval and is not a one-off statement detail.

New tags must include:

- `description`: definition and usage boundary.
- `parent` or `parents`: where it fits in the hierarchy.
- `created_reason`: why existing tags are insufficient.
- `status`: usually `candidate`.

When creating a new tag, also keep the WebUI translation in sync. Add a Chinese display name in `web/src/i18n.ts`, or run `python scripts/check_tag_translations.py` and explicitly record that the fallback display is acceptable for now.

Good examples:

- `dp/digit-dp`
- `string/acam`
- `math/transform/fwt`
- `data-structure/monotonic-stack`
- `math/inclusion-exclusion/minmax`
- `trick/maintain-contribution`

Bad examples:

- `trick/put-largest-at-position-three`
- `trick/red-blue-array-from-sample`
- `algorithm/use-vector-and-sort`

## Repository Commands

List pending AI reviews:

```powershell
python scripts/list_pending_reviews.py --limit 20
```

Generate a reviewed JSON template:

```powershell
python scripts/make_review_template.py 2170E --out reviews/2170E.json
```

Apply one reviewed problem:

```powershell
python scripts/apply_reviewed_problem.py reviews/2170E.json
```

Apply a batch and auto-commit the database:

```powershell
python scripts/apply_review_batch.py reviews/
```

Validate searches:

```powershell
python scripts/search.py --tag dp --tag paradigm/greedy --show-tags
```

## Reviewed JSON Shape

```json
{
  "contest": {
    "contest_id": 2170,
    "title": "Educational Codeforces Round 185 (Rated for Div. 2)"
  },
  "problem": {
    "contest_id": 2170,
    "index": "E",
    "title": "Binary Strings and Blocks",
    "rating": 2100,
    "rating_status": "official",
    "official_tags": ["dp", "combinatorics"]
  },
  "sources": [
    {
      "source_type": "statement",
      "url": "https://codeforces.com/contest/2170/problem/E",
      "notes": "Statement and constraints."
    },
    {
      "source_type": "editorial",
      "url": "https://codeforces.com/blog/entry/...",
      "notes": "Used to confirm the main solution."
    },
    {
      "source_type": "luogu_solution",
      "url": "https://www.luogu.com.cn/problem/solution/CF2170E",
      "notes": "Used as an additional solution-source cross-check."
    }
  ],
  "reference_candidates": [
    {
      "source_type": "luogu_solution",
      "url": "https://www.luogu.com.cn/problem/solution/CF2170E",
      "notes": "Candidate source; move into sources only if consulted."
    }
  ],
  "annotation": {
    "summary": "Short problem summary.",
    "constraints": "Key constraints that determine complexity.",
    "core_idea": "Core reduction, observation, construction, or invariant.",
    "complexity": "O(...)",
    "tricks": ["Key trick"],
    "confidence": "high",
    "review_status": "reviewed"
  },
  "solution_variants": [
    {
      "name": "main",
      "summary": "Main solution.",
      "complexity": "O(...)",
      "confidence": "high",
      "is_primary": true
    }
  ],
  "tags": [
    {
      "tag": "dp",
      "importance": "primary",
      "evidence": "The state design and transition are the core of the solution.",
      "solution_variant": "main"
    }
  ]
}
```

## Quality Bar

- Do not mark a problem `reviewed` if it only has official tags.
- Do not save large copied editorials; store URLs and short notes.
- Do not invent official rating. If Codeforces has no rating, use `pending_cf_rating`, `no_cf_rating`, or `unknown`.
- Official rating below 1400 is out of scope unless the user explicitly changes policy.
- After a batch, commit the database with a message naming the reviewed problem range and count.
