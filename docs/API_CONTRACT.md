# 内容与搜索数据契约

> 更新日期：2026-10-29。当前读者站点没有业务 HTTP API；本文约定构建数据、页面路径及浏览器搜索边界。

## 契约事实源

- [content.ts](../frontend/src/types/content.ts)：内容清单与文章类型。
- [buildContent.mjs](../frontend/scripts/lib/buildContent.mjs) 及 [声明文件](../frontend/scripts/lib/buildContent.d.mts)：构建输入、输出。
- [contentPaths.ts](../frontend/src/composables/contentPaths.ts)：路径编码、互链及侧栏范围。
- [search.ts](../frontend/src/composables/search.ts)：当前工作区的检索数据与返回值。

变更以上字段或路径时同步生成端、消费端和测试，不添加旧数据结构兼容分支。

## 内容构建入口

`build({ contentDir?, outDir? })` 默认读取 `frontend/content/`，输出到 `frontend/src/generated/`。CLI 为 `pnpm build:content`；开发和生产构建也会自动调用内容生成。

| 生成文件 | 数据 |
| --- | --- |
| `content-manifest.json` | `tree`、`articles`、`prevNext`、`tags`、`archive`、`recent` |
| `search-index.json` | 文章检索文档数组 |
| `tags.json` | 标签到文章路径数组的映射 |
| `archive.json` | 年、月到文章路径数组的映射 |

`build` 的返回值同时含 `searchDocs`，Vite 的 `virtual:content-manifest` 只提供内容清单字段；搜索窗口另外惰性加载索引。

## 文章与目录

| 类型 | 字段与含义 |
| --- | --- |
| `FrontMatter` | 可选 `title`、`date`、`updated`、`tags: string[]`、`description`、`sticky` |
| `ArticleMeta` | `slug`、`path`、`relativePath`、规范化 frontmatter、`sortKey`、`mtimeMs`、`excerpt`、`wordCount`、`rawContent` |
| `TreeNode` | `name`、`label`、`path`、`sortKey`、`children`，可含 `article` 或目录 `introduction` |
| `PrevNext` | `prev`、`next` 为文章的 `slug`、`path`、`title`，不存在时为 `null` |

- `path` 是去掉 Markdown 扩展名后的站内原始路径；进入 URL 时逐段编码。
- `relativePath` 是相对 `content/` 的源文件路径，保留扩展名，分隔符统一为 `/`。
- 标题回退顺序：frontmatter、首个一级标题、去前缀文件名；日期缺省使用文件时间。
- `rawContent` 不含 frontmatter。`description` 缺省时 `excerpt` 从正文生成。
- `wordCount` 使用当前中英文计数规则，不按 Markdown 源码字符数计算。
- README 存入目录的 `introduction`，不作为普通文章写入文章映射；标签、归档、搜索均由文章映射生成。

## 页面路径

| 路径 | 行为 |
| --- | --- |
| `/` | 站点首页 |
| `/about` | 固定关于页面 |
| `/:section/:pathMatch(.*)*` | 根据内容树显示分类或文章 |
| `/tags`、`/tags/:tag` | 无同名内容栏目时显示标签工具 |
| `/archive` | 无同名内容栏目时显示归档工具 |

`contentHref(path)` 按段编码中文、空格和特殊字符；`contentPath(root, segments)` 从路由参数恢复内容路径。不要在组件中重复实现路径编码。

`resolveContentUrl(value, relativePath, assets, base = '/')` 以 Markdown 源文件位置解析相对链接：Markdown 指向文章，README 指向分类，已收集资源替换为 Vite 构建地址。生成的站内地址与输入的绝对站内地址添加部署 base；Vite 资源不重复添加前缀，外部地址和锚点保持不变。

内容数据与 Router 使用不含部署前缀的逻辑路径。浏览器 URL 边界由 `withBasePath(value, base)` 添加 base、`stripBasePath(pathname, base)` 去除 base；不属于当前部署路径的 URL 不由 Markdown 点击处理器接管。Vue Router History 与 Vite 资源统一使用 `import.meta.env.BASE_URL`。

生产构建由内容插件调用 `writeStaticPages({ outDir, manifest })`，依据内容树和内置页占用规则生成目录 `index.html`，并输出 `404.html`、`.nojekyll`。这些文件复用构建后的应用 HTML 入口；不存在正文预渲染数据接口。

知识库、博客、项目的分类页只列直属分类与直属文章；首页有 README 正文时显示介绍，无正文时自动展示目录入口。完整 UI 约定见 [FRONTEND_CONVENTION.md](FRONTEND_CONVENTION.md)。

## 搜索数据与查询

当前工作区的 `SearchDocument` 字段：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | string | 文章路径标识 |
| `title` | string | 展示标题 |
| `description` | string | 摘要 |
| `tags` | string | 标签用空格连接后的检索文本 |
| `path` | string | 站内原始路径 |
| `body` | string | 处理后的正文，包含代码关键词 |

`createSearch(documents)` 返回查询函数，查询结果含 `id`、`title`、`description`、`path`，最多 30 条。空白输入返回空数组；多关键词 AND 匹配，标题、标签、摘要权重依次降低，英文支持前缀。

索引源于文章映射；正文生成时移除注释、图片和链接地址及部分格式标记，保留可检索文字及代码内容。变更检索格式时使用新规范数据重建索引。

## 实时更新与边界

- 内容插件监控新增、修改、删除文件和目录，失效虚拟模块并触发页面刷新。
- 生成文件属于构建产物，不由浏览器反写，也不提供在线编辑接口。
- 页面导航、全文搜索和浮动目录不依赖后端服务。
- 自动部署已配置为测试、构建并发布 `frontend/dist/`，部署 base 来自 GitHub Pages 元数据；本地构建、提交和线上可访问分别验收，不能互相替代。
- 新增 HTTP、上传、评论或统计服务前另行定义明确契约，不能把本文描述成这些 API 已存在。
