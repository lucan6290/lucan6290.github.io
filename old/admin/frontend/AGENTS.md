# admin/frontend — AGENTS.md

> 管理前端模块导航入口（Engineering Governance 生成）。详细规范见 `admin/lc-docs/FRONTEND_CONVENTION.md`（项目根）。

## 职责

箓川码笺管理后台前端（Vue 3 + Vite + Naive UI + Pinia + ByteMD），base `/admin/`，为作者提供文章写作/编辑/管理界面。

## 结构

- `public/`：静态资源
- `src/`：前端源码

## 启动

```powershell
npm run dev
```

访问 `http://127.0.0.1:14000/admin/`。

## 入口

- 项目导航：项目根 `AGENTS.md`
- 前端规范：`admin/lc-docs/FRONTEND_CONVENTION.md`
- API 主契约：`admin/docs/管理员后端接口文档.md`

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
