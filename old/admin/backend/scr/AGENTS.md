# scr — AGENTS.md

> 后端源码包。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`（项目根）。

## 职责

FastAPI 后端源码，分层架构，包名 `scr`（非 `app`）。

## 分层（依赖方向自上而下）

```text
api/v1/endpoints → application/workflows → services → infrastructure
```

## 子模块

- `api/`：HTTP 层
- `application/`：应用编排
- `core/`：跨切面能力（配置/鉴权/异常/日志/中间件/安全）
- `infrastructure/`：文件系统 + 注册表/SQLite
- `models/`：领域模型
- `schemas/`：DTO
- `services/`：业务能力

## 约定

- 依赖方向单向，infrastructure 不 import services。
- 入口为 `main.py`。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
