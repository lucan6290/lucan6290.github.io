# api/v1 — AGENTS.md

> v1 路由聚合层。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

聚合各业务端点路由到 `/v1` 前缀。

## 内容

- `router.py`：APIRouter 聚合，include 各端点。
- `dependencies.py`：服务工厂（`get_xxx_service` + `lru_cache`）。
- `responses.py`：`COMMON_ERROR_RESPONSES` 公共错误响应。
- `endpoints/`：各业务端点。

## 约定

- 完整路径 `/api/v1/<resource>`。
- 依赖注入经 FastAPI `Depends` + `dependencies.py`。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
