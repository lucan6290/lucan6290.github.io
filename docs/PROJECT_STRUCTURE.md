# 工程目录与实现入口

> 更新日期：2026-10-29。本文只描述当前前端及工程文档；按职责定位，不复制源码。

## 当前维护目录

```text
xiaocancoding/
├── AGENTS.md                         # Agent 导航入口
├── docs/
│   ├── DOCUMENTATION_INDEX.md        # 工程文档入口
│   ├── GLOBAL_STANDARDS.md           # 公共开发约束
│   ├── PROJECT_STRUCTURE.md          # 当前目录职责
│   ├── FRONTEND_CONVENTION.md        # 前端约定
│   ├── SITE_CONTENT_GUIDE.md         # 内容写作与维护
│   ├── API_CONTRACT.md               # 内容与搜索数据契约
│   ├── BACKEND_CONVENTION.md         # 后端边界
│   ├── PRD/                         # 需求及专题方案
│   └── superpowers/plans/            # 任务实施计划
├── frontend/
│   ├── README.md                    # 启动、构建、写作说明
│   ├── content/                     # 唯一内容事实源
│   │   ├── knowledge/
│   │   ├── blog/
│   │   └── projects/
│   ├── public/                      # 站点公共静态资源
│   ├── scripts/build-content.mjs     # 内容生成命令
│   ├── scripts/lib/                 # 生成逻辑、类型与测试
│   ├── src/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── config/
│   │   ├── router/
│   │   ├── styles/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── views/
│   │   ├── vite/
│   │   └── generated/               # 自动生成，禁止手动编辑
│   └── dist/                        # 构建产物
└── .github/workflows/               # 自动化流程
```

## 源码职责

| 能力 | 路径（仓库根目录相对） |
| --- | --- |
| 路由分发 | `frontend/src/router/index.ts`、`frontend/src/views/ContentRoute.vue` |
| 分类首页与列表 | `frontend/src/views/CategoryView.vue` |
| 独立文章 | `frontend/src/views/ArticleView.vue` |
| 首页与关于 | `frontend/src/views/HomePage.vue`、`frontend/src/views/AboutPage.vue` |
| 内容清单访问 | `frontend/src/composables/useContent.ts` |
| URL 编码、相对路径和侧栏范围 | `frontend/src/composables/contentPaths.ts` |
| 顶部栏目生成 | `frontend/src/config/nav.ts`、`frontend/src/components/layout/Navbar.vue` |
| Markdown 与图片 | `frontend/src/components/article/MarkdownRenderer.vue` |
| 侧栏 | `frontend/src/components/sidebar/` |
| 文章列表、面包屑与排序 | `frontend/src/components/list/` |
| 本文目录 | `frontend/src/components/toc/FloatToc.vue` |
| 读者搜索窗口 | `frontend/src/components/layout/SearchDialog.vue` |
| 读者检索逻辑 | `frontend/src/composables/search.ts` |
| 主题与基础样式 | `frontend/src/styles/tokens.css`、`frontend/src/styles/base.css` |
| 清单类型 | `frontend/src/types/content.ts` |
| 内容扫描与索引 | `frontend/scripts/lib/buildContent.mjs`、`buildContent.d.mts` |
| 静态路由入口生成 | `frontend/scripts/lib/staticPages.mjs`、`staticPages.d.mts` |
| 开发监控与虚拟模块 | `frontend/src/vite/contentManifestPlugin.ts` |
| 回归测试 | `frontend/scripts/lib/*.test.mjs` |

## 内容结构

目录就是分类，每篇项目或笔记使用一个 Markdown 文件。数字前缀用于排序；URL 保留实际目录名、文件名。

```text
frontend/content/projects/
├── README.md
├── 01-我的项目/
│   ├── 01-TerminalVoice.md
│   ├── 02-AgentKit.md
│   └── 03-get_jobs.md
└── 02-开源项目与工具/
    ├── 01-Orca.md
    └── 02-Hexhub.md
```

知识库和博客使用同样的目录模型。图片与文章相邻存放，统一命名为 `文章名-images/`；详细规则见 [内容指南](SITE_CONTENT_GUIDE.md)。内容分类目录不属于新增业务模块，不需逐个加入页面路由或栏目配置。

## 内容生成流程

`content/` → `scripts/lib/buildContent.mjs` → `src/generated/` → Vite 虚拟内容模块 / 搜索索引 → Vue 页面。

- `pnpm dev` 先生成内容，随后监听文件、目录和资源变更并刷新页面。
- `pnpm build` 先生成内容，再做类型检查和生产打包，输出 `dist/`。
- 生产内容插件依据内容树和内置页面规则生成静态目录入口、`404.html` 与 `.nojekyll`，复用应用入口 HTML；这不等于正文 SSG 预渲染。
- 生成文件和构建产物不作为手工修改入口。
- 当前本地运行端口为 3400；读者端搜索、目录与文章展示均不需要运行时后端。

## 文档与实现同步

新增或移动实现入口时同步本文件和 [文档索引](DOCUMENTATION_INDEX.md)。数据结构变化同步 [内容契约](API_CONTRACT.md)，内容规则变化同步 [内容指南](SITE_CONTENT_GUIDE.md)。
