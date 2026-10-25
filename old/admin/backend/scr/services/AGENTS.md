# services — AGENTS.md

> 业务能力服务层。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

承载业务逻辑，按业务域划分；单一文件/单一规则维护放这里。

## 子模块

- `ai/`：AI 写作辅助
- `content/`：内容业务服务
- `site/`：构建/部署/Git 同步

## 约定

- 依赖 `infrastructure/`，被 `application/workflows/` 编排。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
