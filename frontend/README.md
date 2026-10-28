# frontend — 箓川码笺自研前端

> 替代 `site/`（Docusaurus）的自研前端，页面样式完全复刻现站，代码独立编写。

## 技术栈

- Vite 6 + Vue 3.5 + TypeScript
- ByteMD（GFM + highlight + KaTeX + Mermaid）只读渲染
- minisearch 全文搜索
- 纯 CSS design tokens（复刻 site/src/css/custom.css 变量体系）

## 本地开发

```powershell
cd frontend
pnpm install
pnpm dev          # http://127.0.0.1:3400/
```

端口固定为 **3400**（遵守项目根 AGENTS.md 约束）。若被占用先清理：

```powershell
netstat -ano | Select-String ':3400'
Stop-Process -Id <PID> -Force
```

## 内容写作规范

- 内容事实源：`content/` 目录
- 目录 = 分类页，`.md` = 内容页，任意嵌套
- 文件名数字前缀排序：`01-xxx.md`；无前缀按标题排序；也可切换为发布日期排序
- frontmatter 字段：`title` / `date` / `updated` / `tags` / `description` / `sticky`
- 置顶：`sticky: true` 恒排最前
- `content/` 一级目录自动生成顶部栏目，栏目内的目录和文章自动进入左侧目录及下拉菜单。

### 复制笔记即可展示

将 Markdown 笔记文件夹（连同配图）放进 `content/knowledge/`，随笔放进 `content/blog/`：

```text
content/knowledge/Python学习/
├── README.md
├── 01-环境安装.md
├── 02-基础语法.md
└── images/
    └── 环境配置.png
```

- 文档头部的 YAML 配置不是必填项。标题依次取 `title`、正文首个 `# 一级标题`、去掉数字前缀的文件名。
- `README.md`（不区分大小写）作为所在分类的介绍，显示在文章列表之前，不作为普通文章出现在列表、标签和归档里。
- `![配置](./images/环境配置.png)` 等相对图片路径按 Markdown 文件位置解析，开发和生产构建均可使用。支持 PNG、JPEG、GIF、SVG、WebP、AVIF、BMP、ICO；PDF 可作为附件链接。
- `[下一章](./02-基础语法.md)` 自动跳转到站内文章，`[分类介绍](./README.md)` 跳转到分类页；支持 `../`、中文、空格（链接地址可用 `%20`）及查询参数、锚点。
- 文内标题锚点保留中文和数字、英文转小写、空格转 `-`、去掉标点；同名标题追加 `-1`、`-2`。例如 `## 安装步骤` 对应 `#安装步骤`。
- `images/`、`assets/`、以 `-imgs` 结尾的目录保留给资源，不作为分类；一级空目录仍生成栏目。知识库、博客和项目栏目的空分类也保留；仅含图片等资源的目录不生成分类。
- 以 `.` 或 `_` 开头的文件、目录不进入内容树。目录名与文件名构成 URL，移动或重命名后需要同步更新相关链接。
- 未填写日期时使用文件时间。复制文件或重新检出仓库可能改变这些时间；有发布日期要求时请显式填写 `date`。

运行 `pnpm dev` 时，新增、修改或删除内容会自动刷新。公网静态网站仍需重新执行构建并部署 `dist/`，仅复制到本地不会更新线上。

本阶段以标准 Markdown 为支持范围，不执行 MDX JSX，也不转换 Obsidian 双链、Word 或原始 HTML 内的资源地址。

### 验证

```powershell
pnpm test         # 内容扫描与路径回归测试，需要 Node.js 22.18+ 或 24+
pnpm build        # 类型检查与生产构建
```

## 顶部栏目与目录

| 一级目录 | 顶部栏目 | 首页内容 |
| --- | --- | --- |
| `content/knowledge/` | 知识库 | README 正文；无正文时自动展示直属分类与文章 |
| `content/blog/` | 博客 | README 正文；无正文时自动展示直属分类与文章 |
| `content/projects/` | 项目 | README 正文；无正文时自动展示直属分类与文章 |
| 固定页面 `/about` | 关于 | `src/views/AboutPage.vue` |
| `content/学习路线/` 等新目录 | 文件夹名称 | README（可选）与文章列表 |

- 新建一级目录即可出现顶部入口，无需修改导航或路由代码，空目录也可进入。
- “关于”是固定页面，点击顶部导航直接进入，不依赖内容目录。
- 窄窗口点击顶部“栏目”按钮展开导航，选择页面后自动收起。
- 知识库、博客和项目下拉菜单只显示首页及直属一级文件夹。二级及更深文件夹显示在分类页和左侧目录；分类页只列直属子分类和直属文章，不将后代文档平铺。其他栏目下拉仍显示首页及直属子分类、文章。
- 知识库层级示例：`knowledge/Java/集合框架/HashMap.md` → 下拉选 Java → 分类页选集合框架 → 打开 HashMap。新建空分类也可按此路径逐级进入。
- 知识库、博客和项目共用目录与文章展示规则：首页显示各自 `README.md` 的正文，侧栏自动显示一级分类；README 不存在或内容为空时，自动显示栏目标题、直属子分类和直属文章。其他分类的 README 作为分类介绍，不单独列为文章。
- 项目内容示例：`projects/01-我的项目/01-TerminalVoice.md` 和 `projects/02-开源项目与工具/01-Orca.md`。新增目录或 Markdown 后会自动进入分类与导航，无需修改页面代码。
- 现有四栏按知识库、博客、项目、关于排列，新增栏目追加在后；新增栏目间遵循内容树的数字前缀及名称顺序。
- 重命名、删除目录会同步改变栏目及地址；隐藏和资源目录不生成栏目。
- `src/config/nav.ts` 仅保留四栏中文名称、固定顺序、Logo 和右侧外链配置。
- `tags` 和 `archive` 原为标签、归档工具页；如果创建同名一级目录，则该地址优先展示内容栏目。

## 构建

```powershell
pnpm build        # 输出到 dist/
pnpm preview      # 本地预览构建产物
```

## 不在本前端范围

- 评论区 / 阅读统计（P1）
- SEO / RSS / SSG 预渲染（P2）
- series 系列专题
- 在线编辑 / admin 联动
- 内容迁移（用户自行从 site/blog + site/docs 迁入）
