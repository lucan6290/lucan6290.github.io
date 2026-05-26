---
title: 我的博客搭建之旅 —— Hexo + Butterfly + GitHub Pages 全记录
date: 2026-05-22 15:30:00
categories:
  - [成长随笔, 博客建设]
tags: [hexo, butterfly, github-pages, ci-cd, tutorial, experience, problem-solving, 博客]
description: 从零开始，用 Hexo + Butterfly 主题在 GitHub Pages 上搭建个人技术博客的完整记录。
sticky: 100
---

## 前言

一直想拥有一个属于自己的技术博客，用来记录学习过程中的点滴。经过一番调研，最终选择了 **Hexo + Butterfly + GitHub Pages** 这套方案。这篇文章记录整个搭建过程，包括踩过的坑和解决方法。

## 为什么选 Hexo + Butterfly？

| 框架 | Node 生态 | 中文支持 | 主题丰富度 | 构建速度 |
|------|----------|---------|-----------|---------|
| Hexo | 原生支持 | 优秀 | 极多 | 快 |
| Hugo | 需安装 Go | 一般 | 较多 | 极快 |
| Jekyll | 需 Ruby | 一般 | 一般 | 较慢 |
| Gatsby | 原生支持 | 一般 | 丰富 | 慢 |

最终选择 Hexo 的原因：

1. **Node.js 环境** — 我电脑上已经有 Node，不需要额外安装
2. **Butterfly 主题** — 界面精美，中文文档齐全
3. **Markdown 写作** — 写技术文章的最佳方式
4. **免费托管** — GitHub Pages 提供无限流量

---

## 一、本地环境准备

### 1.1 安装 Node.js

Hexo 基于 Node.js，需要先安装 Node.js 环境。

**Windows 系统**：

