# api — AGENTS.md

> 后端调用层。详细规范见 `admin/lc-docs/FRONTEND_CONVENTION.md` 第 2.5/2.6 节。

## 职责

统一封装后端 `/api/v1` 调用，禁止在各 view 散写 axios。

## 内容

- `local.ts`：`LocalAPIClient`（axios 封装、鉴权头、重试、错误映射）
- `index.ts`：导出 `BlogAPI` 类型与入口

## 约定

- 契约 DTO 字段 snake_case，与后端一致。
- 展示类型映射仅单接口显式映射，不做全局运行时转换。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
