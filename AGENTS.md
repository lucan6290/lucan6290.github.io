# AGENTS.md

本文件是箓川码笺的开发导航。先定位任务，再读取相应入口与模块规范。

## 项目结构

| 模块 | 职责 | 入口 |
| --- | --- | --- |
| `frontend/` | Vite + Vue + TypeScript 读者站点 | [前端说明](frontend/README.md) |
| `frontend/content/` | 站点和桌面 App 共用的 Markdown 内容事实源 | [内容写作指南](docs/SITE_CONTENT_GUIDE.md) |
| `admin-desktop/` | Tauri 2 + Vue 3 桌面管理 App | [桌面端开发导航](admin-desktop/AGENTS.md) |
| `admin-desktop/src-backend/` | 本地 Python/FastAPI 内容服务 | [桌面后端规范](admin-desktop/src-backend/AGENTS.md) |
| `frontend/service/` | 可选的公开互动和在线写作服务 | [互动服务规范](frontend/service/AGENTS.md) |
| `old/` | 历史归档 | [当前工程文档索引](docs/DOCUMENTATION_INDEX.md) |

## 任务入口

| 任务 | 先读 |
| --- | --- |
| 站点页面、构建与搜索 | [前端说明](frontend/README.md)、[工程文档索引](docs/DOCUMENTATION_INDEX.md) |
| 站点内容及元信息 | [内容写作指南](docs/SITE_CONTENT_GUIDE.md) |
| 桌面界面、原生层及内容后端 | [桌面端开发导航](admin-desktop/AGENTS.md)、[桌面端文档索引](admin-desktop/docs/DOCUMENTATION_INDEX.md) |
| 桌面内容接口或写入行为 | [内容接口契约](admin-desktop/docs/内容接口契约.md) |
| 站点互动和在线写作 | [互动服务规范](frontend/service/AGENTS.md)、[服务说明](frontend/service/README.md) |

先核对现有组件、服务和工作流，有可复用实现时优先复用。接口变更以对应模块契约为准，并同步实现与验证。新增业务模块时补齐该模块的 `AGENTS.md` 并登记到对应文档索引与本文件的任务入口。

跨层或多阶段改动按需准备需求、方案和契约。按需求、方案、契约、架构、实现、集成与代码的顺序评审，每级通过后进入下一阶段。单文件小改动可跳过方案文档。

新建 `frontend/content/` 下的普通文章时，按内容指南使用固定顺序的 `title`、`date`、`updated`、`description`、`tags`、`sticky`。新建时两个时间相同，使用真实的 `YYYY-MM-DDTHH:mm:ss+08:00`。首次写作时间 `date` 创建后保持不变，修改正文或元信息时更新 `updated`。目录介绍 README、工程说明和设计文档可使用各自格式。

目录即导航。修改 Markdown 或目录后，开发模式重新生成内容并触发 HMR，生产构建通过 `pnpm prebuild` 生成内容。禁止手动编辑 `frontend/src/generated/`。

## 本地开发

| 模块 | 工作目录 | 命令与端口 |
| --- | --- | --- |
| 读者站点 | `frontend/` | `pnpm dev`，`http://127.0.0.1:3400/`。依赖用 `pnpm install`，构建用 `pnpm build` |
| 桌面 App | `admin-desktop/` | `npm run tauri:dev`，Vite 界面使用 `http://127.0.0.1:14200/`，原生应用自动启动内容服务 |
| 桌面内容服务 | 仓库根目录 | 浏览器联调时执行 `python admin-desktop/src-backend/main.py --project-root . --port 18000 --reload`，另在 `admin-desktop/` 执行 `npm run dev` |
| 站点互动服务 | `frontend/service/` | 见 [服务说明](frontend/service/README.md) |

启动前先检查固定开发端口。被本项目的旧进程占用时，确认进程身份后停止对应进程，再按原端口启动。桌面 App 启动的内容后端优先用 18000，冲突时使用系统分配的回环端口。站点开发与构建预览共用 3400。桌面环境准备与连接步骤见 [桌面端说明](admin-desktop/README.md#开发启动)。
