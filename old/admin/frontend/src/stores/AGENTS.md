# stores — AGENTS.md

> Pinia 状态管理。详细规范见 `admin/lc-docs/FRONTEND_CONVENTION.md` 第 2.4 节。

## 职责

全局共享状态；页面局部状态用组件内 `ref`/`reactive`。

## 内容

- `aiConfig.ts`：AI 配置
- `aiWriting.ts`：AI 写作
- `categories.ts`：分类
- `knowledgeIndex.ts`：知识索引
- `posts.ts`：文章
- `settings.ts`：设置

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
