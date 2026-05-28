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
2. Read the statement and constraints.
3. Check normal solution sources when available: Codeforces editorial, Luogu, reliable blogs, accepted code, or your own derivation.
4. Write the decisive idea, not just a vague category.
5. Record materially different solution variants.
6. Assign tags with importance:
   - `primary`: essential to the main solution.
   - `secondary`: important supporting technique.
   - `incidental`: implementation detail that should not match default search.
7. Every `primary` tag must have evidence.
8. Apply the reviewed JSON with repository scripts and verify search results.

If sources are missing or the solution is inferred, lower `confidence` and say so in source notes.

## Tag Rules

Prefer existing tags or aliases. Create a new tag only when it improves future retrieval and is not a one-off statement detail.

New tags must include:

- `description`: definition and usage boundary.
- `parent` or `parents`: where it fits in the hierarchy.
- `created_reason`: why existing tags are insufficient.
- `status`: usually `candidate`.

Good examples:

- `algorithm/dp/digit-dp`
- `algorithm/string/acam`
- `algorithm/transform/fwt`
- `data-structure/monotonic-stack`
- `math/inclusion-exclusion/minmax`
- `trick/maintain-contribution`

Bad examples:

- `trick/put-largest-at-position-three`
- `topic/red-blue-array-from-sample`
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
python scripts/search.py --tag algorithm/dp --tag paradigm/greedy --show-tags
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
      "tag": "algorithm/dp",
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
