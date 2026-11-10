# components — AGENTS.md

> 通用/业务组件。

## 职责

可复用组件，只做视图渲染/局部状态/事件处理，不承载跨页业务逻辑。

## 内容

- `AIAssistant.vue`：AI 助手
- `NewPostModal.vue`：新建文章弹窗
- `ai-writing/`：AI 写作子组件

## 约定

- 组件命名 PascalCase。
- Composition API + `<script setup>`。

当前管理界面开发见 [桌面前端开发规范](../../../../../admin-desktop/src/AGENTS.md)。
