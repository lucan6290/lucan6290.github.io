# components — AGENTS.md

> 通用/业务组件。详细规范见 `admin/lc-docs/FRONTEND_CONVENTION.md` 第 5/6 节。

## 职责

可复用组件，只做视图渲染/局部状态/事件处理，不承载跨页业务逻辑。

## 内容

- `AIAssistant.vue`：AI 助手
- `NewPostModal.vue`：新建文章弹窗
- `ai-writing/`：AI 写作子组件

## 约定

- 组件命名 PascalCase。
- Composition API + `<script setup>`。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
