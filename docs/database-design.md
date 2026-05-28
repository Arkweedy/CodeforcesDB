# 数据库设计规则

本文件记录数据库身份、rating、contest 过滤、Div.1/Div.2 去重等设计细则。

## 唯一键

contest 和 problem 使用稳定唯一键：

```text
contest_uid = cf_contest:{contest_id}
problem_uid = cf_problem:{contest_id}:{index}
```

URL 只作为 source/canonical 信息，不作为主键。

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

problem index 按字符串保存，支持 `A`, `A1`, `B2`, `H` 等格式。

## 核心表

主要业务表：

```text
contests
problems
problem_sources
problem_annotations
tags
tag_edges
tag_aliases
problem_tags
solution_variants
ingestion_queue
rating_refresh_queue
problem_user_state
```

`problem_user_state` 保存 WebUI 收藏和备注。它是 WebUI 唯一允许直接写入的业务表。

## Contest eligibility

`contests.eligibility_status`：

```text
eligible
excluded
needs_manual_review
```

默认排除：

- 语言限定赛，例如 `Kotlin Heroes`。
- 娱乐赛，例如 `April Fools Day Contest`。
- 启发式、优化、challenge、marathon 类比赛。
- 明显不是标准 AC 判题目标的比赛。
- 非标准通信/测试场，除非用户明确要求纳入。

无法判断时使用 `needs_manual_review`，不要强行归类。

保留人工 override：

```text
manual_include
manual_exclude
```

## Rating

`problems.rating` 只能使用 Codeforces 官方 rating。

`rating_status`：

```text
official
pending_cf_rating
no_cf_rating
unknown
```

规则：

- 有官方 rating 时必须使用官方值。
- 无官方 rating 时不能写入正式 `rating`。
- 新近比赛暂无 rating，标记 `pending_cf_rating`。
- 长期无 rating，标记 `no_cf_rating`。
- 人工估分若未来启用，只能放入独立字段，不参与默认 rating 查询。
- 默认只收录官方 rating `>= 1400` 的题。

## Div.1 / Div.2 重题归并

Codeforces 同一轮有时会同时开 Div.1 和 Div.2，且共享部分题目。

维护规则：

- 同一轮、同一开始时间、Div.1/Div.2 两边同名的题目视为同一道题。
- canonical problem 永远选择 Div.1 入口。
- Div.2 入口只能作为 alias/source 保存。
- Div.2 alias 不应进入默认查询结果。
- Div.2 alias 不应进入 pending review 列表。
- 如果用户要求 review Div.2 的重复入口，先解析到 Div.1 canonical problem。
- 不要为 Div.2 alias 单独创建高质量 reviewed tag。

已有库可重新扫描：

```powershell
python scripts/dedupe_division_duplicates.py
```

## 查询默认语义

默认查询行为：

- 只匹配 `rating_status = official`。
- 不显示 Div.1/Div.2 duplicate alias。
- tag 查询会展开子 tag。
- 多个 tag 默认表示 AND。
- 默认 importance 是 `primary + secondary`，不包含 `incidental`。

## SQLite 使用

- 默认数据库路径是 `data/cfdb.sqlite`。
- 这是需要 git 跟踪的业务数据。
- 忽略 SQLite 临时文件：`*.sqlite-wal`, `*.sqlite-shm`, `*.sqlite-journal`。
- 使用 `cfdb.db.connect()` 管理连接生命周期。
- 不要长期持有 SQLite 连接，Windows 上容易锁库。
