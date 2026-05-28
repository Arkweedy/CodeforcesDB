---
name: cf-problem-tagger
description: Use when adding reviewed Codeforces problem annotations to this SQLite database, deciding hierarchical algorithm/trick tags, or proposing new candidate tags for competitive programming problems.
---

# CF Problem Tagger

Use this workflow to turn one Codeforces problem into a reviewed database annotation.

## Inputs

- Problem reference: `contestId+index` or either Codeforces URL form.
- Available sources: statement, Codeforces editorial, Luogu/editorial blogs, accepted code, or self-derived solution.
- Local database initialized by `scripts/init_db.py`.

## Workflow

1. Normalize the problem key with `contest_id + index`; never use URL as identity.
2. Read the statement constraints and identify the target complexity.
3. Compare at least one reliable solution source with your own reasoning.
4. Write a concise annotation:
   - `summary`: what the problem asks.
   - `core_idea`: the decisive reduction, observation, construction, or invariant.
   - `complexity`: time and memory.
   - `confidence`: `low`, `medium`, or `high`.
5. Add solution variants when there are materially different accepted approaches.
6. Assign tags with importance:
   - `primary`: necessary to explain the main solution.
   - `secondary`: important support technique or data structure.
   - `incidental`: appears in implementation but should not match default searches.
7. Apply the annotation with `python scripts/tag_problem.py path/to/annotation.json`.
8. Verify expected searches with `python scripts/search.py`.

## New Tag Criteria

Prefer an existing tag or alias. Create a new tag only when all are true:

- It improves future retrieval in a way existing tags do not.
- It is not a one-off statement detail.
- It has a clear parent, definition, and boundary.
- It is expected to recur across problems, or is a classic algorithm, trick, proof pattern, or paradigm.
- It is not merely a synonym; synonyms must be aliases.
- Every `primary` use has evidence.

New tags start as `candidate` unless the concept is already standard and well-defined.

Good candidate examples:

- `algorithm/dp/digit-dp`
- `algorithm/string/acam`
- `data-structure/monotonic-stack`
- `math/inclusion-exclusion/minmax`
- `trick/maintain-contribution`

Poor candidate examples:

- `trick/put-largest-at-position-three`
- `topic/red-blue-array-from-sample`
- `algorithm/use-vector-and-sort`

## Annotation JSON Shape

```json
{
  "problem": "2170E",
  "annotation": {
    "summary": "Short statement summary.",
    "core_idea": "Main reduction or observation.",
    "complexity": "O(n log n)",
    "confidence": "high",
    "review_status": "reviewed"
  },
  "solution_variants": [
    {
      "name": "main",
      "summary": "Main solution idea.",
      "complexity": "O(n log n)",
      "confidence": "high",
      "is_primary": true
    }
  ],
  "tags": [
    {
      "tag": "algorithm/dp",
      "importance": "primary",
      "evidence": "The state transition is the core of the solution.",
      "source": "manual",
      "solution_variant": "main"
    }
  ]
}
```

## Quality Bar

- Do not rely only on Codeforces official tags for reviewed annotations.
- Do not mark a tag `primary` unless removing it would make the solution explanation misleading.
- If a data structure can be replaced by a simpler container without changing the idea, mark it `incidental` or omit it.
- If a problem has no official rating, do not invent `rating`; use only annotation fields.
- After tagging, run at least one coarse query and one specific query that should include the problem.
