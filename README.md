# Codeforces 题目数据库

这是一个本地 SQLite 题目数据库，用来按 rating、算法、数据结构、题型、trick 等条件快速检索 Codeforces 题目。

当前数据库默认路径：

```text
data/cfdb.sqlite
```

## 快速开始

初始化数据库和基础 tag registry：

```powershell
python scripts/init_db.py
```

抽取一段 contest：

```powershell
python scripts/ingest_contests.py --start 2170 --end 2178
```

抽取脚本默认会：

- 跳过官方 rating 低于 `1400` 的题。
- 使用 Codeforces 官方 rating；没有官方 rating 时不会自行估分。
- 应用非 ICPC 风格比赛排除规则。
- 抽取结束后自动提交 `data/cfdb.sqlite`，commit message 会写明抽取范围和题目数。

如果只想抽取但不自动 commit：

```powershell
python scripts/ingest_contests.py --start 2170 --end 2178 --no-auto-commit
```

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

查询未评分或无评分题时需要显式指定：

```powershell
python scripts/search.py --include-unrated --tag algorithm/dp
python scripts/search.py --rating-status pending_cf_rating
```

## 唯一键与 URL 归一化

contest 和 problem 都使用稳定唯一键：

```text
contest_uid = cf_contest:{contest_id}
problem_uid = cf_problem:{contest_id}:{index}
```

下面两个入口会归一到同一道题：

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

## Rating 策略

`problems.rating` 只存 Codeforces 官方 rating。默认 rating 查询只匹配：

```text
rating_status = official
```

其他状态：

```text
pending_cf_rating  # 新题暂无 rating，等待 CF 更新
no_cf_rating       # 长期无 CF rating，例如部分 ICPC mirror
unknown            # 抽取失败或信息不完整
```

如果以后需要人工估分，只能写入独立字段 `estimated_rating`，不得混入默认 rating 查询。

## Tag 体系

tag 是动态维护的层级路径，不是封闭枚举：

```text
algorithm/string/acam
algorithm/dp/automaton-dp
algorithm/transform/fwt
data-structure/monotonic-stack
math/inclusion-exclusion/minmax
paradigm/constructive
trick/maintain-contribution
```

tag registry 存在 SQLite 表中：

```text
tags
tag_edges
tag_aliases
```

查询父 tag 会包含子 tag，alias 会自动归一化。新增 tag 默认应为 `candidate`，review 后再改成 `active`。

## 人工细化题目标签

项目内置了 tagger skill 规程：

```text
skills/cf-problem-tagger/SKILL.md
```

人工 review 后，用 JSON 文件更新题目 annotation、solution variants 和精细 tag：

```powershell
python scripts/tag_problem.py annotations/2170E.json
```

JSON 形状：

```json
{
  "problem": "2170E",
  "annotation": {
    "summary": "题意摘要。",
    "core_idea": "核心转化或关键观察。",
    "complexity": "O(n log n)",
    "confidence": "high",
    "review_status": "reviewed"
  },
  "solution_variants": [
    {
      "name": "main",
      "summary": "主流解法概述。",
      "complexity": "O(n log n)",
      "confidence": "high",
      "is_primary": true
    }
  ],
  "tags": [
    {
      "tag": "algorithm/dp",
      "importance": "primary",
      "evidence": "状态设计和转移是主解法核心。",
      "source": "manual",
      "solution_variant": "main"
    }
  ]
}
```

## 常用维护命令

列出 eligible 但尚未完成抽取的 contest：

```powershell
python scripts/list_unextracted_contests.py
```

手动加入或更新 tag：

```powershell
python scripts/add_tag.py algorithm/string/acam --status active --alias acam
```

运行测试：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
```

## 当前 demo 数据

已抽取范围：

```text
contest/2170 ~ contest/2178
```

其中 `2177 ICPC 2025 Online Winter Challenge powered by Huawei` 被排除，因为它属于启发式/优化 challenge，不适合作为 ICPC 风格题库数据。
