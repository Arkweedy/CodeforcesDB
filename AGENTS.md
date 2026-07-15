# AGENTS.md

本文件面向后续维护这个仓库的 Codex agent / 脚本作者。执行抽取、review、tagging、schema 修改、WebUI 修改前都应先读这里。

所有 Markdown、JSON、Python 源码都使用 UTF-8。读取中文文档时显式使用 UTF-8，避免 PowerShell 默认编码导致乱码。

## 仓库目标

这个仓库维护一个本地 Codeforces 题目数据库，用于按 rating、算法、数据结构、题型、trick 检索 ICPC 风格训练题。

典型查询目标：

```text
2500~2900 + math/transform/fwt
1500~2300 + dp/digit-dp
1900 + paradigm/constructive
2300 + data-structure/monotonic-stack
string/acam + dp
```

数据库不追求完整收录所有 Codeforces 活动。语言限定赛、娱乐赛、启发式优化赛、特殊测试场等应排除或标记人工审核。

## 文档职责

- `AGENTS.md`：agent 执行规则、职责、约束、提交规范。
- `README.md`：面向人类使用者，介绍数据库功能和 WebUI。
- `docs/ai-review-workflow.md`：AI-reviewed 工作流、reviewed JSON、skill。
- `docs/database-design.md`：唯一键、rating、contest 过滤、Div.1/Div.2 去重。
- `docs/tagging.md`：tag 层级、新 tag 标准、evidence 和前端翻译同步。
- `docs/webui-architecture.md`：WebUI 技术栈、前后端接口、文件职责和扩展方式。
- `docs/sharing-and-deployment.md`：试用分发、依赖安装、zip 打包、公网部署注意事项。
- `docs/operations.md`：bootstrap、覆盖检查、维护脚本、测试命令。

## 最重要原则

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

## Agent 职责

当用户要求抽取或 review Codeforces 题目时：

1. 先检查范围覆盖状态，判断是需要 bootstrap、AI review，还是已经 complete/excluded。
2. 对每道题使用 `cf-problem-tagger` 工作流。
3. 阅读题面和约束。
4. 优先查 Codeforces editorial、Luogu、可靠博客、accepted code；资料不足时自行推导并降低 confidence。
5. 写出题意摘要、核心转化或关键观察、复杂度、tricks。
6. 区分 `primary / secondary / incidental` tag。
7. 每个 `primary` tag 必须有 evidence。
8. 一题多解时写入 `solution_variants`，并把 tag 绑定到对应解法。
9. reviewed JSON 只保存来源 URL 和短 notes，不保存大段题解原文。
10. 入库后运行必要查询/测试确认结果。

详细流程见 [docs/ai-review-workflow.md](docs/ai-review-workflow.md)。

## 并行 AI Review 规则

长批量 AI review 应默认使用 worker 并行分析，但所有落库和提交动作必须由主 agent 串行完成。

触发并行策略：

- 待 review 题数 `>= 6`。
- 或包含 `>= 3` 道 `2800+` 题。
- 或预计单线程 review 超过约 30 分钟。
- 若用户明确要求顺序 review、低 token，或任务很小，则不并行。

worker 数量：

- 默认最多开 `3` 个 worker。
- 低中难度大批量超过 20 题时可开到 `4` 个 worker。
- 不要为了追求数量让多个 worker 分析同一道题。
- 优先启动最高 rating、资料最少或推导最重的题，让长尾分析和中低难题重叠进行。
- 使用滚动窗口：worker 完成后先保存结果并关闭，再补发下一片；不要把已完成 worker 长时间留在并发槽位中。

主 agent 职责：

- 检查范围覆盖状态，确认哪些题需要 bootstrap、AI review、跳过或排除。
- 处理 Div.1 / Div.2 重叠题：同一共享题只分配 canonical Div.1 题，Div.2 入口只作为 alias/source。
- 按难度切片并分配 worker。
- 汇总并审核 worker 的 reviewed JSON 草稿。
- 统一判断新 tag 是否应该创建，避免近义 tag、重复 tag 或错误父级。
- 同步维护 `web/src/i18n/tags.zh.json` 中的完整 tag 路径翻译；新路径片段可复用时，同时维护 `web/src/i18n.ts` 的 segment fallback。
- 统一规范化来源类型和 URL；候选链接只有实际读取后才能进入 `sources[]`，无法确认 verdict 的代码不得标成 accepted code。
- 串行运行 `apply_review_batch.py` 写入数据库。
- 以 contest 为写入屏障：上一场的 DB 必须完成校验、commit 和 push，才允许 apply 下一场，避免 SQLite 二进制改动无法按场次拆分。
- 统一运行搜索验收、`check_tag_translations.py`、后端测试和必要的前端构建。
- DB 自动提交后立即 push；review payload、i18n 或文档改动另行提交并 push。

worker 职责：

- 只分析被分配的题目并输出 reviewed JSON 草稿。
- 每题必须阅读题面和约束，并参考 Codeforces editorial、Luogu、可靠博客、accepted code 或自行推导。
- 每题必须输出 annotation、solution variants、tags、primary evidence。
- 对不确定题降低 confidence，并明确列出需要主 agent 复核的点。
- 可以提议新 tag，但不能自行决定最终 taxonomy。
- 不得直接写 `data/cfdb.sqlite`，不得运行 `apply_review_batch.py`，不得 commit 或 push。

