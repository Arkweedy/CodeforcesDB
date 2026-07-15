# AI-Reviewed 工作流

本文件说明高质量题目入库流程。脚本只负责校验和写库；题目 tag 的判断必须由 Codex agent 阅读题面、参考题解并推导后完成。

## 主入口

仓库内 skill：

```text
skills/cf-problem-tagger/SKILL.md
```

全局运行时副本：

```text
C:\Users\Arkweedy\.codex\skills\cf-problem-tagger
```

当用户指定题目或 contest 范围进行 review 时，agent 必须使用该 skill 的规则。

## 单题流程

1. 确认题目已完成 metadata/bootstrap。
2. 生成 reviewed JSON 模板。
3. 阅读题面和约束。
4. 查 Codeforces editorial、Luogu、可靠博客或 accepted code。
5. 必要时自行推导，并按资料充分程度设置 confidence。
6. 写出 annotation：
   - summary
   - constraints
   - core_idea
   - complexity
   - tricks
7. 写出一个或多个 `solution_variants`。
8. 写 tag，并区分 `primary / secondary / incidental`。
9. 每个 `primary` tag 必须有 evidence。
10. 应用 reviewed JSON 写库。
11. 运行覆盖检查和代表性查询。

## Luogu 候选来源

`make_review_template.py` 会生成 Luogu 候选题解 URL：

```text
https://www.luogu.com.cn/problem/solution/CF{contest_id}{index}
```

它只会出现在 `reference_candidates` 中。只有实际参考过该页面时，才把它移动到 `sources`，并写短 notes。

## Reviewed JSON 结构

核心形状：

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
  "reference_candidates": [
    {
      "source_type": "luogu_solution",
      "url": "https://www.luogu.com.cn/problem/solution/CF2170E",
      "notes": "候选来源；只有实际参考后才移动到 sources。"
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
      "tag": "dp",
      "importance": "primary",
      "evidence": "DP 状态设计和转移是主解法核心。",
      "solution_variant": "main"
    }
  ]
}
```

新增 tag 时，在对应 tag object 内补：

```json
{
  "description": "清晰定义。",
  "parent": "dp",
  "created_reason": "为什么值得成为可复用 tag。",
  "status": "candidate"
}
```

## 批量入库与提交

`apply_review_batch.py` 完成 AI-reviewed 批量入库后默认自动提交 `data/cfdb.sqlite`。

commit message 形如：

```text
review CF problems 2170A-2170F (6 problems)
```

review JSON 文件和文档/代码变更需要单独手动提交。

如需禁用自动提交：

```powershell
.venv\Scripts\python.exe scripts\apply_review_batch.py reviews\2170A.json --no-auto-commit
```

## 不允许的行为

- 只复用 Codeforces official tags 就标记 reviewed。
- 没读题面就写 tag。
- primary tag 没有 evidence。
- 新 tag 没有 definition/parent/created_reason。
- 把大段题解原文复制进 JSON。
- 为 Div.2 alias 单独写高质量 reviewed tag。
