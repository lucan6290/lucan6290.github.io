# 博客阅读体验改版（2026-09-09）

## 生效规则与冻结范围
- Task Type: frontend；Change Surface: frontend_code。
- Required Rules: global、frontend；跨模块条件加载 src/pages、src/components、src/css、src/theme、plugins 的 AGENTS.md。已完整读取，missing_rules=[]。
- 来源：根/site AGENTS.md、site/lc-docs/GLOBAL_STANDARDS.md、FRONTEND_CONVENTION.md、目标模块入口及现有代码。
- 保留 Docusaurus / React / TypeScript、Markdown 事实源、现有 URL、导航分类、侧栏折叠/拖拽与固定 3400 热更新端口；不修改管理端、不新增依赖。

## 需求与验收
1. 首页：暖白与松绿的克制配色、编辑式标题、清晰知识入口、由真实内容派生的近期文章。
2. 博客：文章摘要、日期、阅读时长，支持跨分页全文列表的标题/摘要搜索、分类筛选和空结果重置。
3. 阅读：舒适行宽/行高、明确正文层级、可发现且可键盘操作的大纲入口。
4. 桌面/手机、亮色/暗色完整适配；不以 hover 作为唯一操作入口；减少动态效果偏好可用。
5. 构建、TypeScript、真实浏览器路由/筛选/主题/移动端回归；保留验证记录。

## 复用发现与方案
- 复用现有 Layout、Docusaurus 主题切换/移动导航、blog-category-pages 插件与 blogSidebars 分类。
- 插件从 Docusaurus 已解析的 blogPosts 提取全站文章摘要，供首页与博客页共用，避免复制 Markdown 或手写文章信息；排除 draft / unlisted。
- 在既有 BlogHomePage 目录增加内容类型/helper 与 CSS Module，不引入新模块或状态库。
- CSS 全局语义变量统一站点表面、文字、边框、交互和暗色；页面局部布局采用 CSS Modules。
- 大纲保留现有树形结构，改为显式按钮开关，支持 Escape 关闭与焦点返回，不再自动挤动全页。

## 契约与评审（实现前）
- API 契约：不适用，无网络接口变更。
- 站点派生数据：blog-category-pages.globalData.posts，字段 title/description/permalink/date/readingTime/tags/category/categoryPath；来源 Docusaurus 已发布文章 metadata，分类来源 blogSidebars。
- 主题 Props 保持 Docusaurus 接口兼容；所有文章链接使用 metadata.permalink。
- 需求评审 PASS；前端方案 PASS；契约评审 PASS（仅静态派生数据）；架构评审 PASS（沿用插件与现有主题）。状态 APPROVED。

## 基线
- 修改前工作树干净；首页与 /blog 无浏览器运行时错误，截图保存在 site/.codex-tmp/。
- TypeScript 基线有 4 项既有错误：BlogSidebar 的 @site/blogSidebars 类型解析、TOCItems 自定义 Props 与 Tree 递归只读类型。涉及相同改动面时最小修正。

## 完成验证
待实现后补充实际命令与结果。
