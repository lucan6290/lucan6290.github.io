# types — AGENTS.md

> TypeScript 类型定义。详细规范见 `admin/lc-docs/FRONTEND_CONVENTION.md` 第 2.6 节。

## 职责

从 API Contract 派生的类型，保证跨层类型一致（`derive_types_from_contract`）。

## 内容

- `api.ts`：API 类型
- `local.ts`：本地 API 错误/重试类型
- `ai-writing.ts`：AI 写作类型

## 约定

- 契约 DTO 字段 snake_case，与后端一致。
- strict 模式，避免 `any`。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
