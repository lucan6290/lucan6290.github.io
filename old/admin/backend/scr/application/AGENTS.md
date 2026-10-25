# application — AGENTS.md

> 应用编排层。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

跨文件、跨服务、有回滚要求的应用层编排，位于 HTTP 层与业务服务层之间。

## 子模块

- `content/`：内容编排。

## 约定

- 编排逻辑放此处，不放到 endpoints 或 services。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
