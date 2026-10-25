# src — AGENTS.md

> 前端源码目录。详细规范见 `admin/lc-docs/FRONTEND_CONVENTION.md`。

## 职责

管理前端源码，按职责分目录。

## 子模块

- `api/`：后端调用层
- `assets/`：静态资源
- `components/`：组件
- `plugins/`：插件
- `stores/`：Pinia 状态
- `types/`：TS 类型
- `utils/`：工具
- `views/`：页面

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
