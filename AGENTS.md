# AGENTS.md

本文件是给后续维护这个仓库的 Codex agent / 脚本作者看的规则说明。执行抽取、review、tagging、schema 修改前都应先读这里。

所有 Markdown、JSON、Python 源码都使用 UTF-8。读取中文文档时显式使用 UTF-8，避免 PowerShell 默认编码导致乱码。

## 仓库目标

这个仓库维护一个本地 Codeforces 题目数据库，目标是支持这类检索：

```text
2500~2900 + algorithm/transform/fwt
1500~2300 + algorithm/dp/digit-dp
1900 + paradigm/constructive
2300 + data-structure/monotonic-stack
algorithm/string/acam + algorithm/dp
```

数据库偏向 ICPC 风格训练题，不完整收录所有 Codeforces 活动。

## 最重要的原则

真正的题目抽取必须有 AI-reviewed 分析参与。

`scripts/ingest_contests.py` 只能作为 metadata/bootstrap 工具。它写入的 Codeforces official tags 只是候选线索，`review_status` 只能是 `auto_seeded`，不能代表高质量 tag 已完成。

高质量入库必须使用 `cf-problem-tagger` skill：

```text
skills/cf-problem-tagger/SKILL.md
```

全局 skill 运行时副本应同步到：

```text
C:\Users\Arkweedy\.codex\skills\cf-problem-tagger
```

## AI-reviewed 工作流

每道题必须：

- 读取题面和约束。
- 优先查 Codeforces editorial、Luogu、可靠博客、accepted code；资料不足时自行推导并降低 confidence。
- `make_review_template.py` 会生成 Luogu `reference_candidates`；候选来源只有实际参考后才应移动到 reviewed JSON 的 `sources`。
- 写出题意摘要、核心转化或关键观察、复杂度、tricks。
- 区分 `primary / secondary / incidental` tag。
- 每个 `primary` tag 必须有 evidence。
- 一题多解时写入 `solution_variants`，并把 tag 绑定到对应解法。
- reviewed JSON 只保存来源 URL 和短 notes，不保存大段题解原文。

## Git 规则

- 本目录是 git 仓库。
- `apply_review_batch.py` 完成 AI-reviewed 批量入库后默认自动 commit `data/cfdb.sqlite`。
- commit message 必须包含 reviewed problem 范围和题目数，例如 `review CF problems 2170A-2170F (6 problems)`。
- `ingest_contests.py` 的自动提交只代表 metadata/bootstrap，不代表 AI review 完成。
- 自动提交只应 stage 数据库文件；代码、文档、schema 修改应单独手动 commit。
- 如需禁用自动提交，使用 `--no-auto-commit`。

## 唯一键规则

- contest 主键固定为 `contest_id`，派生唯一键为 `cf_contest:{contest_id}`。
- problem 主键固定为 `contest_id + problem_index`，派生唯一键为 `cf_problem:{contest_id}:{index}`。
- URL 不能作为主键，只作为 source/canonical 信息。
- `problemset` 入口和 `contest` 入口必须归一到同一题。
- problem index 按字符串保存，支持 `A`, `A1`, `B2`, `H` 等形式。

## 抽取范围与过滤规则

默认只保留官方 rating `>= 1400` 的题。

默认排除：

- 语言限定赛，例如 `Kotlin Heroes`。
- 娱乐赛，例如 `April Fools Day Contest`。
- 启发式、优化、challenge、marathon 类比赛，例如 `ICPC 2025 Online Winter Challenge powered by Huawei`。
- 明显不是标准 AC 判题目标的比赛。

无法判断时使用 `needs_manual_review`，不要强行归类。

给定 contest id 范围前，优先运行覆盖状态检查：

```powershell
python scripts/list_missing_contests.py --start 2170 --end 2178
```

其中 `not_in_db` / `unextracted` 代表需要先 bootstrap；`pending_review` 代表可以进入 AI-reviewed 标注；`complete` / `excluded` 默认无需处理。

