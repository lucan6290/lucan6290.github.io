# AGENTS.md

> 本文件是项目的导航入口（Agent 的第一张地图），不是规范百科。详细规范按任务类型逐级加载到 `admin/lc-docs/`、`site/lc-docs/` 与 `admin/docs/`。

## Project Overview

箓川码笺（xiaocancoding）：个人技术站与知识库系统，自研前端 + Docusaurus 旧站 + 自建内容管理后台的单仓全栈项目。

| 工程 | 技术栈 | 状态 |
| --- | --- | --- |
| `frontend/` | Vite 6 + Vue 3.5 + TypeScript + ByteMD | **新自研前端（开发中）** |
| `admin-desktop/` | Tauri 2 + Vue 3 + 独立 FastAPI 内容服务 | 当前桌面管理端，管理 `frontend/content/` |
| `site/` | Docusaurus 3 + React 19 + TypeScript | 旧站（逐步被 frontend 替代） |
| `admin/frontend/` | Vue 3 + Vite + Naive UI + Pinia + ByteMD | 管理端前端 |
| `admin/backend/` | FastAPI + Pydantic v2 + PyYAML + Python 3.10 | 管理端后端 |

关键约束：
- 本地优先，**新前端以 `frontend/content/` 下 Markdown 为唯一内容事实源**（目录即导航，零配置）；旧站仍以 `site/blog/`、`site/docs/` 为事实源。
- 四端口固定，见下方「本地开发规范」。
- `frontend/` 与 `site/` 共用 3400 端口，**不得同时运行**。

## Before Coding（开发前必读）

1. **先发现规范**：新前端读 `frontend/README.md`；管理端读 `admin/lc-docs/`；旧站点读 `site/lc-docs/`（均含 `PROJECT_STRUCTURE`、`GLOBAL_STANDARDS`、`FRONTEND_CONVENTION`；管理端另有 `BACKEND_CONVENTION`、`API_CONTRACT`，站点端另有 `SITE_CONTENT_GUIDE`）。
2. **先看路由**：确定改动属于新前端 / 旧站点 / 管理前端 / 管理后端，按对应约定执行。
3. **先查复用**：新增能力前先搜 `services/`、`workflows/` 是否有可复用实现，不重复造轮子。
4. **先看契约**：涉及接口改动先读 `admin/docs/管理员后端接口文档.md`（API 主契约）。
5. **新前端内容管线**：改 `frontend/content/` 下的 MD 或目录结构后，dev 模式自动重跑 `scripts/build-content.mjs` 并触发 HMR；生产构建由 `pnpm prebuild` 触发。**不要手动编辑 `src/generated/`**（gitignore，构建产物）。

## Project Structure

完整目录见 `admin/lc-docs/PROJECT_STRUCTURE.md`（管理端）或 `site/lc-docs/PROJECT_STRUCTURE.md`（站点端）。核心入口：

- **新前端内容事实源**：`frontend/content/`（目录即分类页，`.md` 即内容页，任意嵌套）
- **新前端代码**：`frontend/src/`（组件 / 视图 / composables / 样式）
- **新前端内容管线**：`frontend/scripts/build-content.mjs` → 输出 `frontend/src/generated/`
- 旧站内容：`site/blog/`、`site/docs/`（逐步迁移到 `frontend/content/`）
- 管理前端：`admin/frontend/src/`
- 管理后端：`admin/backend/scr/`
- 内容规则：`admin/backend/data/content-schema/`

## Task Routing

| 任务类型 | 对应模块 / 文档 |
| --- | --- |
| 运行服务 | 下方「本地开发规范」 |
| **新前端开发** | `frontend/README.md` → `frontend/src/` |
| **新前端内容写作** | 先读 `docs/SITE_CONTENT_GUIDE.md`（统一 YAML 六字段与时间语义）→ `frontend/content/`（零配置，目录即导航） |
| **桌面管理端开发** | `admin-desktop/AGENTS.md` → `admin-desktop/docs/DOCUMENTATION_INDEX.md` |
| **桌面内容接口变更** | `admin-desktop/docs/内容接口契约.md`（独立契约，不使用旧站接口） |
| 后端开发 | 后端模块 `AGENTS.md` → `admin/lc-docs/BACKEND_CONVENTION.md` |
| 管理前端开发 | 前端模块 `AGENTS.md` → `admin/lc-docs/FRONTEND_CONVENTION.md` |
| 旧站点开发 | 站点模块 `AGENTS.md` → `site/lc-docs/FRONTEND_CONVENTION.md` |
| 接口变更 | `admin/lc-docs/API_CONTRACT.md` + `admin/docs/管理员后端接口文档.md` |
| 内容工作流 | `admin/docs/内容工作流接口说明.md` |

