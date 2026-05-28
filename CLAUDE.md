# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供项目指引。

## 项目概述

Hexo 8.1.2 博客（"箓川码笺"），使用 Butterfly 5.5.5-b1 主题。中文技术博客，部署到 GitHub Pages：https://lucan6290.github.io。作者：lucan。

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run server` | 启动本地预览（http://localhost:4000） |
| `npm run build` | 生成静态文件到 `public/` |
| `npm run clean` | 清理缓存和 `public/` |
| `npx hexo np <一级前缀> <二级前缀> "标题"` | 创建新文章（推荐，自动命名） |
| `npx hexo new page "Page Name"` | 创建新页面 |

## 项目架构

- **`_config.yml`** — Hexo 站点配置（URL、分类/标签映射、永久链接格式 `:year/:month/:day/:title/`）
- **`_config.butterfly.yml`** — Butterfly 主题配置。所有主题定制都在此文件。
- **`themes/butterfly/`** — Butterfly 主题（不提交到 git，见 `.gitignore`）。下载地址：https://github.com/jerryc127/hexo-theme-butterfly/releases/tag/v5.5.5-b1
- **`source/_posts/`** — 博客文章，按分类文件夹组织（Markdown + YAML front matter）
- **`source/css/custom.css`** — 自定义 CSS 样式
- **`scaffolds/`** — 各分类的文章模板
- **`scripts/`** — Hexo 自定义脚本（如 `new-post.js`）

## 目录结构

```
blog/
├── source/
│   ├── _posts/              # 博客文章（按分类文件夹组织）
│   │   ├── tech-study/      # 技术研习
│   │   ├── pitfall-review/  # 踩坑复盘
│   │   ├── project-practice/  # 项目实战
│   │   ├── growth-essay/    # 成长随笔
│   │   └── resource-sharing/  # 资源分享
│   ├── _drafts/             # 草稿
│   ├── about/               # 关于页面
│   ├── categories/          # 分类页
│   ├── tags/                # 标签页
│   └── img/                 # 图片资源
│       ├── covers/          # 分类封面图
│       └── posts/           # 文章图片（按一级分类组织）
│           ├── tech-study/        # 技术研习图片
│           ├── pitfall-review/    # 踩坑复盘图片
│           ├── project-practice/  # 项目实战图片
│           ├── growth-essay/      # 成长随笔图片
│           └── resource-sharing/  # 资源分享图片
├── themes/
│   └── butterfly/           # Butterfly 主题（不提交到 git）
├── scaffolds/               # 文章模板（按分类）
├── scripts/                 # Hexo 自定义脚本
├── _config.yml              # Hexo 主配置
├── _config.butterfly.yml    # Butterfly 主题配置
└── source/css/custom.css    # 自定义样式
```

## 部署

GitHub Actions 工作流（`.github/workflows/deploy.yml`）在推送到 `main` 分支时触发：使用 `npm ci` 安装依赖，运行 `npx hexo generate`，然后通过 GitHub Pages Actions 部署。支持手动触发（`workflow_dispatch`）。

## 规范

### 创建新文章（必须遵守）

**命令格式：**
```bash
npx hexo np <一级前缀> <二级前缀> "标题"
```

**示例：**
```bash
npx hexo np ts vue3 "Vue3组合式API详解"
# → 文件: source/_posts/tech-study/ts-vue3-Vue3组合式API详解.md

npx hexo np pr docker "Docker环境配置踩坑"
# → 文件: source/_posts/pitfall-review/pr-docker-Docker环境配置踩坑.md

