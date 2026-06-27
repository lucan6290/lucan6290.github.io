# AGENTS.md

本文件为 Codex 在本仓库中工作时的项目规范与执行规则。所有自动化修改、文章创建、样式调整和部署相关操作都应优先遵守本文档。

## 项目概述

- 项目类型：Hexo 8.1.2 静态博客
- 站点名称：箓川码笺
- 主题：Butterfly 5.5.5-b1
- 语言：中文技术博客
- 部署地址：https://lucan6290.github.io
- 作者：lucan

## Codex 工作规则

1. 优先读取并遵守本文件，其次参考 `README.md`、`CLAUDE.md`、`blog-content/_config.yml` 和 `blog-content/_config.butterfly.yml`。
2. 不要直接修改 `blog-content/themes/butterfly/` 下的文件；主题定制只允许放在 `blog-content/_config.butterfly.yml` 和 `blog-content/source/css/custom.css`。
3. 发现工作区已有未提交改动时，不要回滚或覆盖无关文件；只处理当前任务需要修改的文件。
4. 新增文章后必须更新 `blog-content/source/_posts/index.md`，并运行 `cd blog-content && npm run build` 验证构建。
5. 重大结构调整、部署配置变更、批量改名、删除文件前，需要先向用户确认。
6. 提交信息使用简洁中文描述。

## 常用命令

| 命令 | 说明 |
|------|------|
| `cd blog-content && npm run server` | 启动本地预览，默认地址为 `http://localhost:4000` |
| `cd blog-content && npm run build` | 生成静态文件到 `blog-content/public/` |
| `cd blog-content && npm run clean` | 清理 Hexo 缓存和 `blog-content/public/` |
| `cd blog-content && npx hexo np <一级前缀> <二级前缀> "标题"` | 创建新文章，推荐使用，会自动命名 |
| `cd blog-content && npx hexo new page "Page Name"` | 创建新页面 |

## 项目结构

```text
blog/
├── admin-dev/
│   ├── frontend/              # 管理后台前端源码
│   ├── backend/               # 管理后台本地模式后端源码
│   └── docs/                  # 管理后台文档
├── blog-content/              # Hexo 博客前端内容
│   ├── source/
│   │   ├── _posts/            # 博客文章，按分类文件夹组织
│   │   ├── _drafts/           # 草稿
│   │   ├── about/             # 关于页面
│   │   ├── categories/        # 分类页
│   │   ├── tags/              # 标签页
│   │   └── img/
│   │       └── covers/        # 分类封面图
│   ├── themes/
│   │   └── butterfly/         # Butterfly 主题，不提交到 git
│   ├── scaffolds/             # 文章模板
│   ├── scripts/               # Hexo 自定义脚本
│   ├── _config.yml            # Hexo 主配置
│   ├── _config.butterfly.yml  # Butterfly 主题配置
│   └── source/css/custom.css  # 自定义样式
└── .github/workflows/         # 部署工作流
```

## 关键文件

- `blog-content/_config.yml`：Hexo 站点配置，包含 URL、分类/标签映射、永久链接格式。
- `blog-content/_config.butterfly.yml`：Butterfly 主题配置，所有主题配置修改都在此文件。
- `blog-content/source/_posts/`：博客文章目录，Markdown 文件按分类存放。
- `blog-content/source/_posts/index.md`：全站文章总目录，新增文章后必须同步维护。
- `blog-content/source/css/custom.css`：自定义 CSS 样式。
- `blog-content/scripts/new-post.js`：文章创建相关脚本。
- `admin-dev/frontend/`：管理后台前端源码，构建产物输出到 `blog-content/source/admin/`。
- `admin-dev/backend/`：管理后台本地模式后端源码。
- `admin-dev/docs/`：管理后台说明文档。
- `blog-content/`：Hexo 博客前端内容存放目录。

## 文章创建规范

创建新文章必须使用：

```bash
cd blog-content && npx hexo np <一级前缀> <二级前缀> "标题"
```

示例：

```bash
cd blog-content && npx hexo np ts vue3 "Vue3组合式API详解"
# 生成：blog-content/source/_posts/tech-study/ts-vue3-Vue3组合式API详解.md

cd blog-content && npx hexo np pr docker "Docker环境配置踩坑"
# 生成：blog-content/source/_posts/pitfall-review/pr-docker-Docker环境配置踩坑.md

cd blog-content && npx hexo np ge annual "2026年终技术总结"
# 生成：blog-content/source/_posts/growth-essay/ge-annual-2026年终技术总结.md
```

## 文件命名规范

文章文件命名格式：

```text
[一级前缀]-[二级前缀]-[具体主题].md
```

一级分类前缀：

