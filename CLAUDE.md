# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hexo 8.1.2 blog ("箓川码笺") using the Butterfly 5.5.5-b1 theme. Chinese-language technical blog deployed to GitHub Pages at https://lucan6290.github.io. Author: lucan.

## Commands

- `npm run server` — local dev server (default http://localhost:4000)
- `npm run build` — generate static files to `public/`
- `npm run clean` — clear cache and `public/`
- `npx hexo new "Post Title"` — create a new post in `source/_posts/`
- `npx hexo new page "Page Name"` — create a new page in `source/<name>/`

## Architecture

- **`_config.yml`** — Hexo site config (URL, categories/tags maps, permalink format `:year/:month/:day/:title/`)
- **`_config.butterfly.yml`** — Butterfly theme config. This is the primary file for all theme customization.
- **`themes/butterfly/`** — Butterfly theme (NOT tracked in git, see `.gitignore`). Download from https://github.com/jerryc127/hexo-theme-butterfly/releases/tag/v5.5.5-b1
- **`source/_posts/`** — blog posts organized by category folders (Markdown with YAML front matter)
- **`source/css/custom.css`** — custom CSS styles
- **`scaffolds/`** — post templates for each category

## Deployment

GitHub Actions workflow (`.github/workflows/deploy.yml`) runs on push to `main`: installs deps with `npm ci`, runs `npx hexo generate`, then deploys via GitHub Pages Actions. Manual trigger available via `workflow_dispatch`.

## Conventions

### 创建新文章（必须遵守）

#### 使用分类模板创建（推荐）

**命令格式：**
```bash
hexo new [分类模板] "文章标题"
```

**五个一级分类模板：**

| 命令 | 一级分类 | 创建目录 | 适用场景 |
|------|---------|---------|---------|
| `hexo new tech-study "标题"` | 技术研习 | `source/_posts/tech-study/` | 技术学习、教程、原理分析 |
| `hexo new pitfall-review "标题"` | 踩坑复盘 | `source/_posts/pitfall-review/` | 问题解决、踩坑记录 |
| `hexo new project-practice "标题"` | 项目实战 | `source/_posts/project-practice/` | 项目开发、实战案例 |
| `hexo new growth-essay "标题"` | 成长随笔 | `source/_posts/growth-essay/` | 个人感悟、求职经验 |
| `hexo new resource-sharing "标题"` | 资源分享 | `source/_posts/resource-sharing/` | 工具推荐、资源整理 |

**示例：**
```bash
hexo new tech-study "Vue 3 组合式 API 详解"
hexo new pitfall-review "Docker 环境配置踩坑"
hexo new growth-essay "2026 年终技术总结"
```

### 文件命名规范（必须严格遵守）

**命名格式**: `[一级分类前缀]-[二级分类前缀]-[具体主题].md`

- `一级分类前缀`: 固定的分类前缀（见下表）
- `二级分类前缀`: 技术/工具/项目名称（灵活定义）
- `具体主题`: 文章主题描述，中英文均可

#### 一级分类前缀对照表

| 一级分类 | 前缀 | 目录 | 适用场景 |
|---------|------|------|---------|
| 技术研习 | `ts-` | `source/_posts/tech-study/` | 技术学习、教程、原理分析 |
| 踩坑复盘 | `pr-` | `source/_posts/pitfall-review/` | 问题解决、踩坑记录 |
| 项目实战 | `pp-` | `source/_posts/project-practice/` | 项目开发、实战案例 |
| 成长随笔 | `ge-` | `source/_posts/growth-essay/` | 个人感悟、求职经验 |
| 资源分享 | `rs-` | `source/_posts/resource-sharing/` | 工具推荐、资源整理 |

#### 二级分类前缀规则

二级分类前缀**灵活定义**，用于标识文章所属的技术栈、工具、项目或主题。

**命名原则：**
1. 按技术栈命名：使用技术/工具的英文名或缩写
2. 按项目命名：使用项目代号或简称
3. 按主题命名：使用主题关键词

**常用二级分类前缀速查表：**

| 前缀 | 说明 | 前缀 | 说明 |
|------|------|------|------|
| `vue3-` / `vue2-` | Vue | `react-` | React |
| `typescript-` | TypeScript | `js-` / `javascript-` | JavaScript |
| `node-` / `nodejs-` | Node.js | `python-` | Python |
| `docker-` | Docker | `k8s-` / `kubernetes-` | Kubernetes |
| `mysql-` | MySQL | `redis-` | Redis |
| `linux-` | Linux | `nginx-` | Nginx |
| `ai-` | AI 通用 | `llm-` | 大语言模型 |
| `claude-` | Claude | `cursor-` | Cursor |
| `git-` | Git | `hexo-` | Hexo |
| `vmware-` | VMware | `env-` | 环境配置通用 |
| `career-` | 求职之路 | `interview-` | 面试相关 |
| `learn-` | 学习方法 | `read-` | 读书笔记 |
| `annual-` | 年度总结 | `blog-` | 博客建设 |

#### 命名示例

```bash
# 技术研习
ts-vue3-响应式原理详解.md
ts-claude-开发环境配置.md
ts-docker-容器网络配置.md

# 踩坑复盘
pr-docker-容器启动失败排查.md
pr-mysql-索引失效分析.md
pr-vmware-共享目录配置.md

# 项目实战
pp-blog-用户认证功能实现.md
pp-shop-订单模块开发日志.md

# 成长随笔
ge-career-求职经历总结.md
ge-learn-高效学习方法.md
ge-blog-博客架构规划.md

# 资源分享
rs-claude-常用提示词合集.md
rs-vue3-组件库推荐.md
```

#### 命名注意事项

```bash
# ✅ 正确示例
ts-vue3-组合式API详解.md
pr-vmware-共享目录配置.md

# ❌ 错误示例
ts-vue3.md                      # 缺少具体主题
vue3-组合式API.md               # 缺少一级分类前缀
ts_vue3_组合式API.md            # 使用下划线分隔
ts-vue3-组合式API详解教程入门笔记.md  # 太长，超过60字符
```

**长度建议：**
- 理想长度：15-40 个字符
- 最大长度：不超过 60 个字符

### 元数据规范

- Posts use YAML front matter with `title`, `date`, `categories`, `tags`, `description`, `cover`
- Language: `zh-CN`; timezone: `Asia/Shanghai`
- Categories mapped to English slugs via `category_map` in `_config.yml`

## Theme Setup

If `themes/butterfly/` is missing, download it:
```bash
mkdir -p themes
cd themes
# Download from https://github.com/jerryc127/hexo-theme-butterfly/releases/tag/v5.5.5-b1
# Extract to themes/butterfly/
```

See `THEME_SETUP.md` for details.

## Documentation Maintenance

When project structure, conventions, or directory layout changes are requested, automatically update these documentation files:
- `CLAUDE.md` — this file
- `.claude-guidelines.md` — detailed development guidelines
- `README.md` — project overview