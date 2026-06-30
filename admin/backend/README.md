# Admin Backend

本地优先的 Docusaurus 内容管理后端，基于 FastAPI + Pydantic v2。
详细设计与接口契约见 `admin/docs/管理员后端技术设计.md` 与 `admin/docs/管理员后端接口文档.md`。

## 1. 环境要求

- Python 3.10+
- 推荐使用 Conda 虚拟环境（见全局开发规范）

## 2. 安装依赖

```powershell
cd E:\A-Code\xiaocancoding\admin\backend
python -m pip install -r requirements.txt
```

## 3. 启动服务

> **关键：必须在 `admin/backend/` 目录下、以模块方式（`-m`）启动。**
> `scr` 是 src-layout 包，代码中大量使用 `from scr...` 的包级绝对导入，只有以 `-m` 方式启动、并位于 `admin/backend/` 时，`scr` 包才能被正确解析。

推荐方式（支持热重载）：

```powershell
cd E:\A-Code\xiaocancoding\admin\backend
python -m uvicorn scr.main:app --reload --port 18000
```

或使用内置入口（等效，默认监听 `127.0.0.1:18000`）：

```powershell
python -m scr.main
```

启动成功后可访问：

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:18000/api/v1/health | 健康检查 |
| http://127.0.0.1:18000/docs | OpenAPI 交互文档 |
| http://127.0.0.1:18000/openapi.json | OpenAPI Schema |

## 4. 常见问题

### `ModuleNotFoundError: No module named 'scr'`

原因：运行目录不在 `admin/backend/`，或使用了 `python main.py` / `python scr/main.py` 这类直接执行脚本的方式。直接执行脚本会把脚本所在目录（`scr/`）放进 `sys.path`，而非其父目录 `backend/`，导致 `scr` 包找不到。

解决：回到 `admin/backend/`，改用 `python -m uvicorn scr.main:app --reload` 或 `python -m scr.main`。

### `python main.py` 执行后没反应 / 直接退出

`scr/main.py` 本身只定义了 `app` 对象，需通过 uvicorn 加载，或用 `python -m scr.main`（已内置入口）。直接 `python main.py` 不会启动 HTTP 服务。

### `No module named uvicorn`

未安装依赖，执行 `python -m pip install -r requirements.txt`。

## 5. 配置项

通过环境变量覆盖默认值：

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `LUCHUAN_PROJECT_ROOT` | 自动从源码位置回溯 4 层 | 项目根目录 |
| `LUCHUAN_ENV` | `local` | 运行环境，用于 `/health` 的 `environment` 字段 |
| `LUCHUAN_LOG_LEVEL` | `INFO` | 日志级别 |
| `LUCHUAN_CORS_ORIGINS` | admin 前端 14000 / Vite 5173 / Next 3000 等 6 个本地源 | 允许跨域的前端来源（逗号分隔），覆盖默认白名单 |
| `LUCHUAN_REGISTRY_INDEX_PATH` | `admin/backend/data/registry_index.sqlite3` | SQLite 注册表索引库路径；YAML/Markdown 仍是源文件，SQLite 仅用于后台搜索、分页、排序和统计 |

PowerShell 下设置环境变量示例（仅当前会话生效）：

```powershell
$env:LUCHUAN_ENV = "dev"
python -m uvicorn scr.main:app --reload
```

## 6. SQLite 注册表索引

后台提供可重建的 SQLite 管理索引，不取代 `admin/backend/data/content-schema/*.yml` 和 Markdown 源文件。需要搜索、分页、排序、统计时，先同步索引：

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:18000/api/v1/registry-index/sync
```

常用接口：

| 地址 | 说明 |
| --- | --- |
| `POST /api/v1/registry-index/sync` | 从 YAML 与 Markdown 重建 SQLite 索引 |
| `GET /api/v1/registry-index/entities?entity_type=category&q=Java&page=1&page_size=20` | 查询分类、标签、文章等通用实体 |
| `GET /api/v1/registry-index/stats` | 查看索引统计与最近同步状态 |
| `GET /api/v1/registry-index/yaml/categories` | 查看 YAML 注册表原文 |
| `PUT /api/v1/registry-index/yaml/categories` | 保存 YAML 原文并重建索引 |
| `GET /api/v1/registry-index/yaml/categories/entries` | 查看 YAML 条目列表，用于表单维护 |
| `PUT /api/v1/registry-index/yaml/categories/entries` | 保存 YAML 条目列表并重建索引 |
| `GET /api/v1/registry-index/diff/categories` | 检查 YAML 注册表与 SQLite 索引差异 |