1. 访问 [Node.js 官网](https://nodejs.org/)
2. 下载 LTS（长期支持版）安装包
3. 双击安装，一路 Next 即可
4. 打开终端验证安装：

```bash
node -v
# 输出示例: v20.15.0

npm -v
# 输出示例: 10.7.0
```

**建议**：Node.js 版本建议 18.x 及以上，Hexo 8.x 对 Node.js 18+ 支持更好。

### 1.2 配置 npm 镜像（国内用户）

国内访问 npm 官方源较慢，建议切换到淘宝镜像：

```bash
# 切换到淘宝镜像
npm config set registry https://registry.npmmirror.com

# 验证是否生效
npm config get registry
```

### 1.3 安装 Hexo CLI

```bash
npm install -g hexo-cli

# 验证安装
hexo -v
```

---

## 二、创建 Hexo 项目

### 2.1 初始化项目

```bash
# 创建项目目录
hexo init my-blog

# 进入目录
cd my-blog

# 安装依赖
npm install
```

初始化完成后，目录结构如下：

```
my-blog/
├── _config.yml      # 站点配置文件
├── package.json     # 依赖配置
├── scaffolds/       # 文章模板
├── source/          # 源文件
│   ├── _posts/      # 博客文章
│   └── _drafts/     # 草稿
└── themes/          # 主题目录
```

### 2.2 本地预览

```bash
# 启动本地服务器
hexo server

# 或简写
hexo s
```

打开浏览器访问 `http://localhost:4000`，可以看到默认的 Hexo 页面。

---

## 三、安装 Butterfly 主题

### 3.1 下载主题

```bash
# 进入主题目录
cd themes

# 克隆 Butterfly 主题
git clone -b master https://github.com/jerryc127/hexo-theme-butterfly.git butterfly

# 返回项目根目录
cd ..
```

### 3.2 安装主题必需依赖

Butterfly 主题需要一些额外的渲染器：

```bash
npm install hexo-renderer-pug hexo-renderer-stylus --save
```

### 3.3 启用主题

修改项目根目录的 `_config.yml`：

```yaml
# Extensions
theme: butterfly
```

### 3.4 创建主题配置文件（重要）

{% note warning %}
不要直接修改 `themes/butterfly/_config.yml`，因为主题更新时会被覆盖。
{% endnote %}

**正确做法**：在项目根目录创建 `_config.butterfly.yml`，Hexo 会自动合并配置：

```bash
# 在项目根目录创建
touch _config.butterfly.yml
```

---

## 四、配置站点信息

### 4.1 修改 `_config.yml`

以下是本博客的完整配置，按需修改：

```yaml
# Hexo Configuration
# Docs: https://hexo.io/docs/configuration.html

# Site
title: 箓川码笺                    # 博客标题
subtitle: '于技术之川，拾字成箓'    # 副标题
description: '箓藏千思，川流不息 —— 在广阔无垠的技术山川中，记录每一次探索、每一个踩坑、每一份感悟。'
keywords:
  - 技术博客
  - 踩坑记录
  - 前端
  - 后端
  - Agent
author: lucan                      # 作者名
language: zh-CN                    # 语言
timezone: 'Asia/Shanghai'          # 时区

# URL
url: https://你的用户名.github.io   # 改成你的 GitHub Pages 地址
permalink: :year/:month/:day/:title/
permalink_defaults:
pretty_urls:
  trailing_index: true
  trailing_html: true

# Directory
source_dir: source
public_dir: public
tag_dir: tags
archive_dir: archives
category_dir: categories
code_dir: downloads/code
i18n_dir: :lang
skip_render:

# Writing
new_post_name: :title.md
default_layout: post
titlecase: false
external_link:
  enable: true
  field: site
  exclude: ''
filename_case: 0
render_drafts: false
post_asset_folder: true            # 启用文章资源文件夹
relative_link: false
future: true
syntax_highlighter: highlight.js
highlight:
  line_number: true
  auto_detect: false
  tab_replace: ''
  wrap: true
  hljs: false

# Home page setting
index_generator:
  path: ''
  per_page: 8                      # 首页每页文章数
  order_by: -date

# Pagination
per_page: 8
pagination_dir: page

# Extensions
theme: butterfly

# Deployment（部署配置，后面会用到）
deploy:
  type: git
  repo: https://github.com/你的用户名/你的用户名.github.io.git
  branch: main
```

### 4.2 配置 Butterfly 主题

在 `_config.butterfly.yml` 中添加基础配置：

```yaml
# 导航菜单
menu:
  首页: / || fas fa-home
  归档: /archives/ || fas fa-archive
  分类: /categories/ || fas fa-folder
  标签: /tags/ || fas fa-tags
  关于: /about/ || fas fa-user

# 社交链接
social:
  fab fa-github: https://github.com/你的用户名 || GitHub || '#24292e'
  fas fa-envelope: mailto:你的邮箱@gmail.com || 邮箱 || '#4a7dbe'

# 代码块设置
code_blocks:
  theme: pale night
  macStyle: true
  height_limit: 520
  word_wrap: false
  copy: true
  language: true

# 搜索功能
search:
  use: local_search
  placeholder: 搜索文章...

# 暗黑模式
darkmode:
  enable: true
  button: true
  autoChangeMode: 1

# 文章目录
toc:
  post: true
  number: true
  expand: false
  scroll_percent: true

# 字数统计
wordcount:
  enable: true
  post_wordcount: true
  min2read: true
  total_wordcount: true
```

### 4.3 安装搜索插件

本地搜索功能需要安装插件：

```bash
npm install hexo-generator-search --save
```

---

## 五、创建必要页面

### 5.1 创建分类页

```bash
hexo new page categories
```

编辑 `source/categories/index.md`：

```markdown
---
title: 分类
date: 2026-05-22 15:00:00
type: categories
comments: false
---
```

### 5.2 创建标签页

```bash
hexo new page tags
```

编辑 `source/tags/index.md`：

```markdown
---
title: 标签
date: 2026-05-22 15:00:00
type: tags
comments: false
---
```

### 5.3 创建关于页

```bash
hexo new page about
```

编辑 `source/about/index.md`，填写你的个人信息。

---

## 六、GitHub 仓库设置

### 6.1 创建 GitHub 仓库

1. 登录 [GitHub](https://github.com/)
2. 点击右上角 `+` → `New repository`
3. 仓库名称必须是：`你的用户名.github.io`（例如：`lucan6290.github.io`）
4. 选择 `Public`（公开）
5. 勾选 `Add a README file`
6. 点击 `Create repository`

{% note info %}
仓库名必须是 `用户名.github.io` 格式，这是 GitHub Pages 的要求。
{% endnote %}

### 6.2 上传本地项目到 GitHub

在本地项目根目录执行：

```bash
# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Hexo blog setup"

# 添加远程仓库（改成你的用户名）
git remote add origin https://github.com/你的用户名/你的用户名.github.io.git

# 推送到 main 分支
git branch -M main
git push -u origin main
```

### 6.3 创建 .gitignore 文件

在项目根目录创建 `.gitignore`，避免提交不必要的文件：

```gitignore
.DS_Store
Thumbs.db
db.json
*.log
node_modules/
public/
.deploy*/
.idea/
*.iml
```

---

## 七、配置 GitHub Actions 自动部署

### 7.1 创建工作流文件

在项目根目录创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches:
      - main

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build-deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 24

      - name: Cache node_modules
        uses: actions/cache@v4
        with:
          path: node_modules
          key: ${{ runner.os }}-node-${{ hashFiles('package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-

      - name: Install dependencies
        run: npm ci

      - name: Generate static files
        run: npx hexo generate

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### 7.2 提交工作流文件

```bash
git add .
git commit -m "Add GitHub Actions workflow"
git push
```

---

## 八、配置 GitHub Pages

### 8.1 启用 GitHub Pages

1. 进入仓库页面
2. 点击 `Settings` → `Pages`（左侧菜单）
3. 在 `Build and deployment` → `Source` 中选择 `GitHub Actions`
4. 页面会自动刷新，显示部署状态

### 8.2 等待部署完成

1. 点击仓库顶部的 `Actions` 标签
2. 查看工作流运行状态
3. 显示绿色 ✓ 表示部署成功
4. 大约 1-3 分钟后访问 `https://你的用户名.github.io` 即可看到博客

---

## 九、日常使用

### 9.1 新建文章

本博客已配置按一级分类组织文章目录，推荐使用分类模板创建文章：

```bash
# 推荐：使用分类模板
hexo new tech-study "文章标题"      # 技术研习 → source/_posts/tech-study/
hexo new pitfall-review "文章标题"  # 踩坑复盘 → source/_posts/pitfall-review/
hexo new project-practice "文章标题" # 项目实战 → source/_posts/project-practice/
hexo new growth-essay "文章标题"    # 成长随笔 → source/_posts/growth-essay/
hexo new resource-sharing "文章标题" # 资源分享 → source/_posts/resource-sharing/
```

使用分类模板的好处：
- 文章自动创建在对应分类目录
- 自动预设分类字段
- 便于文件管理

### 9.2 文章 Front Matter 模板

```yaml
---
title: 文章标题
date: 2026-05-22 15:00:00
categories:
  - [技术研习, 入门笔记]
tags: [tag1, tag2, tag3]
description: 文章简介，会显示在文章列表和搜索引擎结果中。
cover: /img/covers/xxx.svg    # 封面图片（自动根据一级分类分配）
sticky: 100                   # 置顶优先级，数字越大越靠前（可选）
status: published             # draft/wip/published（可选，默认 published）
---
```

**内容分级说明：**

| 状态 | 值 | 说明 |
|------|------|------|
| 草稿 | `draft` | 刚开始写，部署时自动排除 |
| 半成品 | `wip` | Work In Progress，显示 WIP 标识 |
| 正式文章 | `published` | 完成度高（默认值） |

### 9.3 本地预览

```bash
hexo clean    # 清理缓存
hexo generate # 生成静态文件
hexo server   # 启动本地服务器
```

访问 `http://localhost:4000` 预览效果。

### 9.4 发布文章

```bash
git add .
git commit -m "New post: 文章标题"
git push
```

推送后 GitHub Actions 会自动构建部署。

---

## 十、踩坑记录

### 坑 1：npm install 失败

**现象**：`hexo init` 后运行 `hexo server` 报错 `MODULE_NOT_FOUND`

**原因**：国内网络环境下，`hexo init` 可能使用 pnpm 安装，导致 node_modules 结构不兼容

**解决**：删除 `node_modules` 和 `pnpm-lock.yaml`，改用 `npm install` 重新安装

```bash
rm -rf node_modules pnpm-lock.yaml
npm install
```

### 坑 2：GitHub Pages 404

**现象**：代码 push 后访问 `xxx.github.io` 显示 404

**解决步骤**：

1. 确认仓库名严格为 `用户名.github.io`
2. 进入 `Settings` → `Pages` → `Source` 选择 `GitHub Actions`
3. 检查 `Actions` 页面是否有报错
4. 等待 1-5 分钟生效

### 坑 3：主题配置不生效

**原因**：直接修改了 `themes/butterfly/_config.yml`，主题更新时配置丢失

**正确做法**：在项目根目录创建 `_config.butterfly.yml`，Hexo 会自动合并配置

### 坑 4：Actions 部署失败

**常见原因**：

1. `package-lock.json` 不存在或损坏 → 运行 `npm install` 重新生成
2. Node.js 版本过低 → 修改 `deploy.yml` 中的 `node-version`
3. 依赖安装失败 → 检查 `package.json` 中的依赖版本

### 坑 5：文章图片不显示

**原因**：图片路径错误或未启用文章资源文件夹

**解决**：

1. 确保 `_config.yml` 中 `post_asset_folder: true`
2. 图片放在与文章同名的文件夹中
3. 文章中使用 `{% asset_img image.jpg 图片描述 %}` 或相对路径引用

---

## 总结

搭建个人博客看似简单，实际过程中会遇到不少小问题。但这也是学习的一部分 —— 记录这些问题和解决方案，本身就是一篇不错的文章。

这篇文章就是新博客的第一篇，算是为「箓川码笺」开个头。希望以后能在这里积累更多有价值的技术内容。

## 参考资料

- [Hexo 官方文档](https://hexo.io/zh-cn/docs/)
- [Butterfly 主题文档](https://butterfly.js.org/)
- [GitHub Pages 官方文档](https://docs.github.com/zh/pages)

---
*于技术之川，拾字成箓*
