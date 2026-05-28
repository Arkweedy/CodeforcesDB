# Codeforces AI-Reviewed 题目数据库

这是一个本地 SQLite 题目数据库，用来按 rating、算法、数据结构、题型、trick 等条件快速检索 Codeforces 题目。

**主流程不是自动爬取 tag，而是 AI-reviewed 逐题分析。** Codex agent 需要阅读题面、查常见题解来源、必要时自行推导，再写入 reviewed JSON。脚本只负责校验、写库、查询和提交。

默认数据库：

```text
data/cfdb.sqlite
```

## 主流程：AI-reviewed 标注

1. 列出待 review 题：

```powershell
python scripts/list_pending_reviews.py --limit 20
```

2. 生成单题 reviewed JSON 模板：

```powershell
python scripts/make_review_template.py 2170E --out reviews/2170E.json
```

3. Codex agent 使用 `cf-problem-tagger` skill 分析题目：

- 读题面和约束。
- 查 Codeforces editorial、Luogu、可靠博客或 accepted code。
- 推导核心解法、复杂度和 trick。
- 决定 `primary / secondary / incidental` tag。
- 为每个 `primary` tag 写 evidence。

4. 写入一题：

```powershell
python scripts/apply_reviewed_problem.py reviews/2170E.json
```

5. 批量写入并自动提交数据库：

```powershell
python scripts/apply_review_batch.py reviews/
```

批量提交信息会包含 reviewed 范围和题目数，例如：

```text
review CF problems 2170A-2170F (6 problems)
```

## Skill

仓库内 skill：

```text
skills/cf-problem-tagger/SKILL.md
```

该 skill 也应同步到 Codex 全局 skills 目录：

```text
C:\Users\Arkweedy\.codex\skills\cf-problem-tagger
```

后续你可以通过对话或定时任务唤醒 Codex agent，让它使用 `$cf-problem-tagger` 对指定范围逐题分析并入库。

## Bootstrap：基础元数据抽取

旧脚本 `scripts/ingest_contests.py` 只用于 bootstrap contest/problem 元数据：

```powershell
python scripts/ingest_contests.py --start 2170 --end 2178
```

它会：

- 从 Codeforces API 获取 contest/problem/rating/official tags。
- 跳过官方 rating 低于 `1400` 的题。
- 排除语言限定、娱乐赛、启发式优化赛等非 ICPC 风格比赛。
- 把 official tags 映射成候选层级 tag，并标记为 `auto_seeded`。

它不会做题解分析，也不会产出高质量 reviewed tag。official tags 只能作为线索。

## 查询

按 rating 和 tag 查询：

```powershell
python scripts/search.py --rating 1500 2300 --tag algorithm/dp --show-tags
```

多个 `--tag` 表示 AND 查询：

```powershell
python scripts/search.py --tag algorithm/string/acam --tag algorithm/dp
```

排除某类 tag：

```powershell
python scripts/search.py --tag algorithm/dp --exclude data-structure/segment-tree
```

查询未评分或无评分题：

```powershell
python scripts/search.py --include-unrated --tag algorithm/dp
python scripts/search.py --rating-status pending_cf_rating
```

## 唯一键

contest 和 problem 使用稳定唯一键：

```text
contest_uid = cf_contest:{contest_id}
problem_uid = cf_problem:{contest_id}:{index}
```

下面两个 URL 必须归一到同一题：

```text
https://codeforces.com/problemset/problem/2231/A
https://codeforces.com/contest/2231/problem/A
```

归一结果：

```text
contest_id = 2231
index = A
problem_uid = cf_problem:2231:A
canonical_url = https://codeforces.com/contest/2231/problem/A
problemset_url = https://codeforces.com/problemset/problem/2231/A
```

## Reviewed JSON

核心字段：

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
      "notes": "题面与约束。"
    }
  ],
  "annotation": {
    "summary": "题意摘要。",
    "constraints": "关键约束。",
    "core_idea": "核心转化或关键观察。",
    "complexity": "O(...)",
    "tricks": ["关键技巧"],
    "confidence": "high",
    "review_status": "reviewed"
  },
  "solution_variants": [
    {
      "name": "main",
      "summary": "主解法。",
      "complexity": "O(...)",
      "confidence": "high",
      "is_primary": true
    }
  ],
  "tags": [
    {
      "tag": "algorithm/dp",
      "importance": "primary",
      "evidence": "DP 状态设计和转移是主解法核心。",
      "solution_variant": "main"
    }
  ]
}
```

## Rating 规则

- `problems.rating` 只能写 Codeforces 官方 rating。
- `rating_status = official` 时必须有整数 rating。
- 没有官方 rating 时使用 `pending_cf_rating`、`no_cf_rating` 或 `unknown`。
- 人工估分只能放在独立字段，不能参与默认 rating 查询。
- 默认拒绝官方 rating `< 1400` 的题。

## Tag 规则

tag 是动态层级路径：

```text
algorithm/string/acam
algorithm/dp/automaton-dp
algorithm/transform/fwt
data-structure/monotonic-stack
math/inclusion-exclusion/minmax
trick/maintain-contribution
```

新增 tag 默认是 `candidate`，必须提供：

- `description`
- `parent` 或 `parents`
- `created_reason`

## 测试

建议禁用 pycache：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
```

所有 Markdown 和 JSON 文件都应使用 UTF-8。

## Div.1 / Div.2 重题归并

同一轮 Codeforces 如果同时举办 Div.1 和 Div.2，且两边出现同名题目，则认为这是同一道题的不同入口。

规则：

- Div.1 入口作为 canonical problem。
- Div.2 入口只保留为 alias/source，不作为独立题目参与默认查询。
- `scripts/ingest_contests.py` 会在抽取后自动标记这类重题。
- `scripts/search.py`、`scripts/list_pending_reviews.py` 和 reviewed JSON 写库流程默认只处理 canonical problem。
- 如果对 Div.2 alias 生成模板或写入 reviewed JSON，会解析到 Div.1 canonical problem。

可手动重新扫描已有数据库：

```powershell
python scripts/dedupe_division_duplicates.py
```
