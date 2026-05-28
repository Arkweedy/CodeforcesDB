# AGENTS.md

本文件是给后续维护这个仓库的 agent / 脚本作者看的规则说明。执行任何抽取、tagging 或 schema 修改前都应先读这里。

## 仓库目标

这个仓库维护一个本地 Codeforces 题目数据库，目标是支持下面这类检索：

```text
2500~2900 + algorithm/transform/fwt
1500~2300 + algorithm/dp/digit-dp
1900 + paradigm/constructive
2300 + data-structure/monotonic-stack
algorithm/string/acam + algorithm/dp
```

数据库偏向 ICPC 风格训练题，不是完整收录所有 Codeforces 活动。

## Git 规则

- 本目录已经是 git 仓库。
- 每次运行 `scripts/ingest_contests.py` 完成抽取后，默认自动 commit `data/cfdb.sqlite`。
- 自动 commit message 必须包含抽取范围和入库题目数，例如 `ingest CF contests 2170-2178 (44 problems)`。
- 自动抽取提交只应 stage 数据库文件，不要顺手提交用户正在修改的代码或文档。
- 如果需要禁用自动提交，使用 `--no-auto-commit`。
- 修改代码、文档或 schema 后，应手动运行测试，再单独 commit。

## 唯一键规则

- contest 主键固定为 `contest_id`，派生唯一键为 `cf_contest:{contest_id}`。
- problem 主键固定为 `contest_id + problem_index`，派生唯一键为 `cf_problem:{contest_id}:{index}`。
- URL 不能作为主键；URL 只作为 source/canonical 信息。
- `problemset` 入口和 `contest` 入口必须归一为同一个 problem。
- problem index 必须按字符串保存，支持 `A`, `A1`, `B2`, `H` 等形式。

## 抽取范围与过滤规则

默认只保留官方 rating `>= 1400` 的题。不要把 1400 以下题写进正式题库。

默认排除：

- 语言限定赛，例如 `Kotlin Heroes`。
- 娱乐赛，例如 `April Fools Day Contest`。
- 启发式、优化、challenge、marathon 类比赛，例如 `ICPC 2025 Online Winter Challenge powered by Huawei`。
- 明显不是标准 AC 判题目标的比赛。

如果自动规则无法判断，使用 `needs_manual_review`，不要强行归类。

## Rating 规则

- `problems.rating` 只能使用 Codeforces 官方 rating。
- 有官方 rating 时必须采用官方值，不得自行评估覆盖。
- 暂无官方 rating 的新题标为 `pending_cf_rating`，并进入 `rating_refresh_queue`。
- 长期无 rating 的题标为 `no_cf_rating`。
- 如果将来确实需要人工估分，只能写入 `estimated_rating`，不得参与默认 rating 查询。

## Tag 规则

tag 是动态层级体系，不是封闭集合。路径示例：

```text
algorithm/string/acam
algorithm/dp/automaton-dp
algorithm/transform/fwt
data-structure/monotonic-stack
math/inclusion-exclusion/minmax
trick/maintain-contribution
```

新增 tag 的标准：

- 能显著改善未来检索。
- 不是一次性题面描述。
- 和已有 tag 不重复；同义词应加入 alias。
- 有清楚的父 tag、定义和使用边界。
- 预期可复用于多题，或属于经典算法、技巧、证明模式、题型范式。
- `primary` tag 必须有 evidence。

新增 tag 默认使用 `candidate`，review 后再改为 `active`。

## Annotation 规则

- 自动抽取阶段只使用 Codeforces official tags 映射到层级 tag，review 状态为 `auto_seeded`。
- 细粒度 tag、trick、主算法、复杂度、多解法必须通过人工 review 或后续 tagger 流程补充。
- 人工标注入口是 `scripts/tag_problem.py`。
- 项目内 tagger 规程在 `skills/cf-problem-tagger/SKILL.md`。
- 不要仅复述 Codeforces 官方 tag；reviewed annotation 应体现题解核心。

## Codeforces API 注意事项

- `contest.standings` 当前实现只传 `contestId`。
- 不要为了少取数据给匿名请求追加 `from` / `count` / `showUnofficial` 等参数；之前这样会触发 HTTP 400。
- API 访问需要节流，默认 delay 为 `2.1` 秒。
- 网络失败时不要手工编造 contest/problem 数据；应保留失败状态并重试。

## SQLite 注意事项

- 默认数据库路径是 `data/cfdb.sqlite`，这是需要被 git 跟踪的业务数据。
- 忽略 SQLite 临时文件：`*.sqlite-wal`, `*.sqlite-shm`, `*.sqlite-journal`。
- 使用 `cfdb.db.connect()`，它会在上下文退出时自动 commit/rollback 并关闭连接。
- 不要长期持有 SQLite 连接，否则 Windows 上可能锁住数据库文件。

## 测试与清洁

运行测试时建议禁用 pycache：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
```

提交前确认：

- 测试通过。
- 没有 `__pycache__`、`.pytest_cache` 或 SQLite 临时文件。
- `git status --short` 中没有无关用户改动被混入。