npx hexo np ge annual "2026年终技术总结"
# → 文件: source/_posts/growth-essay/ge-annual-2026年终技术总结.md
```

### 文件命名规范（必须严格遵守）

**命名格式**: `[一级前缀]-[二级前缀]-[具体主题].md`

#### 一级分类前缀对照表

| 前缀 | 分类 | 目录 | 适用场景 |
|------|------|------|---------|
| `ts` | 技术研习 | `source/_posts/tech-study/` | 技术学习、教程、原理分析 |
| `pr` | 踩坑复盘 | `source/_posts/pitfall-review/` | 问题解决、踩坑记录 |
| `pp` | 项目实战 | `source/_posts/project-practice/` | 项目开发、实战案例 |
| `ge` | 成长随笔 | `source/_posts/growth-essay/` | 个人感悟、求职经验 |
| `rs` | 资源分享 | `source/_posts/resource-sharing/` | 工具推荐、资源整理 |

#### 二级分类前缀（灵活定义）

| 前缀 | 说明 | 前缀 | 说明 |
|------|------|------|------|
| `ai` | AI 通用 | `llm` | 大语言模型 |
| `git` | Git | `hexo` | Hexo |
| `learn` | 学习方法 | `read` | 读书笔记 |
| `annual` | 年度总结 | `blog` | 博客建设 |

#### 命名示例

```bash
ts-frontend-vue3响应式原理详解.md       # 技术研习
pr-docker-docker容器启动失败排查.md   # 踩坑复盘
pp-blog-用户认证功能实现.md     # 项目实战
ge-career-求职经历总结.md       # 成长随笔
rs-claude-AI常用提示词合集.md     # 资源分享
```

### 文章 Front Matter

每篇文章必须包含以下内容(hexo np命令已自动创建)：

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

# Hexo 官方参数
layout: post
comments: true
permalink:
excerpt:
published: true
lang: zh-CN

# Butterfly 主题参数
cover: /img/covers/封面.svg  # 按分类自动设置
sticky:

# 博客自定义参数
slug:
status: draft  # draft / wip / published

# 系列文章（可选，3篇以上相关文章时使用）
series:
series_order:
---
```

> 💡 官方文档：https://hexo.io/docs/front-matter.html

### 系列文章导航

当有 3 篇以上紧密相关的文章时，使用 `series` 字段组织：

```yaml
---
series: "系列名称"
series_order: 1
---
```

### 分类目录索引

每个一级分类目录下有一个索引文章（置顶）：

| 索引文件 | 作用 |
|---------|------|
| `ts-index.md` | 技术研习目录 |
| `pr-index.md` | 踩坑复盘目录 |
| `pp-index.md` | 项目实战目录 |
| `ge-index.md` | 成长随笔目录 |
| `rs-index.md` | 资源分享目录 |

**索引维护规则：**

创建新文章后，必须检查并更新对应一级分类的索引文件，将新文章添加到对应的二级分类位置：

```markdown
## 二级分类名称

- [文章标题](文件名.md)
```

**示例：**

创建 `ge-blog-博客架构规划.md` 后，更新 `ge-index.md`：

```markdown
## 博客建设

- [博客架构与长期发展规划](ge-blog-博客架构与长期发展规划.md)
- [博客架构规划](ge-blog-博客架构规划.md)  ← 新增
```

> 💡 索引文件按二级分类组织，新增文章需放入对应二级分类区块内

### 写作规范

- **语言**：中文为主，清晰易懂
- **格式**：Markdown，合理使用标题、列表、表格、代码块
- **代码块**：注明语言，示例要正确可运行
- **图片**：按一级分类存放，命名与文章一致

#### 图片命名规范

**命名格式**：`[一级分类前缀]-[二级分类前缀]-[具体主题]-imgN.扩展名`

| 一级分类 | 图片目录 | 命名示例 |
|---------|---------|---------|
| 技术研习 | `source/img/posts/tech-study/` | `ts-vue3-响应式原理详解-img1.png` |
| 踩坑复盘 | `source/img/posts/pitfall-review/` | `pr-docker-容器启动失败排查-img1.png` |
| 项目实战 | `source/img/posts/project-practice/` | `pp-blog-用户认证功能实现-img1.png` |
| 成长随笔 | `source/img/posts/growth-essay/` | `ge-annual-2026年终技术总结-img1.png` |
| 资源分享 | `source/img/posts/resource-sharing/` | `rs-claude-常用提示词合集-img1.png` |

**Markdown 引用：**
```markdown
![图片描述](/img/posts/tech-study/ts-vue3-响应式原理详解-img1.png)
```

### 协作规则

#### 必须遵守

1. ✅ 不要直接修改 `themes/butterfly/` 下的文件
2. ✅ 主题定制在 `_config.butterfly.yml` 和 `source/css/custom.css`
3. ✅ 重大变更先确认再执行
4. ✅ 新增文章后，运行 `npm run build` 验证构建

#### 推荐做法

- 先了解现有文章的风格再创建新文章
- 复杂问题拆分成小步骤，逐步执行

## Git 与部署

- 推送到 `main` 分支自动触发 GitHub Actions 部署
- Commit 信息使用简洁中文描述
- 也可手动触发：https://github.com/lucan6290/lucan6290.github.io/actions

## 主题安装

如果 `themes/butterfly/` 目录不存在：
```bash
mkdir -p themes
cd themes
# 从 https://github.com/jerryc127/hexo-theme-butterfly/releases/tag/v5.5.5-b1 下载
# 解压到 themes/butterfly/
```

## 文档维护

当项目结构、规范或目录布局发生变化时，自动更新本文件（`CLAUDE.md`）。