# 维护操作

本文件面向维护者，记录 bootstrap、覆盖检查、脚本和测试命令。人类日常查询请使用 WebUI。

## 环境

建议使用仓库内虚拟环境：

```powershell
.venv\Scripts\python.exe
```

批处理前建议固定 UTF-8，并避免测试产生字节码垃圾：

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
```

维护脚本和测试统一使用 `.venv\Scripts\python.exe`。不要回退到系统 `python` 判断依赖是否可用；系统环境缺少 FastAPI 等包时会产生与仓库无关的假失败。

前端包管理使用：

```powershell
npm.cmd
```

避免 PowerShell 执行策略拦截 `npm.ps1`。

## Bootstrap 元数据

`scripts/ingest_contests.py` 只用于获取 contest/problem/rating/official tags 等基础元数据。

```powershell
.venv\Scripts\python.exe scripts\ingest_contests.py --start 2170 --end 2178
```

它不会做 AI-reviewed 分析，也不会产出高质量 tag。

## 覆盖状态检查

查看范围覆盖：

```powershell
.venv\Scripts\python.exe scripts\list_missing_contests.py --start 2170 --end 2178
```

只看需要处理的场次：

```powershell
.venv\Scripts\python.exe scripts\list_missing_contests.py --start 2170 --end 2178 --only-actionable
```

状态含义：

- `not_in_db`：本地还没有 contest 元数据，需要先 bootstrap。
- `unextracted`：contest 已入库，但题目还没完成 bootstrap。
- `needs_manual_review`：需要人工确认是否适合纳入。
- `failed`：bootstrap 失败，需要重试或排查网络/API。
- `pending_review`：题目已 bootstrap，但仍是 `raw/auto_seeded`，需要 AI review。
- `complete`：默认无需处理。
- `excluded`：已排除。
- `not_found`：该 contest id 是 Codeforces 编号空洞，不是待抽取场次；`--only-actionable` 会隐藏它。

## Pending review

列出待 review 题：

```powershell
.venv\Scripts\python.exe scripts\list_pending_reviews.py --limit 20
```

生成 reviewed JSON 模板：

```powershell
.venv\Scripts\python.exe scripts\make_review_template.py 2170E --out reviews/2170E.json
```

写入单题：

```powershell
.venv\Scripts\python.exe scripts\apply_reviewed_problem.py reviews/2170E.json
```

批量写入并自动提交 DB：

```powershell
.venv\Scripts\python.exe scripts\apply_review_batch.py reviews/2170A.json reviews/2170B.json
```

## 批量 AI Review 效率与故障经验

### 调度与 worker 生命周期

- 先派发 `3000+`、资料稀缺和需要自行证明的题，再处理普通题，尽量让长尾耗时被其他 worker 覆盖。
- worker 使用滚动窗口；同一题只分配一次。并发槽满时，先保存并关闭已经完成的 worker，再补发下一片。
- worker 返回长 JSON 后，主 agent 必须先解析并保存草稿，再关闭 worker。先关闭再取结果会造成重复传输或重做。
- 长尾 worker 不要直接重复派发；先保留已有分析，必要时由主 agent 只接管缺失的来源或证明。

### 来源检索捷径

- NERC、NEERC 等 ICPC mirror 优先直接查官方 statement PDF、tutorial PDF、jury archive 和 runs archive，不要把时间耗在寻找不存在的普通 Codeforces blog editorial。
- 遇到赛后修题面或更正语义时，先核对当前题面、主办方公告和官方分析的发布时间；以更正后的语义为准，并把更正公告写入 source notes，禁止复用基于旧题面的分析。确认一次后应把有效公告或官方 PDF URL 共享给同场其他 worker，避免重复检索。
- Luogu 题解 URL 只是候选。只有实际打开并读取后才能写入 `sources[]`；页面为零篇题解或访问失败时应如实记录，不得当作算法证据。
- 来源类型在合并前统一：`accepted_code` / `accepted_submission` 归一为 `accepted-code`，`independent_blog` / `reliable_blog` / `author_blog` 归一为 `blog`；主办方更正公告也使用 `blog`，并在 notes 中说明其官方性质。
- 无法确认 verdict 的归档代码保留为 `independent_code`，不能升级成 `accepted-code`。
- reviewed JSON 不保留 `local:` URL。自行推导和本地对拍使用题目的 canonical Codeforces URL，验证细节写入短 notes。

### 校验与写入屏障

- 先用只读 SQLite 连接验证一个 contest 的全部 JSON，再在一个 `apply_review_batch.py` 事务中按题号串行写入。
- 一场 contest 是最小 DB 提交单位。上一场 DB 完成 commit 和 push 前，不 apply 下一场，否则 SQLite 二进制改动无法可靠拆分。
- 新 tag 由主 agent 统一去重、确定父级并同步完整路径和 segment fallback 翻译；不要直接接受各 worker 的近义候选。
- JSON 逐题做轻量校验；完整后端测试、前端测试和构建在每场完成后统一运行一次，避免无意义重复。
- 修改大型翻译表前先读取精确上下文，使用小范围 `apply_patch`；一个过时锚点会让整个复合补丁原子失败。

## 搜索脚本

命令行搜索脚本用于维护、验收和调试，不是 README 面向人类的主入口。

示例：

```powershell
.venv\Scripts\python.exe scripts\search.py --rating 2500 2900 --tag math/transform/fwt --show-tags
.venv\Scripts\python.exe scripts\search.py --tag string/acam --tag dp
.venv\Scripts\python.exe scripts\search.py --include-unrated --tag dp
```

## WebUI

WebUI 结构说明见 [webui-architecture.md](webui-architecture.md)。
试用分发与部署说明见 [sharing-and-deployment.md](sharing-and-deployment.md)。

后端：

```powershell
.venv\Scripts\python.exe -m uvicorn cfdb.web_app:app --reload --host 127.0.0.1 --port 8000
```

个人数据默认写入被 Git 忽略的 `data/cfdb.user.sqlite`。需要其他位置时设置：

```powershell
$env:CFDB_USER_PATH='D:\path\to\cfdb.user.sqlite'
```

Vite 默认代理到 `http://127.0.0.1:8000`，可通过 `VITE_API_TARGET` 覆盖。

前端开发模式：

```powershell
npm.cmd run dev --prefix web
```

构建：

```powershell
npm.cmd run build --prefix web
```

前端测试：

```powershell
npm.cmd test --prefix web
```

## 测试

后端单测：

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONDONTWRITEBYTECODE='1'; .venv\Scripts\python.exe -m unittest discover -s tests
```

tag 翻译检查：

```powershell
.venv\Scripts\python.exe scripts\check_tag_translations.py
```

提交前检查：

```powershell
git status --short
```

确认没有 `__pycache__`、`.pytest_cache`、SQLite 临时文件或无关用户改动。

## Codeforces API 注意事项

- `contest.standings` 当前实现只传 `contestId`。
- 不要为匿名请求追加 `from` / `count` / `showUnofficial`。
- API 访问需要节流，默认 delay 是 `2.1` 秒。
- 网络失败时不要手工编造 contest/problem 元数据，应保留失败状态并重试。
