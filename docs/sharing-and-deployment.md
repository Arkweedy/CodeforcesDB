# 试用分发与部署说明

本文件说明如何把数据库给朋友试用，以及以后考虑公网部署前需要注意什么。

## 能不能直接 clone

可以。

本仓库把核心业务数据 `data/cfdb.sqlite` 纳入 git 跟踪，所以只要你已经把最新数据库 commit 并 push，朋友 clone 后会拿到同一份题库数据。

不会随仓库提交的内容包括：

```text
.venv/
web/node_modules/
web/dist/
.npm-cache/
__pycache__/
```

这些都应在朋友本机重新安装或构建。

## 推荐试用方式：Git clone

适合会使用 Git 的朋友。

### 依赖

建议环境：

- Python 3.11+。
- Node.js 20+。
- Git。

Node 版本不必和开发机完全一致，但应能运行 Vite 6 / React 18 工具链。

### Windows PowerShell

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

### macOS / Linux

```bash
git clone <repo-url>
cd Codeforces

python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt

npm ci --prefix web
npm run build --prefix web

python -m uvicorn cfdb.web_app:app --host 127.0.0.1 --port 8765
```

然后打开：

```text
http://127.0.0.1:8765
```

## 开发模式启动

如果朋友想看前端热更新或改 UI，可以用开发模式。

终端 1：

```powershell
.venv\Scripts\python.exe -m uvicorn cfdb.web_app:app --reload --host 127.0.0.1 --port 8765
```

终端 2：

```powershell
npm.cmd run dev --prefix web
```

打开 Vite 输出的地址，通常是：

```text
http://127.0.0.1:5173
```

开发模式下，Vite 会把 `/api` 代理到 `http://127.0.0.1:8765`。

## 单服务模式启动

如果只是试用，推荐先 build 前端，然后只跑 FastAPI。

```powershell
npm.cmd run build --prefix web
.venv\Scripts\python.exe -m uvicorn cfdb.web_app:app --host 127.0.0.1 --port 8765
```

原因：

- 只开一个服务。
- 不需要 Vite 常驻。
- 更接近未来部署方式。

`web/dist` 被 `.gitignore` 忽略，所以 clone 后需要自己运行 `npm.cmd run build --prefix web`。

## 不用 Git 的 zip 打包

如果朋友不想用 Git，可以发 zip。

zip 应包含：

```text
cfdb/
data/cfdb.sqlite
docs/
reviews/
scripts/
skills/
tests/
web/
README.md
AGENTS.md
requirements.txt
web/package.json
web/package-lock.json
```

zip 不应包含：

```text
.git/
.venv/
web/node_modules/
web/dist/
.npm-cache/
__pycache__/
.pytest_cache/
*.sqlite-wal
*.sqlite-shm
*.sqlite-journal
```

收到 zip 后，朋友仍需要执行安装依赖和构建前端的步骤。

## 更新数据库

如果使用 Git：

```powershell
git pull
npm.cmd ci --prefix web
npm.cmd run build --prefix web
```

通常 Python 依赖很少变化，不一定每次都要重新安装；如果 `requirements.txt` 改了，再运行：

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

如果使用 zip，每次更新都需要重新解压新包。

## 朋友试用时的数据写入

WebUI 当前唯一会写库的是：

```text
problem_user_state
```

也就是收藏和备注。

这意味着朋友本地收藏/备注会写入他自己的 `data/cfdb.sqlite`。如果他之后 `git pull`，SQLite 文件可能产生冲突或本地修改。

建议试用时二选一：

- 只浏览和查询，不使用收藏/备注。
- 把朋友的收藏/备注视为本地个人数据，不和主仓库同步。

后续如果要认真多人使用，应把 user state 从主 SQLite 业务库中分离，或者引入用户系统。

## 公网部署前注意事项

当前项目适合本地使用，不建议原样直接公网开放。

如果未来部署到公网，至少要考虑：

1. 不要使用 `--reload`。
2. 先运行 `npm run build`，由后端托管 `web/dist`。
3. 使用反向代理，例如 Nginx / Caddy。
4. 给服务加访问控制或登录。
5. 明确 favorite/note 是全站共享还是用户私有。
6. 给 `data/cfdb.sqlite` 做定期备份。
7. 确保部署进程对 SQLite 有写权限，但不要暴露整个仓库目录。
8. 如果多人同时写 note/favorite，评估 SQLite 锁和并发写问题。

一个更接近部署的启动方式：

```powershell
npm.cmd run build --prefix web
.venv\Scripts\python.exe -m uvicorn cfdb.web_app:app --host 127.0.0.1 --port 8765
```

公网反向代理再把外部 HTTPS 流量转到 `127.0.0.1:8765`。

## 发布前检查清单

给朋友试用前建议确认：

```powershell
git status --short
```

确认没有未提交的重要数据变更，尤其是：

```text
data/cfdb.sqlite
```

再运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; .venv\Scripts\python.exe -m unittest discover -s tests
npm.cmd run build --prefix web
```

最后 push：

```powershell
git push
```
