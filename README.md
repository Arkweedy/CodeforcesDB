# Codeforces AI-Reviewed 题目数据库

这是一个本地 Codeforces 题目数据库，用来按难度、算法、数据结构、题型和 trick 快速定位训练题。

数据库的核心不是搬运 Codeforces official tags，而是保存经过 AI-reviewed 分析后的题目信息：题意摘要、核心观察、复杂度、解法变体、证据来源，以及细粒度层级 tag。

## 能做什么

- 按 rating 范围筛题，例如 `1500~2300`、`2500~2900`。
- 按层级 tag 筛题，例如 `动态规划 / 数位 DP`、`数学 / 变换 / FWT`、`数据结构 / 单调栈`。
- 多 tag 组合查询，例如 `AC 自动机 + DP`。
- 查看题目的核心思路、trick、复杂度、solution variants、来源链接和 tag evidence。
- 打开题目链接直接跳转到 Codeforces。
- 给题目做本地收藏和备注。
- 自动隐藏 Div.1 / Div.2 重复题的 alias，默认只显示 canonical problem。

## WebUI

WebUI 是主要使用入口，适合日常检索和浏览。

主要界面能力：

- 左侧按层级选择 tag。
- 通过 rating、rating status、tag 组合方式筛选题目。
- 支持中文 / English 切换。
- 题目按钮和 rating badge 使用 Codeforces 难度色段。
- tag chip 按算法大类配色。
- 题目详情抽屉展示完整 annotation、solution variants、sources、aliases、tag evidence。
- 收藏和备注只属于个人使用状态，不会改动 AI-reviewed tags。

## 给朋友试用

推荐方式是把仓库 push 到 Git 远端，让朋友直接 clone。`data/cfdb.sqlite` 是被 git 跟踪的业务数据，因此 clone 后会自带当前数据库。

依赖不会随仓库一起提交：

```text
.venv/
web/node_modules/
web/dist/
```

朋友需要本机安装：

- Python 3.11+。
- Node.js 20+，或至少能运行当前 Vite/React 工具链的 Node 版本。
- Git。

Windows PowerShell 快速启动：

```powershell
git clone <repo-url>
cd Codeforces

py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

npm.cmd ci --prefix web
npm.cmd run build --prefix web

.venv\Scripts\python.exe -m uvicorn cfdb.web_app:app --host 127.0.0.1 --port 8765
```

然后打开：

```text
http://127.0.0.1:8765
```

更多打包、zip 分发和未来公网部署注意事项见 [docs/sharing-and-deployment.md](docs/sharing-and-deployment.md)。

本地启动：

```powershell
.venv\Scripts\python.exe -m uvicorn cfdb.web_app:app --reload --host 127.0.0.1 --port 8765
npm.cmd run dev --prefix web
```

然后打开前端命令输出中的本地地址。开发模式下，前端会把 `/api` 请求代理到 FastAPI。

构建后也可以直接由 FastAPI 托管前端：

```powershell
npm.cmd run build --prefix web
.venv\Scripts\python.exe -m uvicorn cfdb.web_app:app --reload --host 127.0.0.1 --port 8765
```

## 数据质量

每道高质量入库题都应经过 AI-reviewed 流程：

- 阅读题面和约束。
- 参考 Codeforces editorial、Luogu、可靠博客或 accepted code。
- 必要时自行推导。
- 写明核心思路、trick、复杂度和证据。
- 区分 `primary / secondary / incidental` tag。

因此这里的 tag 会比 Codeforces official tags 更细，例如：

```text
math/transform/fwt/and-fwt
dp/digit-dp
data-structure/monotonic-stack
math/inclusion-exclusion/minmax
trick/maintain-contribution
```

## 文档职责

- [AGENTS.md](AGENTS.md)：给后续 Codex agent / 脚本维护者看的执行规则、约束和职责。
- [docs/ai-review-workflow.md](docs/ai-review-workflow.md)：AI-reviewed 标注流程、reviewed JSON 和 skill 使用方式。
- [docs/database-design.md](docs/database-design.md)：数据库唯一键、rating、contest 过滤、Div.1/Div.2 去重等设计规则。
- [docs/tagging.md](docs/tagging.md)：tag 层级、importance、evidence、新 tag 标准和翻译同步。
- [docs/webui-architecture.md](docs/webui-architecture.md)：WebUI 技术栈、前后端连接方式和文件职责。
- [docs/sharing-and-deployment.md](docs/sharing-and-deployment.md)：给朋友试用、zip 打包、依赖安装和公网部署注意事项。
- [docs/operations.md](docs/operations.md)：bootstrap、覆盖检查、脚本、测试和维护命令。

## 当前定位

这个仓库偏向 ICPC 风格训练题，不追求完整收录所有 Codeforces 活动。语言限定赛、娱乐赛、启发式优化赛、非标准交互/测试场等会被排除或标记人工审核。
