---
title: 从零开始写一篇博客 —— 完整写作指南
date: 2026-05-25 10:00:00
categories:
  - [成长随笔, 博客建设]
tags: [blog, hexo, markdown, 写作指南, 教程]
description: 一篇手把手教你如何从零开始写完一篇完整博客的指南，包括创建文章、选择分类、命名规范、Markdown 语法、图片插入、本地预览和发布到仓库的完整流程。
cover: /img/covers/growth-essay.svg
---

## 前言

本文将手把手教你如何从零开始写一篇完整的博客文章，涵盖从创建到发布的全流程。无论你是第一次写博客，还是想了解本博客的写作规范，这篇文章都能帮到你。

---

## 一、创建新文章

### 1.1 使用自定义命令创建（推荐）

本博客已定制 `hexo np` 命令，自动完成文件命名、目录创建和 Front Matter 生成。

**命令格式：**

```bash
hexo np <一级前缀> <二级前缀> <标题>
```

**示例：**

```bash
hexo np ts vue3 "Vue3组合式 API详解"
# → source/_posts/tech-study/ts-vue3-Vue3组合式 API详解.md
```

> 💡 详细说明请参考 [定制创建文章命令记录](ge-blog-定制创建文章命令记录.md)

### 1.2 文章命名规范

文件名格式：`[一级分类前缀]-[二级分类前缀]-[具体主题].md`

**示例：**
- `ts-vue3-组合式API详解.md` — 技术研习 / Vue3
- `pr-docker-环境配置踩坑.md` — 踩坑复盘 / Docker
- `ge-annual-2026年终总结.md` — 成长随笔 / 年度总结

> 💡 完整命名规范请参考 [博客架构与长期发展规划](ge-blog-博客架构与长期发展规划.md)

---

## 二、填写文章信息（Front Matter）

创建文章后，打开 `.md` 文件，你会看到类似这样的内容：

```yaml
---
title: Vue 3 组合式 API 详解
date: 2026-05-25 10:00:00
categories:
  - [技术研习, 入门笔记]
tags: [vue3, composition-api, 前端]
description: 深入讲解 Vue 3 组合式 API 的核心概念和最佳实践。
---
```

### 2.1 必填字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `title` | 文章标题（显示在博客上） | `Vue 3 组合式 API 详解` |
| `date` | 发布日期时间 | `2026-05-25 10:00:00` |
| `categories` | 分类层级 | `[技术研习, 入门笔记]` |
| `tags` | 标签列表 | `[vue3, 前端]` |
| `description` | 文章简介（100-200字） | 显示在列表页和搜索引擎 |

### 2.2 可选字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `cover` | 封面图片（自动分配，通常无需填写） | `/img/covers/tech-study.svg` |
| `sticky` | 置顶优先级（数字越大越靠前） | `100` |
| `status` | 内容状态 | `draft` / `wip` / `published` |
| `slug` | 自定义 URL | `vue3-composition-api` |

---

## 三、Markdown 常用语法

### 3.1 标题

```markdown
## 二级标题

### 三级标题

#### 四级标题
```

### 3.2 文本样式

```markdown
**粗体文本**
*斜体文本*
~~删除线~~
`行内代码`
```

### 3.3 列表

**无序列表：**

```markdown
- 项目一
- 项目二
  - 子项目 2.1
- 项目三
```

**有序列表：**

```markdown
1. 第一步
2. 第二步
3. 第三步
```

### 3.4 代码块

```markdown
```javascript
function hello() {
  console.log('Hello, World!');
}
```
```

### 3.5 引用

```markdown
> 这是一段引用文本
> 可以多行
```

### 3.6 表格

```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容1 | 内容2 | 内容3 |
```

### 3.7 链接和图片

```markdown
[链接文本](https://example.com)

![图片描述](/path/to/image.png)
```

---

## 四、插入图片

### 4.1 图片存放位置

本博客已启用 `post_asset_folder: true`，每篇文章可以有一个同名文件夹存放图片。

**目录结构：**

```
source/_posts/tech-study/
├── ts-ocr模型生产环境部署.md        # 文章文件
└── ts-ocr模型生产环境部署/          # 资源文件夹（与文章同名）
    ├── architecture.png            # 架构图
    └── screenshot.png              # 截图
```

### 4.2 插入图片的方法

**方法一：使用 asset_img 标签（推荐）**

```markdown
{% asset_img architecture.png 系统架构图 %}
```

**方法二：使用相对路径**

```markdown
![系统架构图](ts-ocr模型生产环境部署/architecture.png)
```

---

## 五、本地预览

### 5.1 启动本地服务器

```bash
# 清理 + 生成 + 启动（推荐）
hexo clean && hexo generate && hexo server
```

### 5.2 访问预览

打开浏览器访问 `http://localhost:4000`

---

## 六、发布到仓库

### 6.1 发布流程

```bash
# 1. 查看修改状态
git status

# 2. 添加所有修改
git add .

# 3. 提交修改
git commit -m "New post: 文章标题"

# 4. 推送到远程仓库
git push
```

### 6.2 自动部署

推送后，GitHub Actions 会自动触发部署流程，大约 1-3 分钟后即可看到新文章。

---

## 总结

写一篇博客的完整流程：

```
创建文章 → 编辑内容 → 添加图片 → 本地预览 → 提交推送 → 自动部署
```

**关键要点：**

1. ✅ 使用自定义命令 `hexo np` 创建文章
2. ✅ 手动指定一级前缀、二级前缀和标题
3. ✅ 填写完整的 Front Matter
4. ✅ 图片放在同名资源文件夹
5. ✅ 本地预览确认无误
6. ✅ 推送后等待自动部署

---

*写作是最好的学习方式，开始你的第一篇博客吧！*