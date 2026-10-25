# admin/backend — AGENTS.md

> 管理后端模块导航入口（Engineering Governance 生成）。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`（项目根）。

## 职责

箓川码笺管理后台的 FastAPI 后端，本地优先读写 `site/` 下 Markdown/MDX 内容，为管理前端提供 `/api/v1` 接口。

## 结构

- `scr/`：后端源码（分层架构）
- `data/`：内容规则中心（content-schema）与运行时数据（SQLite 索引、AI 模型配置）
- `tests/`：pytest 回归测试

## 启动

```powershell
python -m uvicorn scr.main:app --reload --port 18000
```

## 入口

- 项目导航：项目根 `AGENTS.md`
- 后端规范：`admin/lc-docs/BACKEND_CONVENTION.md`
- API 主契约：`admin/docs/管理员后端接口文档.md`

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
