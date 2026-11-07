# 工程文档索引

> 更新日期：2026-11-07。适用范围：`frontend/` 工程、Markdown 内容和可选互动服务。

## 阅读顺序

1. 从 [frontend/README.md](../frontend/README.md) 了解启动、目录和写作方式。
2. 阅读 [全局规范](GLOBAL_STANDARDS.md)，确认修改权限、开发原则与验证要求。
3. 按任务读取下表中的文档和源码入口。

用户最新指令优先。工程文档应与当前实现同步；发现冲突时核对源码并说明差异，不为过时文档或历史数据增加兼容分支。根目录 [AGENTS.md](../AGENTS.md) 是 Agent 导航入口，其路径引用也应与本索引保持一致。

## 当前工程规范

| 文档 | 职责 | 何时更新 |
| --- | --- | --- |
| [GLOBAL_STANDARDS.md](GLOBAL_STANDARDS.md) | 三种体验、权限、Git、验证和运行约束 | 公共约束变化 |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 当前目录与源码职责 | 目录、模块或入口变化 |
| [FRONTEND_CONVENTION.md](FRONTEND_CONVENTION.md) | 页面、导航、样式、搜索和交互 | 前端行为与组件职责变化 |
| [SITE_CONTENT_GUIDE.md](SITE_CONTENT_GUIDE.md) | Markdown、图片、分类和本文目录 | 内容规则变化 |
| [API_CONTRACT.md](API_CONTRACT.md) | 内容清单、路径和搜索数据契约 | 字段、路由或生成数据变化 |
| [BACKEND_CONVENTION.md](BACKEND_CONVENTION.md) | 静态前端、可选互动服务的边界 | 引入或变更后端时 |
| [互动服务说明](../frontend/service/README.md) | 互动服务配置、运行、测试与发布边界 | 改动评论、阅读量或在线写作时 |

## 按任务定位

| 任务 | 先读 | 实现入口 |
| --- | --- | --- |
| 添加文章、项目或工具介绍 | [内容指南](SITE_CONTENT_GUIDE.md) | `frontend/content/` |
| 调整分类和导航 | [前端约定](FRONTEND_CONVENTION.md) | `CategoryView.vue`、`contentPaths.ts`、`nav.ts` |
| 调整文章和图片渲染 | [内容契约](API_CONTRACT.md) | `ArticleView.vue`、`MarkdownRenderer.vue` |
| 调整右下角本文目录 | [前端约定](FRONTEND_CONVENTION.md) | `FloatToc.vue` |
| 调整读者搜索 | [内容契约](API_CONTRACT.md) | `search.ts`、`SearchDialog.vue`、`buildContent.mjs` |
| 评论、阅读量与在线写作 | [互动服务规范](../frontend/service/AGENTS.md) | `frontend/service/`、`PublicArticleTools.vue`、`PublicAdminView.vue` |
| 修改主题与响应式布局 | [前端约定](FRONTEND_CONVENTION.md) | `tokens.css`、`base.css`、对应组件 |
| 排查内容更新 | [工程结构](PROJECT_STRUCTURE.md) | `contentManifestPlugin.ts`、`buildContent.mjs` |
| 构建与发布 | [README](../frontend/README.md) | `frontend/package.json`、`.github/workflows/deploy.yml` |

完整源码相对路径见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)。

## PRD 与专题方案

`PRD/` 的 12 份文档已按当前目录、内容规则和产品状态修订。工程字段和命令仍以根目录规范及源码为准，不能将方案中的后续需求直接认定为已实现。

- [个人技术站自研需求基线](PRD/个人技术站自研需求基线.md)
- [博客架构与长期发展规划](PRD/2026-05-23-博客架构与长期发展规划.md)
- [内容规划规则](<PRD/Docs 与 Blog 内容规划规则.md>)
- [AI 内容归档准则](<PRD/site AI 内容归档准则.md>)
- [文件维护准则](PRD/文件维护准则.md)
- [新增文章同步维护规范](PRD/新增文章同步维护规范.md)
- [Markdown 文件夹展示方案](PRD/2026-10-23-Markdown文件夹展示实施计划.md)
- [知识库分类层级记录](PRD/2026-10-23-知识库分类层级实施记录.md)
- [顶部栏目目录驱动方案](PRD/2026-10-23-顶部栏目目录驱动实施计划.md)
- [视觉与阅读体验方案](PRD/博客视觉与阅读体验完善方案.md)
- [蓝色主题方案](PRD/博客蓝色主题调整方案.md)
- [GitHub 交互设计](PRD/Github交互设计.md)

## 实施计划

`superpowers/plans/` 用于任务执行记录和当前复核清单。视觉、阅读与主题计划已对齐当前实现，搜索和部署计划按对应任务记录实际进展。计划中的授权、勾选项和测试结果仅属于对应任务，不能用作其他任务的修改、提交或发布授权。

- [阅读体验计划](superpowers/plans/2026-10-24-blog-reading-polish.md)
- [视觉优化计划](superpowers/plans/2026-10-24-blog-visual-refresh.md)
- [蓝色主题计划](superpowers/plans/2026-10-24-blue-theme.md)
- [读者搜索计划](superpowers/plans/2026-10-29-reader-search.md)
- [GitHub Pages 部署计划](superpowers/plans/2026-10-29-github-pages-frontend.md)

## 维护方式

- 当前规范只维护当前工程，不添加历史工程启动教程或历史数据兼容要求。
- 修改某条规则时更新负责该规则的文档，其他文档链接过去，减少多处冲突。
- 用当前源码与新规范样例验证文档；文件路径和相对链接必须可定位。
- 文档修订与代码完成、线上发布是不同状态，不以文档描述代替验证证据。
