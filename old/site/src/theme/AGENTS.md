# theme — AGENTS.md

> Docusaurus 主题 swizzle 覆写。详细规范见 `site/lc-docs/FRONTEND_CONVENTION.md` 第 3.3 节。

## 职责

覆写 Docusaurus 默认主题组件，不改 `node_modules` 内主题源码。

## 内容（swizzle 组件）

- `BlogSidebar/`：博客侧边栏
- `DocRoot/`：文档根（含 Layout/Sidebar/ExpandButton）
- `DocSidebar/`：文档侧边栏（含 Desktop/CollapseButton）
- `Footer/`：页脚

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `site/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
