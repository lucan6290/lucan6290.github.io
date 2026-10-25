# 箓川码笺 开发说明（site 目录）

> 面向开发者的 site 目录结构与维护说明。不参与站点构建，纯参考文档。
> 如果你要找"新增一篇文章需要改哪些文件"的规范，本文末尾的【操作速查】一节可直接照做。
> 站内另有一篇面向读者的 [新增文章同步维护规范](docs/project-practice/博客建设/新增文章同步维护规范.md)，两者互补：本文更强调架构原理与 blog 分类聚合页机制。

---

## 一、技术栈与项目性质

- 基于 **Docusaurus 3**（`@docusaurus/preset-classic`），TypeScript 配置。
- 内容分两大体系：**docs（长期知识库）** 与 **blog（阶段博客）**。
- 额外做了一个**自定义插件 + 自定义页面**，用于生成"博客分类聚合页"（见第四节）。
- 部署目标：GitHub Pages，`url: https://lucan6290.github.io`，`baseUrl: '/'`，仓库 `lucan6290/xiaocancoding`。

---

## 二、目录结构总览

```text
site/
├── docusaurus.config.ts          # 主配置：preset、navbar、footer、插件注册
├── sidebars.ts                   # docs 专用：手动维护 docs 左侧侧边栏
├── blogSidebars.ts               # blog 专用：博客"分类清单"，被自定义插件读取
├── plugins/
│   └── blog-category-pages/
│       └── index.js              # 自定义插件：为每个博客分类生成聚合页路由
├── docs/                         # docs 内容（长期知识库）
│   ├── index.md
│   ├── project-practice/         # 一级分类：项目实战
│   └── resource-sharing/         # 一级分类：资源分享
├── blog/                         # blog 内容（按"分类子目录"组织）
│   ├── authors.yml               # 博客作者定义
│   ├── AI观察/                   # 分类目录
│   └── 随笔感想/                 # 分类目录
├── src/
│   ├── pages/                    # 独立页面：首页 / 关于 / 项目展示
│   ├── components/
│   │   └── BlogCategoryPage/     # 自定义渲染的"博客分类聚合页"组件
│   └── css/custom.css            # 主题自定义样式
├── static/                       # 静态资源（img/favicon 等）
├── build/                        # 构建产物（勿手改）
└── .docusaurus/                  # 缓存（勿手改）
```

---

## 三、核心配置文件作用与关联

### 3.1 [docusaurus.config.ts](docusaurus.config.ts) —— 总指挥

它决定"docs / blog / 自定义页面"如何被装配，关键配置块：

