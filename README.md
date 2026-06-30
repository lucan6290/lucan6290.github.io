# 箓川码笺

> 个人技术站与知识库系统 —— 基于 Docusaurus 的公开站点 + 自建管理后台。

站点地址：<https://lucan6290.github.io>

## 项目简介

箓川码笺（xiaocancoding）是一套长期维护的个人技术站，定位为内容展示与写作管理一体化：

- **site**：基于 Docusaurus 的公开站点，承载博客、知识库、项目展示等内容，面向读者。
- **admin**：自建内容管理后台，提供文章写作、编辑、图片管理、分类标签维护、预览构建等写作辅助能力，面向作者。
- **docs**：项目整体规划、设计记录与协作说明。

## 目录结构

```text
xiaocancoding/
├── site/                      # Docusaurus 公开站点
│   ├── blog/                  # 博客文章（随笔、复盘、更新记录）
│   ├── docs/                  # 长期知识库 / 系列教程
│   ├── src/                   # 页面、组件、主题覆写、样式
│   ├── static/                # 静态资源（图片、图标、封面）
│   ├── docusaurus.config.ts   # 站点配置
│   └── sidebars.ts            # 侧边栏配置
├── admin/
│   ├── frontend/              # 管理后台前端（Vue 3 + Vite）
│   ├── backend/               # 管理后台后端（FastAPI）
│   │   └── data/content-schema/   # 分类 / 标签 / 模板等内容规则中心
│   └── docs/                  # 管理端设计与接口文档
└── docs/                      # 项目整体规划文档
```

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 站点（site） | Docusaurus 3、React 19、TypeScript |
| 管理后台前端 | Vue 3、Vite、Naive UI、Pinia、ByteMD |
| 管理后台后端 | FastAPI、Uvicorn、Pydantic、PyYAML |

## 快速开始

### 1. 克隆仓库

```bash
git clone -b develop https://github.com/lucan6290/lucan6290.github.io.git
cd lucan6290.github.io
```

### 2. 启动站点（site）

```bash
cd site
npm install
npm run dev        # 本地访问 http://127.0.0.1:3400
```

常用命令：

| 命令 | 说明 |
| --- | --- |
| `npm run dev` | 本地开发服务器（127.0.0.1:3400） |
| `npm run build` | 构建生产产物到 `build/` |
| `npm run serve` | 本地预览构建结果 |
| `npm run clear` | 清理 Docusaurus 缓存 |

### 3. 启动管理后台（admin）

后端（FastAPI，端口 18000）：

```bash
cd admin/backend
python -m venv .venv
# Windows
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe main.py
```

前端（Vue，端口 14000）：

```bash
cd admin/frontend
npm install
npm run dev        # 本地访问 http://127.0.0.1:14000
```

也可在 `admin/frontend` 下执行 `npm run dev:all` 一键拉起前后端。

## 内容规则

内容规范集中在 [admin/backend/data/content-schema/](admin/backend/data/content-schema/)，包含分类体系、标签、Front Matter 模板等，由管理端后端读写、站点侧遵循。

## 说明

- `site/screenshots/` 为开发调试截图，非站点运行必需资源。
- 依赖目录（`node_modules/`、虚拟环境）已通过 `.gitignore` 忽略，拉取后按上述步骤安装即可。
