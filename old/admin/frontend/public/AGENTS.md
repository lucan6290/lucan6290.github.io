# public — AGENTS.md

> 前端静态资源目录。详细规范见 `admin/lc-docs/FRONTEND_CONVENTION.md`。

## 职责

不经构建直接拷贝到输出目录的静态资源。

## 内容

- `favicon.svg`：站点图标
- `icons.svg`：图标集

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
