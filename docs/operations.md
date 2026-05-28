# 维护操作

本文件面向维护者，记录 bootstrap、覆盖检查、脚本和测试命令。人类日常查询请使用 WebUI。

## 环境

建议使用仓库内虚拟环境：

```powershell
.venv\Scripts\python.exe
```

前端包管理使用：

```powershell
npm.cmd
```

避免 PowerShell 执行策略拦截 `npm.ps1`。

## Bootstrap 元数据

`scripts/ingest_contests.py` 只用于获取 contest/problem/rating/official tags 等基础元数据。

```powershell
python scripts/ingest_contests.py --start 2170 --end 2178
```

它不会做 AI-reviewed 分析，也不会产出高质量 tag。

## 覆盖状态检查

查看范围覆盖：

```powershell
python scripts/list_missing_contests.py --start 2170 --end 2178
```

只看需要处理的场次：

```powershell
python scripts/list_missing_contests.py --start 2170 --end 2178 --only-actionable
```

状态含义：

- `not_in_db`：本地还没有 contest 元数据，需要先 bootstrap。
- `unextracted`：contest 已入库，但题目还没完成 bootstrap。
- `needs_manual_review`：需要人工确认是否适合纳入。
- `failed`：bootstrap 失败，需要重试或排查网络/API。
- `pending_review`：题目已 bootstrap，但仍是 `raw/auto_seeded`，需要 AI review。
- `complete`：默认无需处理。
- `excluded`：已排除。

## Pending review

列出待 review 题：

```powershell
python scripts/list_pending_reviews.py --limit 20
```

生成 reviewed JSON 模板：

```powershell
python scripts/make_review_template.py 2170E --out reviews/2170E.json
```

写入单题：

```powershell
python scripts/apply_reviewed_problem.py reviews/2170E.json
```

批量写入并自动提交 DB：

```powershell
python scripts/apply_review_batch.py reviews/2170A.json reviews/2170B.json
```

## 搜索脚本

命令行搜索脚本用于维护、验收和调试，不是 README 面向人类的主入口。

示例：

```powershell
python scripts/search.py --rating 2500 2900 --tag algorithm/transform/fwt --show-tags
python scripts/search.py --tag algorithm/string/acam --tag algorithm/dp
python scripts/search.py --include-unrated --tag algorithm/dp
```

## WebUI

WebUI 结构说明见 [webui-architecture.md](webui-architecture.md)。

后端：

```powershell
python -m uvicorn cfdb.web_app:app --reload --host 127.0.0.1 --port 8765
```

前端开发模式：

```powershell
npm.cmd run dev --prefix web
```

构建：

```powershell
npm.cmd run build --prefix web
```

## 测试

后端单测：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
```

tag 翻译检查：

```powershell
python scripts/check_tag_translations.py
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
