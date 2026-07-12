# WebUI 架构说明

WebUI 是本地单用户查询工具：React + TypeScript + Vite 提供界面，FastAPI 提供查询、个人状态和显式 Codeforces 同步。

## 数据边界

- `data/cfdb.sqlite` 是 Git 跟踪的主题库，WebUI 只读。
- `data/cfdb.user.sqlite` 是被忽略的个人 overlay，保存收藏、备注、手动/同步做题状态、个人优先级和设置。
- 可通过 `CFDB_PATH` 和 `CFDB_USER_PATH` 分别覆盖两条路径。
- WebUI 不编辑 rating、annotation、solution variants 或 tags；这些仍走 AI-reviewed JSON。

做题状态取值为 `unattempted / attempted / solved`。有效状态优先使用手动覆盖，其次使用 Codeforces 同步状态。个人优先级为 `critical / high / normal / low / NULL`。

## 后端接口

入口为 `cfdb.web_app:app`。主要接口：

```text
GET   /api/tags
GET   /api/search
GET   /api/analytics
GET   /api/problems/{problem_uid}
PATCH /api/problems/{problem_uid}/user-state
GET   /api/settings
PATCH /api/settings
POST  /api/sync/codeforces
```

`/api/search` 返回分页 items、total、当前筛选 summary 和动态 facets。列表查询一次性批量读取题目与 tag，避免逐题查询。筛选、排序、分页和当前详情写入 URL query params。

Codeforces 同步只由设置页显式触发：首次全量，之后按 submission id 增量；更换 handle 会清除同步状态，但保留手动状态和其他个人数据。

## 前端结构

```text
web/src/app/          页面组合、URL 状态、Query cache
web/src/features/     filters / problems / analytics / settings
web/src/shared/       Radix 封装、URL 序列化等通用能力
web/src/i18n/         可由前端和 Python 共用的 tag 翻译 JSON
```

- Radix Primitives：Dialog、Select、Popover、Tooltip、Checkbox、Collapsible。
- TanStack Query：查询缓存、分页占位、mutation 乐观更新和失效。
- Recharts：当前筛选/全库分析图表。
- 自定义 CSS tokens：低饱和青色、浅蓝、樱色和少量粉色。

桌面端为筛选、列表、详情三栏；平板使用侧边抽屉；手机列表改为卡片，筛选和详情改为全屏抽屉。设计基准见 [design/webui-cyan-concept.png](design/webui-cyan-concept.png)。

## 测试与扩展

- API response 使用 Pydantic model，前端维护对应的精简 TypeScript 类型。
- 后端测试必须使用临时主题库和用户库。
- 前端使用 Vitest + React Testing Library。
- tag 翻译唯一来源为 `web/src/i18n/tags.zh.json`；新增 tag 后运行 `python scripts/check_tag_translations.py`。
