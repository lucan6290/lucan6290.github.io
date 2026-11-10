# types — AGENTS.md

> TypeScript 类型定义。

## 职责

从 API Contract 派生的类型，保证跨层类型一致（`derive_types_from_contract`）。

## 内容

- `api.ts`：API 类型
- `local.ts`：本地 API 错误/重试类型
- `ai-writing.ts`：AI 写作类型

## 约定

- 契约 DTO 字段 snake_case，与后端一致。
- strict 模式，避免 `any`。

当前管理界面开发见 [桌面前端开发规范](../../../../../admin-desktop/src/AGENTS.md)。