worker 生命周期：

- 同一题只分配给一个 worker，并记录稳定的 problem label。
- worker 最终输出应以每题一个完整 JSON code block 为主，减少主 agent 二次提取成本。
- 主 agent 收到结果后必须先解析并保存草稿，再关闭 worker；不得先关闭再依赖重新传输长输出。
- worker 的完成通知到达后，不要再向同一 worker 追加补充消息；追加消息可能把已完成状态重新置为运行，造成关闭时拿不到结果。应先持久化 JSON、关闭 worker，再把补充要求放到下一批 prompt。
- worker 成为长尾时，先保留其已有工作并检查进度；必要时由主 agent 接管缺失部分，不要直接重复派发同一道题。

默认切片粒度：

- `1400~2299`：每 worker `4~6` 题。
- `2300~2799`：每 worker `2~4` 题。
- `2800~2999`：每 worker `1~2` 题。
- `3000+`：通常一题一个 worker。
- 每批应先派发 `3000+` 和来源困难题，再派发其余题，避免它们在场次收尾时才进入关键路径。
- Easy / Hard 或其他共享题面的版本对优先交给同一个 worker。共用一次题面模型、editorial 和小规模 oracle，但分别写 JSON，并明确语义差异、复杂度边界与哪些算法不能从低约束版本直接复用。

并行后的主 agent 复核清单：

- 是否遗漏题目或重复 review。
- 是否错误保留了 Div.2 alias 作为独立题。
- 是否只把 Codeforces official tags 直映射成 reviewed tags。
- 每个 `primary` tag 是否有足够 evidence。
- 新 tag 是否符合 [docs/tagging.md](docs/tagging.md) 的标准，是否已有近义 tag 或 alias。
- reviewed JSON、数据库、前端翻译和查询结果是否一致。

## Git 规则

- 本目录是 git 仓库。
- `apply_review_batch.py` 完成 AI-reviewed 批量入库后默认自动 commit `data/cfdb.sqlite`。
- DB commit message 必须包含 reviewed problem 范围和题目数，例如 `review CF problems 2170A-2170F (6 problems)`。
- `ingest_contests.py` 的自动提交只代表 metadata/bootstrap，不代表 AI review 完成。
- 自动 DB 提交只应 stage 数据库文件。
- 代码、文档、schema、review payload 修改应单独手动 commit。
- 远程仓库已绑定；每次成功 commit 后应顺手 `git push` 当前分支，除非用户明确要求暂不 push。
- 如需禁用自动提交，使用 `--no-auto-commit`。
- 不要把无关用户改动混入提交；尤其注意 `data/cfdb.sqlite` 可能因 SQLite 打开/验证产生二进制状态变化。

## 抽取与过滤底线

默认只保留官方 rating `>= 1400` 的题。

默认排除：

- 语言限定赛，例如 `Kotlin Heroes`。
- 娱乐赛，例如 `April Fools Day Contest`。
- 启发式、优化、challenge、marathon 类比赛。
- IOI rules / 子任务评分场次，例如 `Open Olympiad in Informatics ... (IOI rules)`。
- 明显不是标准 AC 判题目标的比赛。
- 非标准测试场或特殊活动，除非用户明确要求纳入。

无法判断时使用 `needs_manual_review`，不要强行归类。

## Rating 规则

- `problems.rating` 只能使用 Codeforces 官方 rating。
- 有官方 rating 时必须采用官方值，不得自行评估覆盖。
- 暂无官方 rating 的新题标为 `pending_cf_rating`。
- 长期无 rating 的题标为 `no_cf_rating`。
- 人工估分只能写入独立字段，不得参与默认 rating 查询。

## Tag 规则

tag 是动态层级体系，不是封闭集合：

```text
string/acam
dp/automaton-dp
math/transform/fwt
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

新增 tag 默认使用 `candidate`。创建新 tag 后还应维护 WebUI 中文翻译，并运行：

```powershell
.venv\Scripts\python.exe scripts\check_tag_translations.py
```

详细规则见 [docs/tagging.md](docs/tagging.md)。

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

## WebUI 维护规则

- WebUI 是本地个人查询工具，不做登录和权限。
- 后端入口是 `cfdb.web_app:app`，前端在 `web/`。
- WebUI 必须把个人数据写入被 Git 忽略的 `data/cfdb.user.sqlite` overlay；主题库 `data/cfdb.sqlite` 对 WebUI 只读。
- WebUI 只允许写 favorite、note、手动/同步做题状态、个人优先级和 app settings。
- 不要通过 WebUI 编辑 rating、annotation、solution variants 或 tags；这些仍必须走 AI-reviewed JSON 流程。
- 前端包管理使用 `npm.cmd`，避免 PowerShell 执行策略拦截 `npm.ps1`。
- 修改 WebUI 后至少运行后端单测、`npm.cmd test --prefix web` 和 `npm.cmd run build --prefix web`。

## 测试与清洁

运行测试：

优先使用仓库虚拟环境；系统 Python 可能缺少 FastAPI 等项目依赖，从而产生与代码无关的假失败。

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONDONTWRITEBYTECODE='1'; .venv\Scripts\python.exe -m unittest discover -s tests
```

提交前确认：

- 测试通过。
- 没有 `__pycache__`、`.pytest_cache` 或 SQLite 临时文件。
- `git status --short` 中没有无关用户改动被混入。
