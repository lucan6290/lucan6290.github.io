# 箓川码笺项目框架规划

## 项目定位

本项目定位为长期维护的个人技术站与知识库系统。

- `site`：Docusaurus 公开站点，负责内容展示、阅读体验、首页、博客、项目页和知识库。
- `admin`：管理端，负责文章创建、内容编辑、图片管理、分类管理、预览构建等写作辅助能力。
- `admin/backend/data/content-schema`：内容规则中心，负责分类、标签、模板、Front Matter 等规范配置（由管理端后端读写）。
- `docs`：项目规划、设计记录和协作说明。

## 目录框架

```text
E:\A-Code\xiaocancoding\
├── site\
│   ├── docs\                 # 长期知识库、系列教程
│   ├── blog\                 # 博客、随笔、复盘、更新记录
│   ├── src\
│   │   ├── pages\            # 首页、关于页、项目展示页
│   │   ├── components\       # 自定义 React 组件
│   │   └── css\              # 阅读样式、主题样式
│   ├── static\               # 公共图片、头像、附件资源
│   ├── docusaurus.config.ts
│   └── sidebars.ts
│
├── admin\
│   ├── frontend\             # 管理后台前端React
│   ├── backend\              # FastAPI 后端python
│   │   └── data\
│   │       └── content-schema\   # 内容规则中心（分类、标签、模板、Front Matter）
│   │           ├── categories.yml  # 分类体系
│   │           ├── tags.yml        # 常用标签
│   │           ├── frontmatter.yml # Front Matter 规范
│   │           └── templates\      # 文章模板
│   └── docs\                 # 管理端相关文档
│
└── docs\                     # 项目整体规划文档
```

## 内容分层

```text
site/docs/     长期知识库、技术体系、系列教程
site/blog/     时间型文章、阶段总结、踩坑复盘、随笔
site/src/pages/ 首页、个人介绍、项目展示、资源导航
site/static/   公共静态资源
```

## Admin 职责

Admin 采用本地优先的内容管理方式。

- 前端提供文章列表、Markdown 编辑、分类选择、图片上传和预览入口。
- 后端使用 FastAPI 读写 `site/docs`、`site/blog` 和 `admin/backend/data/content-schema`。
- 后端负责创建文章、修改内容、生成侧边栏、校验 Front Matter、管理图片资源。
- Git 提交、构建、部署可以后续逐步接入。

## 内容规则

- 文件路径建议使用英文 slug；页面标题、侧边栏显示与正文内容均使用中文。
- 知识库内容放入 `site/docs`，时间型内容放入 `site/blog`。
- 文章必须保留清晰的 Front Matter。
- 图片资源跟随文章：在文章同目录下创建与文章同名的 `文章名-imgs` 文件夹存放图片；公共资源（头像、Logo 等）放入 `site/static`。
- 侧边栏优先由内容规则和目录结构生成，减少手动维护。

## 建设阶段

1. Docusaurus 站点骨架：首页、知识库、博客、关于页、项目页、基础样式。
2. 内容规范：分类、标签、Front Matter、文章模板、图片规则。
3. Admin 基础能力：文章 CRUD（创建、读取、编辑、删除）、Front Matter 解析与校验、分类注册表管理（自动同步目录与封面配置）、图片资源管理（上传、命名、未引用检测、清理）、文章列表与实时预览。
4. 增强能力：侧边栏与目录索引自动生成、文章全量索引与本地知识检索问答、AI 写作辅助（编辑器 / 写作 / 知识库三类 Agent，含受控工具调用与人工审批）、SSRF 安全网页抓取与素材提取、Git 提交 / 推送 / 一键部署。