> 逐级加载：`admin/backend/`、`admin/frontend/` 与 `site/`（代码目录）下均有模块级 `AGENTS.md`（导航入口），改后端/前端/站点时先读目标目录的 `AGENTS.md`，再按需读对应 `admin/lc-docs/` 或 `site/lc-docs/` 章节。完整层级见 `admin/lc-docs/DOCUMENTATION_INDEX.md`（管理端）或 `site/lc-docs/DOCUMENTATION_INDEX.md`（站点端）。
>
> **模块 AGENTS.md 维护**：新增前端/后端/站点模块（目录）时，必须同步生成该目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md`（管理端）或 `site/lc-docs/DOCUMENTATION_INDEX.md`（站点端）的层级索引与本文档 Task Routing。

## Required Documentation（开发前必须产出的文档）

涉及多阶段/跨层改动时，按需产出：需求 → 方案（前后端）→ 契约 → 评审。单文件小改动可跳过。

新建 `frontend/content/` 下的普通 Markdown 文章时，必须按 `docs/SITE_CONTENT_GUIDE.md` 使用固定顺序的 `title`、`date`、`updated`、`description`、`tags`、`sticky` 六字段 YAML。`date` 为首次开始写作时间，创建后不变；修改正文或元信息时更新 `updated`。新建时两个时间相同，使用真实的 `YYYY-MM-DDTHH:mm:ss+08:00` 时间字符串。目录介绍 README、工程说明和设计文档不要求套用文章模板。

## Contract Requirement（契约要求）

- API 主契约：`admin/docs/管理员后端接口文档.md`。
- OpenAPI 快照：`/docs`、`/openapi.json`（后端实现需向主契约对齐）。
- 契约约定汇总：`admin/lc-docs/API_CONTRACT.md`。

## Reuse Requirement（复用要求）

- 新增前先做 Existing Implementation Discovery：`services/`（业务能力）、`application/content/workflows/`（编排）、`infrastructure/`（基础能力）。
- 能复用的不新建；必须新建时说明现有实现为何不满足。

## Review Requirement（评审要求）

多阶段评审闸门：需求评审 → 方案评审（前后端，可并行）→ 契约评审 → 架构评审 → 实现 → 集成评审 → 代码评审。每级未 PASS 不得进入下一阶段。

## Documentation Index

- **新前端文档**：`frontend/README.md`
- **新前端内容写作规范**：`docs/SITE_CONTENT_GUIDE.md`（新文章必读，包含统一 YAML 模板）
- **桌面端文档**：`admin-desktop/docs/DOCUMENTATION_INDEX.md`（含前端、独立后端、测试与原生模块导航）
- 管理端工程治理文档：`admin/lc-docs/DOCUMENTATION_INDEX.md`
- 旧站点工程治理文档：`site/lc-docs/DOCUMENTATION_INDEX.md`
- 管理端设计/接口文档：`admin/docs/`
- 项目规划文档：`docs/`（含 `docs/个人技术站自研需求基线.md`）
- 项目说明：`README.md`

---

# 本地开发规范

## 运行端口

- **新前端**必须运行在 `http://127.0.0.1:3400/`。
- **旧站前端**必须运行在 `http://127.0.0.1:3400/`（与新前端共用端口，**不得同时运行**）。
- 管理前端必须运行在 `http://127.0.0.1:14000/admin/`，端口固定使用 `14000`。
- 管理后端必须运行在 `http://127.0.0.1:18000/`，端口固定使用 `18000`。
- 当前环境为本地开发，不要为了规避端口占用改用其他端口。

## 新前端（frontend）

- 工作目录：`frontend`
- 包管理器：**pnpm**
- 安装依赖：`pnpm install`
- 启动命令：`pnpm dev`（自动先跑 `scripts/build-content.mjs`）
- 访问地址：`http://127.0.0.1:3400/`
- 构建命令：`pnpm build`（输出到 `dist/`）
- 内容事实源：`frontend/content/`（新建目录/文件即自动出现在导航，零配置）
- 顶部导航映射：`frontend/src/config/nav.ts`
- 生成产物：`frontend/src/generated/`（gitignore，勿手动编辑）
- 如果 `3400` 端口被占用，必须先清理占用进程，再启动。
- 不允许临时改成 `3401`、`5173` 或其他端口运行新前端。

PowerShell 检查与清理示例：

```powershell
netstat -ano | Select-String ':3400'
Stop-Process -Id <PID> -Force
```

## 旧站前端（site，逐步弃用）

- 工作目录：`site`
- 启动命令：`npm run dev`
- 访问地址：`http://127.0.0.1:3400/`（与新前端共用端口，**不得同时运行**）
- 仅在需要对照旧站视觉 / 迁移内容时启动。

## 管理前端

- 工作目录：`admin/frontend`
- 启动命令：`npm run dev`
- 访问地址：`http://127.0.0.1:14000/admin/`
- 管理前端本地开发必须使用热更新启动，即使用 `npm run dev`。
- 管理前端端口必须固定为 `14000`。
- 不允许临时改成其他端口运行管理前端。

PowerShell 检查与清理示例：

```powershell
netstat -ano | Select-String ':14000'
Stop-Process -Id <PID> -Force
```

## 管理后端

- 工作目录：`admin/backend`
- Python 环境：`python310`
- 启动命令：`python -m uvicorn scr.main:app --reload --port 18000`
- 访问地址：`http://127.0.0.1:18000/`
- 后端本地开发必须使用热更新启动，即必须保留 `--reload`。
- 管理后端端口必须固定为 `18000`。
- 不允许临时改成其他端口运行管理后端。

PowerShell 检查与清理示例：

```powershell
netstat -ano | Select-String ':18000'
Stop-Process -Id <PID> -Force
```

## 执行要求

- 启动前先确认目标端口是否被占用。
- 若端口被旧的本项目开发服务占用，先停止旧进程，再按固定端口启动。
- 不修改 `site/build`、`site/.docusaurus` 等构建产物来解决端口问题。