## Rating 规则

- `problems.rating` 只能使用 Codeforces 官方 rating。
- 有官方 rating 时必须采用官方值，不得自行评估覆盖。
- 暂无官方 rating 的新题标为 `pending_cf_rating`。
- 长期无 rating 的题标为 `no_cf_rating`。
- 人工估分只能写入独立字段，不得参与默认 rating 查询。

## Tag 规则

tag 是动态层级体系，不是封闭集合：

```text
algorithm/string/acam
algorithm/dp/automaton-dp
algorithm/transform/fwt
data-structure/monotonic-stack
math/inclusion-exclusion/minmax
trick/maintain-contribution
```

新增 tag 标准：

- 能显著改善未来检索。
- 不是一次性题面描述。
- 和已有 tag 不重复；同义词应加入 alias。
- 有清楚的父 tag、定义和使用边界。
- 预期可复用于多题，或属于经典算法、技巧、证明模式、题型范式。
- `primary` tag 必须有 evidence。

新增 tag 默认使用 `candidate`。

创建新 tag 后还应维护 WebUI 中文翻译。运行：

```powershell
python scripts/check_tag_translations.py
```

若脚本报告缺失，优先补 `web/src/i18n.ts`；如果暂不补，需确认 fallback 英文路径显示可接受。

## Codeforces API 注意事项

- `contest.standings` 当前实现只传 `contestId`。
- 不要为匿名请求追加 `from` / `count` / `showUnofficial`；之前这样会触发 HTTP 400。
- API 访问需要节流，默认 delay 是 `2.1` 秒。
- 网络失败时不要手工编造 contest/problem 元数据，应保留失败状态并重试。

## SQLite 注意事项

- 默认数据库路径是 `data/cfdb.sqlite`，这是需要 git 跟踪的业务数据。
- 忽略 SQLite 临时文件：`*.sqlite-wal`, `*.sqlite-shm`, `*.sqlite-journal`。
- 使用 `cfdb.db.connect()`，它会在上下文退出时自动 commit/rollback 并关闭连接。
- 不要长期持有 SQLite 连接，否则 Windows 上可能锁住数据库文件。

## 测试与清洁

运行测试：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
```

提交前确认：

- 测试通过。
- 没有 `__pycache__`、`.pytest_cache` 或 SQLite 临时文件。
- `git status --short` 中没有无关用户改动被混入。

## Div.1 / Div.2 重题归并规则

Codeforces 同一轮有时会同时开 Div.1 和 Div.2，且共享部分题目。维护数据库时必须去重：

- 同一轮、同一开始时间、Div.1/Div.2 两边同名的题目视为同一道题。
- canonical problem 永远选择 Div.1 入口。
- Div.2 入口只能作为 alias/source 保存，不应进入默认查询结果，也不应进入 pending review 列表。
- 如果用户要求 review Div.2 的重复入口，先解析到 Div.1 canonical problem，再写 annotation、solution variants 和 tags。
- 不要为 Div.2 alias 单独创建高质量 reviewed tag；否则聚合查询会重复计数。
- 抽取后运行或确认 `mark_division_duplicates()`，已有库可用 `python scripts/dedupe_division_duplicates.py` 重新扫描。

## WebUI 维护规则

- WebUI 是本地个人查询工具，不做登录和权限。
- 后端入口是 `cfdb.web_app:app`，前端在 `web/`。
- WebUI 唯一允许写库的业务数据是 `problem_user_state` 中的 favorite 和 note。
- 不要通过 WebUI 编辑 rating、annotation、solution variants 或 tags；这些仍必须走 AI-reviewed JSON 流程。
- 前端包管理使用 `npm.cmd`，避免 PowerShell 执行策略拦截 `npm.ps1`。
- 修改 WebUI 后至少运行后端单测和 `npm.cmd run build --prefix web`。
