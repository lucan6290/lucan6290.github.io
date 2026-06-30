# Docs 与 Blog 内容规划规则

## 目标

`site/docs` 和 `site/blog` 分别承担不同的内容职责。

- `site/docs`：长期知识库，沉淀可反复查阅、持续维护、体系化的技术内容。
- `site/blog`：博客时间线，记录阶段进展、踩坑复盘、学习总结和个人成长随笔。

核心原则：

```text
docs 做成技术手册
blog 做成成长时间线
```

## site/docs 内容定位

`site/docs` 适合放长期有效、结构清晰、后续会持续补充的内容。

推荐主栏目：

```text
site/docs/
├── tech-study/             # 技术研习
├── project-practice/       # 项目实战
├── dev-standards/          # 开发规范
├── resource-sharing/       # 资源分享
└── intro.md                # 知识库入口
```

### 技术研习（tech-study）

用于整理系统性的技术知识。

二级分类：

```text
site/docs/tech-study/
├── java/             # JAVA相关
├── database/         # 数据库
├── devops/           # 运维与部署
└── frontend/         # 前端
```

#### JAVA相关（java）

可规划内容：

- Java 基础
- Java 集合
- JVM
- 并发编程
- Spring / Spring Boot

适合文章：

- Java 和 C++ 的区别
- Java 基础面试题总览
- JVM 内存模型
- Spring Boot 项目目录结构

#### 数据库（database）

可规划内容：

- MySQL / Redis

#### 运维与部署（devops）

可规划内容：

- Linux / Docker

适合文章：

- Docker 常用命令速查

#### 前端（frontend）

可规划内容：

- 前端基础

### 项目实战（project-practice）

用于沉淀项目从 0 到 1 的实现过程、架构设计和功能拆解。

二级分类：

```text
site/docs/project-practice/
├── projects/         # 项目案例
├── modules/          # 通用模块
└── deploy/           # 部署上线
```

#### 项目案例（projects）

可规划内容：

- 个人技术站搭建
- 后台管理系统
- 前后端分离项目

适合文章：

- Docusaurus 个人技术站搭建
- 后台管理系统接口设计


#### 部署上线（deploy）

可规划内容：

- 部署上线

适合文章：

- GitHub Pages 部署流程

### 开发规范（dev-standards）

用于沉淀个人或项目团队长期遵循的开发规则。

二级分类：

```text
site/docs/dev-standards/
├── workflow/         # 流程与协作
├── git/              # 版本控制
└── engineering/      # 工程约定
```

#### 流程与协作（workflow）

可规划内容：

- 单人全栈开发流程
- 前后端联调规范

适合文章：

- 单人全栈开发高效流程

#### 版本控制（git）

可规划内容：

- Git 提交规范

适合文章：

- Git 分支与提交规范

#### 工程约定（engineering）

可规划内容：

- 接口设计规范
- 目录结构规范
- 部署规范

适合文章：

- 前后端接口设计规范
- 项目目录结构约定

### 资源分享（resource-sharing）

用于整理长期有用的工具、网站、模板和学习资料。

二级分类：

```text
site/docs/resource-sharing/
├── tools/            # 工具
├── learning/         # 学习资料
├── environment/      # 开发环境
└── templates/        # 模板与脚手架
```

#### 工具（tools）

可规划内容：

- 工具箱
- 推荐网站
- AI 工具

适合文章：

- 常用开发工具箱
- AI 编程工具清单

#### 学习资料（learning）

可规划内容：

- 学习路线

适合文章：

- Java 学习路线
- 前端学习资源整理


## site/blog 内容定位

`site/blog` 适合放带有时间属性、阶段属性和个人经历的内容。

推荐类型：

> blog 按发布日期组织文件（如 `2026-06-29-xxx.md`），下面的分类作为 `tags` 使用，不再细分二级目录。

### 建站日志（site-build-log）

用于记录个人技术站的建设过程。

适合文章：

