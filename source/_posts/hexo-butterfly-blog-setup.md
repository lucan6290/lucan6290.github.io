---
title: 我的博客搭建之旅 —— Hexo + Butterfly + GitHub Pages 全记录
date: 2026-05-22 15:30:00
categories:
  - [踩坑复盘, 环境配置]
tags: [hexo, butterfly, github-pages, ci-cd, tutorial, experience, problem-solving, 博客]
description: 从零开始，用 Hexo + Butterfly 主题在 GitHub Pages 上搭建个人技术博客的完整记录。
cover:
sticky: 100
---

## 前言

一直想拥有一个属于自己的技术博客，用来记录学习过程中的点滴。经过一番调研，最终选择了 **Hexo + Butterfly + GitHub Pages** 这套方案。这篇文章记录整个搭建过程，包括踩过的坑和解决方法。

## 为什么选 Hexo + Butterfly？

| 框架 | Node 生态 | 中文支持 | 主题丰富度 | 构建速度 |
|------|----------|---------|-----------|---------|
| Hexo | 原生支持 | 优秀 | 极多 | 快 |
| Hugo | 需安装 | 一般 | 较多 | 极快 |
| Jekyll | 需 Ruby | 一般 | 一般 | 较慢 |
| Gatsby | 原生支持 | 一般 | 丰富 | 慢 |

最终选择 Hexo 的原因很简单：

1. **Node.js 环境** — 我电脑上已经有 Node，不需要额外安装
2. **Butterfly 主题** — 界面精美，中文文档齐全
3. **Markdown 写作** — 写技术文章的最佳方式
4. **免费托管** — GitHub Pages 提供无限流量

## 搭建步骤

### 1. 安装 Hexo

```bash
npm install -g hexo-cli
hexo init blog
cd blog
npm install
```

### 2. 安装 Butterfly 主题

```bash
cd themes
git clone --depth 1 https://github.com/jerryc127/hexo-theme-butterfly butterfly
```

### 3. 配置主题

在项目根目录创建 `_config.butterfly.yml`，覆盖主题默认配置。关键配置项：

```yaml
# 导航菜单
menu:
  首页: / || fas fa-home
  归档: /archives/ || fas fa-archive
  分类: /categories/ || fas fa-folder
  标签: /tags/ || fas fa-tags
  关于: /about/ || fas fa-user

# 搜索
search:
  use: local_search
  
# 暗黑模式
darkmode:
  enable: true
  autoChangeMode: 1
```

### 4. GitHub Actions 自动部署

{% note info %}
这一步是最容易出错的环节，务必确保 `deploy.yml` 中的分支名称和仓库名称正确。
{% endnote %}

核心配置：

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches:
      - main
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 24
      - run: npm ci
      - run: npx hexo generate
      - uses: peaceiris/actions-gh-pages@v4
        with:
          publish_dir: ./public
          publish_branch: gh-pages
```

## 踩坑记录

### 坑 1：npm install 失败

**现象**：`hexo init` 后直接运行 `hexo server` 报错 `MODULE_NOT_FOUND`

**原因**：国内网络环境下，`hexo init` 可能使用 pnpm 安装，导致 node_modules 结构不兼容

**解决**：删除 `node_modules` 和 `pnpm-lock.yaml`，改用 `npm install` 重新安装

### 坑 2：GitHub Pages 404

**现象**：代码 push 后访问 `xxx.github.io` 显示 404

**解决步骤**：
1. 确认仓库名严格为 `用户名.github.io`
2. 进入 Settings → Pages → Source 选择 `GitHub Actions`
3. 检查 Actions 页面是否有报错
4. 等待 1-5 分钟生效

### 坑 3：主题配置文件不生效

**原因**：直接修改了主题目录下的 `_config.yml`，导致后续更新主题时配置丢失

**正确做法**：在项目根目录创建 `_config.butterfly.yml`，Hexo 会自动合并配置

## 总结

搭建个人博客看似简单，实际过程中会遇到不少小问题。但这也是学习的一部分 —— 记录这些问题和解决方案，本身就是一篇不错的文章。

这篇文章就是新博客的第一篇，算是为「箓川码笺」开个头。希望以后能在这里积累更多有价值的技术内容。

---
*于技术之川，拾字成箓*
