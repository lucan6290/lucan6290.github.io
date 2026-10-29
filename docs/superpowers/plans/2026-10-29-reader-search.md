# 读者全文搜索实施计划

> 使用 executing-plans 执行本搜索任务，按 TDD 顺序验证。用户对此搜索任务已明确授权“按这个方案开始实施”；授权仅限对应任务。不提交、不推送，发布配置另作任务。文档于 2026-10-29 核对当前引用。

**Goal:** 新前端读者可从顶部入口搜索中文、英文标题、标签、摘要和正文，并进入文章。

**Architecture:** 复用内容构建管线输出的 search-index.json。原生 dialog 提供模态搜索窗口；打开后动态导入 MiniSearch 和索引，无后端依赖。检索工具使用中文单字及相邻双字索引、英文单词，查询采用 AND，英文允许前缀匹配，标题权重最高。

**Tech Stack:** Vue 3、TypeScript、已有 MiniSearch 7、Node 内置测试。

**Spec:** 对应搜索任务的已确认方案；当前行为见 [前端约定](../../FRONTEND_CONVENTION.md)，数据字段见 [内容契约](../../API_CONTRACT.md)。

## Global Constraints

- frontend/content/ 是唯一内容事实源，禁止手动修改 src/generated/。
- 仅操作新前端搜索与对应文档；保留现有未提交改动。
- 本地服务固定 http://127.0.0.1:3400/。
- 不修改 .github/workflows/deploy.yml；上线仍需另行切换至 frontend/dist/。

## Review Focus

- 正文末尾关键词应可检索，图片路径、YAML 和隐藏内容不能误入索引。
- 无空格中文、中英文混排、英文大小写与前缀应可检索；空白和纯标点不返回全部文章。
- 标题命中优先，多个关键词不能只命中其中一个就返回。
- 中文、空格及特殊字符文章路径复用 contentHref 编码。
- 窄屏、深色、Esc、Tab 焦点约束、关闭后焦点恢复及加载失败重试。

## Task 1: 全文索引与检索核心

**Files:** 修改 frontend/scripts/lib/buildContent.mjs、buildContent.d.mts；新增 frontend/src/composables/search.ts、frontend/scripts/lib/search.test.mjs。

- [x] 先写测试：正文后段、代码关键词、标题权重、中文局部短语、英文前缀、AND、空输入、隐藏/README 排除、生成后更新与删除。
- [x] 运行 pnpm test，确认新增测试因缺少全文或检索能力失败。
- [x] searchDocs 增加 body，保留代码内容、去除链接地址和标签等格式；不改变现有摘要生成逻辑。
- [x] createSearch(documents: SearchDocument[]) 返回查询函数，结果仅存储标题、描述和路径，最多展示 30 条。
- [x] 运行 pnpm test，预期全部通过。

## Task 2: 搜索入口与弹窗

**Files:** 新增 frontend/src/components/layout/SearchDialog.vue；修改 Navbar.vue。

- [x] 顶部增加“搜索”按钮；关闭移动栏目菜单后打开弹窗。
- [x] 原生 dialog + 自动聚焦输入框，Tab 可访问结果链接，Esc/关闭/遮罩退出并恢复触发按钮焦点。
- [x] 首次打开动态导入引擎与生成索引，加载中/失败重试/无输入/无结果提供明确状态。
- [x] 显示标题、摘要及栏目路径；结果跳转复用 contentHref；复用已有主题变量与窄屏规则。
- [x] pnpm build 类型检查及生产打包通过，浏览器验证桌面/窄屏、深浅主题、正文搜索、跳转、关闭及惰性加载。

## Task 3: 文档与最终验证

**Files:** 精确更新 frontend/README.md 中搜索说明。

- [x] 记录使用方式、更新方式及 GitHub Pages 部署前置条件。
- [x] 完整运行 pnpm test、pnpm build、git diff --check，核对静态输出包含搜索资源。
- [x] 独立审阅当前未提交搜索差异，修复影响功能的问题；不触碰无关改动。

## 执行记录

- 需求/方案评审 PASS：用户已批准上述范围；无需新增运行时后端或 HTTP API，内容与搜索数据按当前契约维护。
- 架构评审 PASS：复用现有生成管线和路径工具，不新增依赖或模块目录。
- 执行时保护其他任务的未提交改动，仅精确更新搜索相关文件、README 搜索段落和本计划。

- 集成验证 PASS：20/20 测试、vue-tsc 类型检查和生产构建通过，git diff --check 无错误。
- 浏览器验证 PASS：桌面及 375px 手机视口、浅/深主题、中文全文与英文检索、空结果、Tab/Enter 跳转、Esc 关闭及焦点恢复。
- 静态预览验证 PASS：首页不预加载搜索资源；停止服务后首次搜索显示错误，恢复服务后点击重新加载可检索。
- 代码评审：只读子代理发现泛型代码误删、摘要绕过清理两项 P2，回归测试 RED→GREEN 后均修复；无遗留评审项。
- 实现决策：沿用现有文章范围，README 分类介绍不进入搜索；不切换 GitHub 发布，不新增依赖、不提交。
- 交付：静态预览 http://127.0.0.1:3400/；本次仅修改搜索相关文件和本计划，用户同期文档整理改动保留。
