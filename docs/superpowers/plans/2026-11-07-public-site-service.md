# Public Site Service Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans with the test-driven-development skill. Verify each step in the isolated lane.

**Goal** 让静态站支持匿名评论、文章累计阅读量和管理员在线编辑 Markdown。

**Architecture** 独立 FastAPI 服务通过 SQLite 保存互动记录，在线写作复用桌面端 ContentStore。Vue 在配置服务地址后访问 API，未配置时展示明确状态。

**Tech Stack** Python 3.11+、FastAPI、SQLite、Vue 3、TypeScript、pnpm。

**Spec** [方案与契约](../specs/2026-11-07-public-site-service-design.md)

## Global Constraints

- Markdown 唯一事实源为 `frontend/content/`，服务只将静态内容清单列出的文档视为已发表。
- 写入测试使用独立临时目录，保存须基于已读取版本，部署与 Git 发布属于独立流程。
- 浏览器仅配置服务地址，管理员凭据留在服务环境和当前页面内存。
- 实现只在隔离分支提交，按文件暂存，分别提交站点互动和在线写作。

## Review Focus

- 同一会话并发访问同篇文章只加一次，不同会话和文章分别计数。
- 未审核与撤下评论不会出现在公开响应，浏览器将标签按文本呈现。
- 非规范或未发布文章标识不能产生数据库记录。
- 未认证请求、其他站点源或超大请求不能进入写入流程。
- 两个编辑器使用同一版本时，过期保存返回冲突并保留网页草稿。

## 1. 公开互动

- [x] 在 `frontend/service/tests/test_public_service.py` 写 HTTP 契约测试，先验证缺少服务时失败。
- [x] 实现 `frontend/service/public_api.py`、`interaction_store.py`，验证公开文章白名单、原子去重、审核流程和限流。
- [x] 实现 `frontend/src/api/publicService.ts` 和 `PublicArticleTools.vue`，使用浏览器验证评论和统计。
- [x] 提交公开互动的代码和相关测试。

## 2. 在线写作与集成

- [x] 增加管理员写作测试，先验证登录后的文档接口尚未实现。
- [x] 实现 `author_routes.py` 及 `PublicAdminView.vue`，验证版本冲突、六字段、路径边界和离开清除凭据。
- [x] 通过临时内容目录、真实 HTTP 及浏览器联调，再运行前端与桌面端回归。
- [x] 提交在线写作代码、测试和服务使用说明，将路由及文章挂载契约交给集成分支。

本地 Chrome 在临时 SQLite 和作者目录中验证了阅读去重、服务重启、留言超时重试与审核、纯文本显示、写作冲突和刷新清除凭据。站点管理入口在静态站部署前缀下的 `/manage-content/`，文章组件传入 `article.relativePath`。生产连接、配置和部署需要另外验证。
