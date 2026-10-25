# src — AGENTS.md

> 站点源码目录。详细规范见 `site/lc-docs/FRONTEND_CONVENTION.md`。

## 子模块

- `components/`：自定义 React 组件
- `pages/`：页面（首页/about/projects）
- `theme/`：Docusaurus 主题 swizzle 覆写
- `css/`：全局样式

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `site/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
