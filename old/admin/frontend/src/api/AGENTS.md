# api — AGENTS.md

> 后端调用层。

## 职责

统一封装后端 `/api/v1` 调用，禁止在各 view 散写 axios。

## 内容

- `local.ts`：`LocalAPIClient`（axios 封装、鉴权头、重试、错误映射）
- `index.ts`：导出 `BlogAPI` 类型与入口

## 约定

- 契约 DTO 字段 snake_case，与后端一致。
- 展示类型映射仅单接口显式映射，不做全局运行时转换。

当前管理界面开发见 [桌面前端开发规范](../../../../../admin-desktop/src/AGENTS.md)。
