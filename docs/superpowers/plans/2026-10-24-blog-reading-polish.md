# 阅读体验维护计划

> 当前修订：2026-10-29。作为现有能力的复核清单；新修改仍须取得本次任务的明确授权。

设计依据：[视觉与阅读体验规范](../../PRD/博客视觉与阅读体验完善方案.md)。工程约束：[全局规范](../../GLOBAL_STANDARDS.md)。

## 当前实现入口

- 正文与文章头部：`frontend/src/components/article/MarkdownRenderer.vue`、`frontend/src/views/ArticleView.vue`。
- 响应式栏目目录：`frontend/src/components/sidebar/ResizableSidebar.vue`。
- 右下角目录：`frontend/src/components/toc/FloatToc.vue`。
- 导航与列表：`frontend/src/components/layout/Navbar.vue`、`frontend/src/components/list/ArticleList.vue`。

## 复核步骤

1. 对照同一篇长文的桌面与窄屏，检查字号、换行、代码、表格和图片。
2. 检查手机目录默认状态、展开收起和路由切换；桌面调宽偏好不污染手机状态。
3. 检查二三级标题的目录收集、章节跳转、Esc 关闭、焦点恢复与减少动态效果。
4. 检查知识库、博客、项目共用组件的导航与阅读行为。
5. 根据实际修改运行相关测试、构建和浏览器验证，记录本次结果。

## 状态说明

上述能力已有实现；本次文档核对不代表重新执行了所有交互验证，也不提供通用的提交、推送或发布授权。主题遵循当前蓝色规范。
