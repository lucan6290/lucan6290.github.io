# GitHub Pages 新前端部署实施计划

用户已明确授权切换部署、处理站点路径与文章刷新；禁止提交或推送。

## 已确认方案

- `.github/workflows/deploy.yml` 改用 Node.js 24、pnpm 10.21.0、锁文件安装及测试，构建并上传 `frontend/dist/`。
- `actions/configure-pages` 的 `base_path` 作为 Vite 构建 base；当前用户站对应 `/`，同时支持项目子路径。
- Vue Router 使用构建 base；导航 Logo 与 Markdown 内链同步处理 base，Vite 资源地址保持由构建器管理。
- 复用内容树，在 Vite 写出产物后为分类、文章、关于、内置标签/归档生成目录 `index.html`，保证静态服务可直接命中；保留 History URL。`404.html` 作为未知内容的错误入口，`.nojekyll` 避免特殊目录被过滤。
- 页面入口仅复用 SPA HTML，不声称已实现正文 SSG/SEO 预渲染。

## 执行步骤与验收

1. [ ] 先添加路径及静态入口回归测试，观察失败；实现 base 增减、路由入口生成和产物路径校验，运行全套测试。
2. [ ] 切换工作流、Router、Logo 和 Markdown 消费端；验证根路径生产构建。
3. [ ] 以非根 base 构建，在不提供 SPA fallback 的静态 HTTP 服务上检查文章 HTTP 200、刷新、中文/空格/查询/锚点、图片和搜索跳转，再验证根路径实际构建。
4. [ ] 同步 README 和内容路径契约，进行只读代码评审及 git diff --check，明确本地验证与线上发布的区别。

## 评审与执行记录

- 需求/方案评审 PASS：本会话已明确授权；部署目标由 Git remote 与 README 确认为 lucan6290.github.io。
- 契约/架构评审 PASS：逻辑内容路径不变，base 只在浏览器 URL 边界处理；静态路由列表与内容树及内置页条件一致。
- 保护工作区已有搜索实现及用户同期文档整理；不更新无关 Actions、不创建提交、不推送或触发线上部署。
