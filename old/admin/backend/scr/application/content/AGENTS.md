# application/content — AGENTS.md

> 内容应用编排层。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

内容域的跨能力编排。

## 子模块

- `workflows/`：文章/分类创建等工作流。

## 约定

- 编排调用 services，不直接触碰 infrastructure。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