- 为什么重建个人技术站
- Docusaurus 站点搭建记录
- 首页改版记录
- GitHub Pages 部署踩坑
- 博客从 CSDN 迁移到个人站

### 踩坑复盘（troubleshooting）

用于记录某次具体问题的发现、解决和经验总结。

适合文章：

- VMware 共享目录配置复盘
- npm 依赖安装失败处理
- Docusaurus 路由 404 问题
- GitHub Pages 部署路径问题
- Windows / Linux 环境差异问题

### 学习周记 / 月记（learning-journal）

用于记录阶段性的学习进展。

适合文章：

- 2026 年 6 月学习总结
- Java 面试复习第 1 周
- 第一次完整搭建个人技术站
- 最近做项目时学到的 5 件事

### 项目过程记录（project-log）

用于记录项目推进中的阶段成果和思考。

适合文章：

- 个人技术站第一版完成
- 后台管理系统接口设计记录
- 某个功能从想法到实现
- 一次重构前后的思考

### 成长随笔（growth-notes）

用于记录技术学习和个人成长中的思考。

适合文章：

- 为什么要写技术博客
- 如何提高单人开发效率
- 从复制代码到理解代码
- 我的技术学习路线调整

## 内容放置判断

写文章前可以按下面的规则判断放到哪里。

| 内容类型 | 推荐位置 |
| --- | --- |
| 长期有效的知识点 | `site/docs` |
| 系列教程 | `site/docs` |
| 面试题整理 | `site/docs` |
| 工具清单 | `site/docs` |
| 项目实现文档 | `site/docs` |
| 开发规范 | `site/docs` |
| 某天遇到的问题 | `site/blog` |
| 项目阶段总结 | `site/blog` |
| 踩坑过程和复盘 | `site/blog` |
| 学习感受 | `site/blog` |
| 成长记录 | `site/blog` |

如果一篇内容同时具备两种属性，按下面方式处理：

- 过程记录放 `site/blog`。
- 最终沉淀出的稳定方法放 `site/docs`。

示例：

- `site/blog/2026-06-29-site-rebuild.md`：记录为什么开始重建技术站、当天做了什么、下一步计划。
- `site/docs/project-practice/site-build.md`：整理如何搭建 Docusaurus 技术站的完整教程。

## 标题风格

`site/docs` 的标题更像教程、手册和知识点。

推荐风格：

- Java 和 C++ 的区别
- Spring Boot 项目目录结构
- Docusaurus 个人技术站搭建
- 单人全栈开发高效流程
- Docker 常用命令速查

`site/blog` 的标题更像记录、复盘和阶段总结。

推荐风格：

- 今天开始重建个人技术站
- 记一次 VMware 共享目录配置问题
- 我为什么把知识库和博客分开
- 个人站第一阶段完成记录
- 2026 年 6 月学习与建站总结

## 优先建设内容

### docs 优先补充

1. 个人技术站搭建
2. 单人全栈开发高效流程
3. Java 基础面试题总览
4. 工具箱
5. 博客迁移规范

### blog 优先补充

1. 重建个人技术站
2. 为什么要把知识库和博客分开
3. 第一次搭建 Docusaurus 的踩坑记录
4. VMware 共享目录配置复盘
5. 2026 年 6 月学习与建站总结

## 维护规则

- 内容路径使用英文 slug。
- 页面标题、侧边栏标题和正文内容使用中文。
- `site/docs` 文章尽量保持长期有效，必要时持续更新。
- `site/blog` 文章保留发布时间和阶段背景。
- 从博客中沉淀出稳定方法后，可以再整理一篇对应的 `docs` 文档。
- 新增 `site/docs` 文章后，需要同步维护 `site/sidebars.ts`。
- 新增 `site/blog` 文章后，需要确认 Front Matter 中的 `slug`、`title`、`authors`、`tags` 清晰可用。

新增文章时具体要改哪些文件，按 `docs/新增文章同步维护规范.md` 执行。
