# views — AGENTS.md

> 页面视图。详细规范见 `admin/lc-docs/FRONTEND_CONVENTION.md` 第 5 节。

## 职责

编排组件与数据流，对应路由页面。

## 内容

- `Login.vue`：登录
- `Dashboard.vue`：仪表盘
- `Posts.vue`：文章列表
- `Editor.vue`：编辑器
- `Registry.vue`：内容注册表
- `AIWriting.vue`：AI 写作
- `Media.vue`：媒体
- `Settings.vue`：设置
- `Home.vue`：首页

## 约定

- 路由映射见 `src/router.ts`（hash，base `/admin/`）。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