| 配置块 | 位置 | 作用 |
|---|---|---|
| `presets → classic → docs` | [docusaurus.config.ts:26-32](docusaurus.config.ts#L26-L32) | 声明 docs 目录 = `docs`，路由前缀 `/docs`，侧边栏文件指向 `./sidebars.ts` |
| `presets → classic → blog` | [docusaurus.config.ts:33-43](docusaurus.config.ts#L33-L43) | 声明 blog 目录 = `blog`，路由前缀 `/blog`，每页 8 篇，开启阅读时长 |
| `plugins` | [docusaurus.config.ts:51-53](docusaurus.config.ts#L51-L53) | 注册本地自定义插件 `./plugins/blog-category-pages` |
| `themeConfig.navbar` | [docusaurus.config.ts:57-143](docusaurus.config.ts#L57-L143) | **手写**顶部导航栏（知识库 / 博客 / 项目 / 关于 四个下拉菜单） |
| `themeConfig.footer` | [docusaurus.config.ts:144-164](docusaurus.config.ts#L144-L164) | 页脚链接（手写） |
| `themeConfig.docs.sidebar` | [docusaurus.config.ts:165-170](docusaurus.config.ts#L165-L170) | docs 侧边栏可折叠 |
| `themeConfig.prism` | [docusaurus.config.ts:179-181](docusaurus.config.ts#L179-L181) | 代码高亮额外语言：java/bash/yaml/json/python |

**关键认知**：顶部导航和页脚都是**硬编码**在配置里的，新增一个一级分类或一篇"重点文章"想进菜单，必须回来改这里的 `to`。

### 3.2 [sidebars.ts](sidebars.ts) —— docs 专用侧边栏

**只服务于 docs，与 blog 无关。** 当前定义了三个 sidebar 分组：

- `overviewSidebar`：知识库首页入口（指向 `index`）。
- `projectPracticeSidebar`：项目实战，含"开发规范""博客建设"两个二级分类。
- `'resource-sharingSidebar'`：资源分享，含"接口测试1""接口测试2"两个二级分类。

docs 文章**必须**在这里登记文章 ID（相对 `docs/` 的路径，不带扩展名），否则不会出现在左侧导航里。docs 的导航顺序完全由这里的书写顺序和 `sidebar_position` 决定。

### 3.3 [blogSidebars.ts](blogSidebars.ts) —— blog 分类清单（自定义机制）

这个文件**不是** Docusaurus 原生侧边栏配置，而是本项目自定义的"博客分类清单"。它被 [plugins/blog-category-pages/index.js](plugins/blog-category-pages/index.js) 用**正则**（不是 import）读取，用来生成博客分类聚合页。

每个条目字段含义：

```ts
{
  label: 'AI观察',        // 聚合页标题与导航显示名
  path: 'AI观察',         // 对应 blog/ 下的分类目录名
  to: '/blog/AI观察',     // 聚合页路由地址
  count: 2,               // 显示用计数（仅展示，不强制校验）
}
```

**重要：** 因为插件用正则解析此文件（见 [index.js:7-33](plugins/blog-category-pages/index.js#L7-L33)），条目里必须保留 `label` / `path` / `to` 三个字段且用引号字符串写法，正则才能匹配上。

### 3.4 自定义插件 [plugins/blog-category-pages/index.js](plugins/blog-category-pages/index.js)

**它做了什么：**

1. 在 `contentLoaded` 阶段读取 [blogSidebars.ts](blogSidebars.ts)，解析出分类清单（[index.js:7-33](plugins/blog-category-pages/index.js#L7-L33)）。
2. 对每个分类，扫描 `blog/<分类目录>/` 下所有 `.md/.mdx`（[index.js:40-61](plugins/blog-category-pages/index.js#L40-L61)），提取 frontmatter 的 `title / description / date / tags / slug`。
3. 用 `addRoute` 注册一个路由：路径 = 分类 `to`，组件 = [`@site/src/components/BlogCategoryPage`](src/components/BlogCategoryPage/index.tsx)，数据 = 该分类下的文章列表（[index.js:63-94](plugins/blog-category-pages/index.js#L63-L94)）。

**permlink 计算规则**（[index.js:35-38](plugins/blog-category-pages/index.js#L35-L38)）：
- 优先取 frontmatter 的 `slug`；
- 否则用文件名，并去掉 `YYYY-MM-DD-` 日期前缀（虽然当前站点文件名都没用日期前缀，但代码支持）。
- 最终拼成 `/blog/<slug>`。

**注意一个潜在不一致点：** 这个聚合页插件计算出的文章链接是 `/blog/<slug>`，而 Docusaurus 原生 blog 路由也由 `slug` 决定。两者必须保持文章 frontmatter 里 `slug` 唯一且稳定，否则聚合页点进去会 404。

### 3.5 聚合页组件 [src/components/BlogCategoryPage/index.tsx](src/components/BlogCategoryPage/index.tsx)

- 顶部标题 "博客分类 / <分类名>"，下方按日期倒序列出文章（标题、日期、描述、标签）。
- 复用了原生 `BlogSidebar` 组件，但传入的是空 items（[index.tsx:96](src/components/BlogCategoryPage/index.tsx#L96)），所以右侧导航实际是空的，标题"博客目录"。

---

## 四、docs 与 blog 的区别（重点）

| 维度 | docs（知识库） | blog（博客） |
|---|---|---|
| 路由前缀 | `/docs` | `/blog` |
| 目录组织 | 按"英文一级分类 / 中文二级 / 中文文章名" | 按"中文分类目录 / 中文文章名" |
| 导航维护 | **必须**手动维护 [sidebars.ts](sidebars.ts) | **不需要**改 sidebars.ts；原生列表/归档/标签页按 `date` 自动生成 |
| 分类聚合页 | 即侧边栏本身 | 由 [blogSidebars.ts](blogSidebars.ts) + 自定义插件生成，如 `/blog/AI观察` |
| 文章顺序 | `sidebar_position` + sidebars.ts 书写顺序 | `date` 倒序 |
| 必备 frontmatter | `title`（推荐 `description`、`sidebar_position`） | `slug`、`title`、`authors`、`date`（推荐 `tags`、`description`、`last_update`） |
| 作者 | 无 | 需在 [blog/authors.yml](blog/authors.yml) 定义 |
| 适合内容 | 长期有效的体系化笔记、教程 | 有时间属性的进展、踩坑、随笔 |

**一句话区分**：docs 是"书"，靠你手动编排目录；blog 是"信息流"，靠日期自动排序，外加一套自定义的分类聚合页。

---

## 五、blog 分类聚合页机制（本项目独有，务必理解）

这是 [新增文章同步维护规范](docs/project-practice/博客建设/新增文章同步维护规范.md) 里**未覆盖**的部分，最容易踩坑。

### 数据流

```text
blogSidebars.ts（声明有哪些分类）
        │  被 plugins/blog-category-pages/index.js 正则读取
        ▼
为每个分类扫 blog/<分类目录>/*.md
        │  提取 frontmatter，按 date 倒序
        ▼
注册路由 /blog/<分类path>  →  BlogCategoryPage 组件渲染
```

### 三个文件必须保持一致

要让某个博客分类聚合页（比如 `/blog/AI观察`）正常工作，**三处必须对齐**：

1. **目录存在**：`blog/AI观察/` 下至少有一篇 `.md`。
2. **清单登记**：[blogSidebars.ts](blogSidebars.ts) 里有对应条目，且 `path` = 目录名、`to` = `/blog/` + 目录名。
3. **导航可达**（可选）：[docusaurus.config.ts](docusaurus.config.ts) 顶部"博客"下拉菜单里有该 `to` 入口。

**任意一处缺失/拼错**：聚合页 404、内容为空、或导航点不进去。

---

## 六、docs 操作流程

### 6.1 新增 docs 文章（在已有二级分类下）

例：在"项目实战 / 开发规范"下新增一篇。

1. 新建文件：`docs/project-practice/开发规范/新文章.md`，frontmatter 至少：
   ```md
   ---
   title: 新文章标题
   description: 一句话说明
   sidebar_position: 2
   ---
   ```
2. 在 [sidebars.ts](sidebars.ts) 对应的 `items` 数组里加入文章 ID：
   ```ts
   items: [
     'project-practice/开发规范/单人全栈开发高效流程',
     'project-practice/开发规范/新文章',
   ],
   ```
3. 不用改 `docusaurus.config.ts`，除非想让它进顶部菜单。

### 6.2 新增 docs 二级分类

1. 新建目录与文章。
2. 在 [sidebars.ts](sidebars.ts) 对应一级分类的 `items` 里加一个 `type: 'category'` 块（照现有"开发规范"块抄）。

### 6.3 新增 docs 一级分类

1. 新建一级目录（英文 slug 命名），含 `index.md` 和子内容。
2. 在 [sidebars.ts](sidebars.ts) 顶部新增一个 sidebar 分组。
3. 在 [docusaurus.config.ts](docusaurus.config.ts) 顶部"知识库"下拉菜单（[docusaurus.config.ts:65-83](docusaurus.config.ts#L65-L83)）加入口，`to` 指向该分类首页。

### 6.4 删除 docs 文章

1. 删除 `.md` 文件。
2. 在 [sidebars.ts](sidebars.ts) 删掉对应文章 ID。
3. 全站搜索旧路径（其他 docs 文章里的 markdown 链接、`docusaurus.config.ts` 的 `to`），按需修正。
4. 当前 `onBrokenLinks: 'warn'`（[docusaurus.config.ts:15](docusaurus.config.ts#L15)），即使有死链也只是警告不阻断构建——但**不要依赖这个**，死链会影响体验。

---

## 七、blog 操作流程（含分类聚合页同步）

### 7.1 在已有分类下新增博客

例：在"AI观察"下新增一篇。

1. 新建文件：`blog/AI观察/新文章.md`，frontmatter 参考：
   ```md
   ---
   slug: 新文章
   title: 新文章标题
   authors: lucan
   date: 2026-07-01T10:00:00+08:00
   description: 一句话说明
   tags:
     - AI
     - 思考
   last_update:
     date: 2026-07-01T10:00:00+08:00
     author: lucan
   ---
   ```
2. **不需要改** [sidebars.ts](sidebars.ts)（blog 不用它）。
3. **不需要改** [blogSidebars.ts](blogSidebars.ts)（分类已存在，插件会自动扫到新文件）。
4. **不需要改** [docusaurus.config.ts](docusaurus.config.ts)，除非要让文章进顶部"博客"菜单。

> 注意 `slug` 必须全站唯一，它直接决定文章 URL `/blog/<slug>`，也决定聚合页能否正确跳转。

### 7.2 新增博客分类（比如新增"踩坑复盘"）

需要改 **3 处**，缺一不可：

1. 新建目录：`blog/踩坑复盘/`，并在里面放至少一篇 `.md`。
2. 在 [blogSidebars.ts](blogSidebars.ts) 加条目：
   ```ts
   {
     label: '踩坑复盘',
     path: '踩坑复盘',
     to: '/blog/踩坑复盘',
     count: 1,
   },
   ```
3.（可选但推荐）在 [docusaurus.config.ts](docusaurus.config.ts) 顶部"博客"下拉菜单（[docusaurus.config.ts:85-101](docusaurus.config.ts#L85-L101)）加入口：
   ```ts
   { label: '踩坑复盘', to: '/blog/踩坑复盘' },
   ```

### 7.3 删除博客文章

1. 删除 `.md` 文件。
2. **不需要改** [blogSidebars.ts](blogSidebars.ts)（插件运行时实时扫描目录，文件没了自然不显示）。
3. 检查是否有其他文章或 `docusaurus.config.ts` 指向过它的 `/blog/<slug>`，按需清理。

### 7.4 删除博客分类

1. 删除整个分类目录。
2. 在 [blogSidebars.ts](blogSidebars.ts) 删除对应条目。
3. 在 [docusaurus.config.ts](docusaurus.config.ts) 顶部"博客"菜单删除对应入口。

### 7.5 新增博客作者

如果 `authors` 不是已有的 `lucan`，需在 [blog/authors.yml](blog/authors.yml) 定义：

```yml
newAuthor:
  name: 作者名
  title: 作者说明
  url: https://example.com
  image_url: https://example.com/avatar.png
```

---

## 八、独立页面 src/pages

[src/pages/](src/pages/) 下放不归属于 docs / blog 的独立页面，每个 `.tsx` 自动生成一个路由：

| 文件 | 路由 | 说明 |
|---|---|---|
| [src/pages/index.tsx](src/pages/index.tsx) | `/` | 站点首页（hero + 三个入口卡片） |
| [src/pages/about.tsx](src/pages/about.tsx) | `/about` | 关于本站 |
| [src/pages/projects.tsx](src/pages/projects.tsx) | `/projects` | 项目展示 |

> 这些页面目前**没有**维护文章清单，新增 docs/blog 文章无需改它们。

---

## 九、操作速查（改哪些文件）

### 新增一篇 docs 文章
- ✅ 新建 `docs/.../文章.md`
- ✅ 改 [sidebars.ts](sidebars.ts) 登记文章 ID

### 新增一篇 blog 文章（已有分类）
- ✅ 新建 `blog/<分类>/文章.md`（含 `slug`）
- ❌ 不改 sidebars.ts / blogSidebars.ts / docusaurus.config.ts

### 新增一个 blog 分类
- ✅ 新建 `blog/<分类>/` 目录 + 文章
- ✅ 改 [blogSidebars.ts](blogSidebars.ts) 加条目
- ✅（推荐）改 [docusaurus.config.ts](docusaurus.config.ts) 博客菜单加入口

### 新增一个 docs 一级分类
- ✅ 新建 `docs/<英文 slug>/` 目录 + 内容
- ✅ 改 [sidebars.ts](sidebars.ts) 加 sidebar 分组
- ✅ 改 [docusaurus.config.ts](docusaurus.config.ts) 知识库菜单加入口

### 删除任意文章
- ✅ 删文件 → 删 sidebars/blogSidebars 里的引用 → 搜全站死链

---

## 十、常用命令

```bash
cd site
npm install         # 安装依赖
npm run start       # 本地开发，默认 http://localhost:3000
npm run build       # 生产构建到 build/
npm run serve       # 本地预览构建产物
npm run deploy      # 部署到 GitHub Pages（需配置 CI/密钥）
```

---

## 十一、常见坑与排查

| 现象 | 排查方向 |
|---|---|
| docs 文章左侧导航不显示 | 文章 ID 没在 [sidebars.ts](sidebars.ts) 登记，或路径拼错 |
| 博客分类聚合页 404 / 内容为空 | [blogSidebars.ts](blogSidebars.ts) 的 `path` 与实际目录名不一致，或目录里没有 `.md` |
| 聚合页点文章 404 | 文章 frontmatter `slug` 被改过或缺失；聚合页插件的 permalink 与原生 blog 路由不同步 |
| 顶部菜单点不动 | [docusaurus.config.ts](docusaurus.config.ts) 里 `to`/`href` 拼错；内部链接用 `to`，外链用 `href` |
| 构建有 broken links 警告 | 当前 `onBrokenLinks: 'warn'` 不会阻断构建，但应修复：检查 sidebars 文章 ID、markdown 内部链接、删除文章后的残留引用 |
| 改了 blogSidebars.ts 不生效 | 该文件被插件用正则解析，确认字段写法是 `label: '...'`、`path: '...'`、`to: '...'` 带引号 |

---

## 十二、相关文件索引

- 主配置：[docusaurus.config.ts](docusaurus.config.ts)
- docs 侧边栏：[sidebars.ts](sidebars.ts)
- blog 分类清单：[blogSidebars.ts](blogSidebars.ts)
- 博客分类插件：[plugins/blog-category-pages/index.js](plugins/blog-category-pages/index.js)
- 聚合页组件：[src/components/BlogCategoryPage/index.tsx](src/components/BlogCategoryPage/index.tsx)
- 博客作者：[blog/authors.yml](blog/authors.yml)
- 站内规范文档：[docs/project-practice/博客建设/新增文章同步维护规范.md](docs/project-practice/博客建设/新增文章同步维护规范.md)
