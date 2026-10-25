# api — AGENTS.md

> HTTP 层入口。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

API 路由入口，仅含版本目录。

## 子模块

- `v1/`：v1 版本路由。

## 约定

- 统一前缀 `/api`（由 `main.py` 引入）。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