| 前缀 | 分类 | 目录 | 适用场景 |
|------|------|------|----------|
| `ts` | 技术研习 | `blog-content/source/_posts/tech-study/` | 技术学习、教程、原理分析 |
| `pr` | 踩坑复盘 | `blog-content/source/_posts/pitfall-review/` | 问题解决、踩坑记录 |
| `pp` | 项目实战 | `blog-content/source/_posts/project-practice/` | 项目开发、实战案例 |
| `ge` | 成长随笔 | `blog-content/source/_posts/growth-essay/` | 个人感悟、求职经验 |
| `rs` | 资源分享 | `blog-content/source/_posts/resource-sharing/` | 工具推荐、资源整理 |

常用二级分类前缀：

| 前缀 | 说明 | 前缀 | 说明 |
|------|------|------|------|
| `ai` | AI 通用 | `llm` | 大语言模型 |
| `git` | Git | `hexo` | Hexo |
| `learn` | 学习方法 | `read` | 读书笔记 |
| `annual` | 年度总结 | `blog` | 博客建设 |

命名示例：

```text
ts-frontend-vue3响应式原理详解.md
pr-docker-docker容器启动失败排查.md
pp-blog-用户认证功能实现.md
ge-career-求职经历总结.md
rs-codex-AI常用提示词合集.md
```

## Front Matter 规范

每篇文章必须包含以下字段。通过 `npx hexo np` 创建时会自动生成基础结构，修改时不要随意删除字段。

```yaml
---
title: 文章标题
date: 2026-05-22 15:30:00
updated:

categories:
  - [一级分类, 二级分类]

tags:
  - 标签1
  - 标签2

description: 文章简介（100-200字）

layout: post
comments: true
permalink:
excerpt:
published: true
lang: zh-CN

cover: /img/covers/封面.svg
sticky:

slug:
status: draft

series:
series_order:
---
```

字段要求：

- `description` 控制在 100-200 字，写清文章主题和读者收益。
- `status` 可选值为 `draft`、`wip`、`published`。
- 3 篇及以上紧密相关的文章使用 `series` 和 `series_order`。
- `cover` 按分类封面配置，优先使用已有 `blog-content/source/img/covers/` 资源。

## 文章总目录维护

博客使用 `blog-content/source/_posts/index.md` 维护已发布文章索引。新增文章后必须将链接添加到对应一级分类和二级分类下。

目录链接格式：

```markdown
## 一级分类名称

### 二级分类名称

- [文章标题](/年/月/日/分类名/文章文件名不含.md/)
```

示例：

```markdown
## 成长随笔

### 博客建设

- [博客架构与长期发展规划](/2026/05/23/growth-essay/ge-blog-博客架构与长期发展规划/)
- [博客架构规划](/2026/05/28/growth-essay/ge-blog-博客架构规划/)
```

分类名使用 `blog-content/_config.yml` 中 `category_map` 映射后的英文名，例如 `growth-essay`、`tech-study`、`pitfall-review`。

## 写作规范

- 使用中文写作，表达清晰，避免无意义堆砌术语。
- Markdown 结构要清楚，合理使用标题、列表、表格和代码块。
- 代码块必须注明语言，示例应尽量可运行。
- 技术文章应包含背景、问题或目标、关键步骤、注意事项和总结。
- 排错文章应写清环境、现象、原因、解决过程和最终方案。

## 图片规范

Hexo 已启用 `post_asset_folder`。每篇文章的图片放在同名资源文件夹中。

目录示例：

```text
blog-content/source/_posts/tech-study/
├── ts-vue3-Vue3组合式API详解.md
└── ts-vue3-Vue3组合式API详解/
    ├── img1.png
    └── img2.jpg
```

图片命名：

```text
img1.png
img2.jpg
img3.webp
```

Markdown 引用：

```markdown
![图片描述](img1.png)
```

## 部署规则

- 推送到 `main` 分支会触发 `.github/workflows/deploy.yml`。
- 工作流在 `blog-content/` 中使用 `npm ci` 安装博客依赖，运行 `npm run build`，再通过 GitHub Pages Actions 部署。
- 支持 `workflow_dispatch` 手动触发。

## 主题安装

如果 `blog-content/themes/butterfly/` 不存在：

```bash
cd blog-content
mkdir -p themes
cd themes
# 从以下地址下载 Butterfly 5.5.5-b1：
# https://github.com/jerryc127/hexo-theme-butterfly/releases/tag/v5.5.5-b1
# 解压到 themes/butterfly/
```

不要将 `blog-content/themes/butterfly/` 提交到 git。

## 文档维护

当项目结构、命令、分类规则、目录布局或协作规范发生变化时，必须同步更新本文件。
