---
title: 从零开始写一篇博客 —— 完整写作指南
date: 2026-05-25 10:00:00
categories:
  - [成长随笔, 博客建设]
tags: [blog, hexo, markdown, 写作指南, 教程]
description: 一篇手把手教你如何从零开始写完一篇完整博客的指南，包括创建文章、选择分类、命名规范、Markdown 语法、图片插入、本地预览和发布到仓库的完整流程。
---

## 前言

本文将手把手教你如何从零开始写一篇完整的博客文章，涵盖从创建到发布的全流程。无论你是第一次写博客，还是想了解本博客的写作规范，这篇文章都能帮到你。

---

## 一、创建新文章

### 1.1 使用分类模板创建（推荐）

本博客已配置按一级分类组织文章目录，使用分类模板可以自动将文章创建在对应目录。

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
# 创建一篇 Vue 3 教程文章
hexo new tech-study "Vue 3 组合式 API 详解"

# 创建一篇环境配置踩坑文章
hexo new pitfall-review "Docker 环境配置踩坑"

# 创建一篇年终总结
hexo new growth-essay "2026 年终技术总结"
```

### 1.2 文章命名规范

文件名格式：`[一级分类前缀]-[二级分类前缀]-[具体主题].md`

#### 1.2.1 一级分类前缀对照表

| 前缀 | 一级分类 | 适用场景 |
|------|---------|---------|
| `tech-` | 技术研习 | 技术学习、教程、原理分析 |
| `pitfall-` | 踩坑复盘 | 问题解决、踩坑记录 |
| `project-` | 项目实战 | 项目开发、实战案例 |
| `growth-` | 成长随笔 | 个人感悟、求职经验 |
| `resource-` | 资源分享 | 工具推荐、资源整理 |

#### 1.2.2 二级分类前缀规则

二级分类前缀**灵活定义**，用于标识文章所属的技术栈、工具、项目或主题。

**命名原则：**

1. **按技术栈命名**：使用技术/工具的英文名或缩写
2. **按项目命名**：使用项目代号或简称
3. **按主题命名**：使用主题关键词

**示例：**

| 二级分类前缀 | 说明 | 适用文章 |
|-------------|------|---------|
| `vue3-` | Vue 3 相关 | Vue 3 教程、原理、实战 |
| `react-` | React 相关 | React Hooks、状态管理 |
| `claude-` | Claude 开发工具 | Claude 安装、使用、技巧 |
| `cursor-` | Cursor 编辑器 | Cursor 配置、快捷键、插件 |
| `hexo-` | Hexo 博客 | Hexo 搭建、主题、插件 |
| `docker-` | Docker 容器 | Docker 安装、配置、实战 |
| `mysql-` | MySQL 数据库 | MySQL 优化、运维、问题 |
| `blog-` | 博客项目 | 博客开发日志、功能实现 |

**完整命名示例：**

```bash
# 技术研习
tech-vue3-响应式原理详解.md           # Vue 3 相关
tech-claude-开发环境配置.md           # Claude 工具相关
tech-cursor-快捷键速查.md             # Cursor 编辑器相关
tech-docker-容器网络配置.md           # Docker 相关

# 踩坑复盘
pitfall-docker-容器启动失败排查.md    # Docker 踩坑
pitfall-mysql-索引失效分析.md         # MySQL 踩坑
pitfall-nodejs-版本冲突解决.md        # Node.js 踩坑

# 项目实战
project-blog-用户认证功能实现.md      # 博客项目
project-shop-订单模块开发日志.md      # 商城项目

# 成长随笔
growth-career-求职经历总结.md         # 求职相关
growth-learn-高效学习方法.md          # 学习方法

# 资源分享
resource-claude-常用提示词合集.md     # Claude 资源
resource-vue3-组件库推荐.md           # Vue 3 资源
```

#### 1.2.3 二级分类前缀速查表

以下是常用的二级分类前缀，可根据需要自由扩展：

**前端技术：**

| 前缀 | 技术 |
|------|------|
| `vue2-` / `vue3-` | Vue |
| `react-` | React |
| `angular-` | Angular |
| `ts-` / `typescript-` | TypeScript |
| `js-` / `javascript-` | JavaScript |
| `css-` | CSS |
| `webpack-` | Webpack |
| `vite-` | Vite |

**后端技术：**

| 前缀 | 技术 |
|------|------|
| `node-` / `nodejs-` | Node.js |
| `spring-` / `springboot-` | Spring Boot |
| `django-` | Django |
| `flask-` | Flask |
| `go-` / `golang-` | Go |
| `java-` | Java |

**数据库：**

| 前缀 | 技术 |
|------|------|
| `mysql-` | MySQL |
| `redis-` | Redis |
| `mongodb-` | MongoDB |
| `postgresql-` | PostgreSQL |

**AI/工具：**

| 前缀 | 技术/工具 |
|------|---------|
| `ai-` | AI 通用 |
| `llm-` | 大语言模型 |
| `claude-` | Claude |
| `cursor-` | Cursor |
| `copilot-` | GitHub Copilot |
| `chatgpt-` | ChatGPT |

**运维/部署：**

| 前缀 | 技术 |
|------|------|
| `docker-` | Docker |
| `k8s-` / `kubernetes-` | Kubernetes |
| `nginx-` | Nginx |
| `linux-` | Linux |
| `ci-` | CI/CD |

**成长随笔专用：**

| 前缀 | 主题 |
|------|------|
| `career-` | 求职之路 |
| `interview-` | 面试相关 |
| `learn-` | 学习方法 |
| `read-` | 读书笔记 |
| `annual-` | 年度总结 |
| `blog-` | 博客建设 |

#### 1.2.4 命名注意事项

```bash
# ✅ 正确示例
tech-vue3-组合式API详解.md
tech-claude-提示词编写技巧.md
pitfall-docker-容器网络踩坑.md

# ❌ 错误示例
tech-vue3.md                      # 缺少具体主题
vue3-组合式API.md                 # 缺少一级分类前缀
tech_vue3_组合式API.md            # 使用下划线分隔
tech-vue3-组合式API详解教程入门笔记.md  # 太长，超过60字符
```

**长度建议：**
- 理想长度：15-40 个字符
- 最大长度：不超过 60 个字符

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

### 2.3 分类层级说明

```yaml
# 一级分类 + 二级分类
categories:
  - [技术研习, 入门笔记]

# 一级分类 + 二级分类 + 三级分类
categories:
  - [技术研习, 前端技术, Vue]

# 仅一级分类
categories:
  - [成长随笔]
```

**一级分类与二级分类对应关系：**

| 一级分类 | 常用二级分类 |
|---------|-------------|
| 技术研习 | 入门笔记、进阶教程、原理探究、源码解读、AI 探索 |
| 踩坑复盘 | 环境配置、代码调试、工程问题、部署运维 |
| 项目实战 | 项目介绍、架构设计、开发日志、功能实现、项目总结 |
| 成长随笔 | 求职之路、面试真题、学习方法、博客建设、年度总结 |
| 资源分享 | 工具推荐、学习资源、代码片段、cheatsheet |

### 2.4 内容分级（status 字段）

| 状态 | 值 | 说明 |
|------|------|------|
| 草稿 | `draft` | 刚开始写，部署时自动排除 |
| 半成品 | `wip` | Work In Progress，页面显示施工中提示 |
| 正式文章 | `published` | 完成度高（默认值，可省略） |

**示例：**

```yaml
---
title: 某某技术深入解析
date: 2026-05-25 10:00:00
categories:
  - [技术研习, 原理探究]
tags: [标签1, 标签2]
description: 文章简介...
status: wip    # 表示文章还在施工中
---
```

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

**效果：**

**粗体文本** *斜体文本* ~~删除线~~ `行内代码`

### 3.3 列表

**无序列表：**

```markdown
- 项目一
- 项目二
  - 子项目 2.1
  - 子项目 2.2
- 项目三
```

**有序列表：**

```markdown
1. 第一步
2. 第二步
3. 第三步
```

**任务列表：**

```markdown
- [x] 已完成
- [ ] 未完成
- [ ] 待处理
```

### 3.4 代码块

**基本语法：**

```markdown
```javascript
function hello() {
  console.log('Hello, World!');
}
```
```

**常用语言标识：**

| 语言 | 标识 |
|------|------|
| JavaScript | `javascript` 或 `js` |
| TypeScript | `typescript` 或 `ts` |
| Python | `python` 或 `py` |
| Java | `java` |
| Go | `go` |
| Rust | `rust` |
| Bash/Shell | `bash` 或 `shell` |
| YAML | `yaml` |
| JSON | `json` |
| SQL | `sql` |

### 3.5 引用

```markdown
> 这是一段引用文本
> 可以多行
```

**效果：**

> 这是一段引用文本
> 可以多行

### 3.6 表格

```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容1 | 内容2 | 内容3 |
| 内容4 | 内容5 | 内容6 |
```

**效果：**

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容1 | 内容2 | 内容3 |
| 内容4 | 内容5 | 内容6 |

### 3.7 链接和图片

```markdown
[链接文本](https://example.com)

![图片描述](/path/to/image.png)
```

### 3.8 分割线

```markdown
---

***

___
```

三种写法效果相同，都生成分割线。

### 3.9 Butterfly 主题特殊语法

**Note 提示框：**

```markdown
{% note default %}
默认提示
{% endnote %}

{% note primary %}
主要提示
{% endnote %}

{% note success %}
成功提示
{% endnote %}

{% note warning %}
警告提示
{% endnote %}

{% note danger %}
危险提示
{% endnote %}

{% note info %}
信息提示
{% endnote %}
```

**折叠区块：**

```markdown
{% fold 点击展开 %}

隐藏的内容

{% endfold %}
```

---

## 四、插入图片

### 4.1 图片存放位置

本博客已启用 `post_asset_folder: true`，每篇文章可以有一个同名文件夹存放图片。

**目录结构：**

```
source/_posts/tech-study/
├── ai-ocr模型生产环境部署.md        # 文章文件
└── ai-ocr模型生产环境部署/          # 资源文件夹（与文章同名）
    ├── architecture.png            # 架构图
    ├── flowchart.png               # 流程图
    └── screenshot.png              # 截图
```

### 4.2 插入图片的方法

**方法一：使用 asset_img 标签（推荐）**

```markdown
{% asset_img architecture.png 系统架构图 %}
```

**方法二：使用相对路径**

```markdown
![系统架构图](ai-ocr模型生产环境部署/architecture.png)
```

**方法三：使用 Markdown 标准语法**

```markdown
![系统架构图](./ai-ocr模型生产环境部署/architecture.png)
```

### 4.3 图片命名规范

| 图片类型 | 命名建议 | 示例 |
|---------|---------|------|
| 架构图 | `architecture.png` | `architecture.png` |
| 流程图 | `flow-xxx.png` | `flow-deploy.png` |
| 截图 | `screenshot-xxx.png` | `screenshot-homepage.png` |
| 代码截图 | `code-xxx.png` | `code-error.png` |
| 对比图 | `compare-xxx.png` | `compare-before-after.png` |

### 4.4 图片优化建议

1. **格式选择**：
   - 截图、照片 → PNG 或 JPG
   - 图标、简单图形 → SVG
   - 动图 → GIF 或 WebP

2. **尺寸控制**：
   - 宽度不超过 1200px
   - 文件大小控制在 500KB 以内

3. **压缩工具**：
   - [TinyPNG](https://tinypng.com/) - 在线压缩
   - [Squoosh](https://squoosh.app/) - Google 出品

---

## 五、本地预览

### 5.1 启动本地服务器

```bash
# 方式一：清理 + 生成 + 启动（推荐）
hexo clean && hexo generate && hexo server

# 方式二：简写
hexo clean && hexo g && hexo s

# 方式三：仅启动（快速预览，可能缓存旧内容）
hexo server
```

### 5.2 访问预览

打开浏览器访问 `http://localhost:4000`

### 5.3 停止服务器

在终端按 `Ctrl + C` 停止服务

### 5.4 常见问题

**端口被占用：**

```bash
# Windows 查看占用 4000 端口的进程
netstat -ano | findstr :4000

# 停止进程（替换 PID）
taskkill /PID 进程号 /F
```

**修改不生效：**

```bash
# 清理缓存重新生成
hexo clean
hexo generate
```

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

推送后，GitHub Actions 会自动触发部署流程：

1. 进入 GitHub 仓库页面
2. 点击 `Actions` 标签
3. 查看工作流运行状态
4. 显示绿色 ✓ 表示部署成功

大约 1-3 分钟后，访问 `https://你的用户名.github.io` 即可看到新文章。

### 6.3 提交信息规范

```bash
# 新文章
git commit -m "New post: Vue 3 组合式 API 详解"

# 更新文章
git commit -m "Update: OCR 模型部署文档"

# 修复问题
git commit -m "Fix: 修复图片路径错误"

# 配置修改
git commit -m "Config: 更新主题配置"
```

---

## 七、完整示例

### 7.1 创建文章

```bash
hexo new tech-study "Vue 3 响应式原理详解"
```

### 7.2 编辑文章

```markdown
---
title: Vue 3 响应式原理详解
date: 2026-05-25 10:00:00
categories:
  - [技术研习, 原理探究]
tags: [vue3, reactivity, 原理, 前端]
description: 深入分析 Vue 3 响应式系统的实现原理，包括 Proxy、依赖收集、触发更新等核心机制。
---

## 前言

Vue 3 的响应式系统相比 Vue 2 有了根本性的改变...

## 一、响应式基础

### 1.1 什么是响应式

响应式是指当数据发生变化时，视图自动更新...

```javascript
const count = ref(0)
count.value++  // 视图自动更新
```

### 1.2 Proxy vs Object.defineProperty

| 特性 | Proxy | Object.defineProperty |
|------|-------|----------------------|
| 监听新增属性 | ✅ 支持 | ❌ 不支持 |
| 监听删除属性 | ✅ 支持 | ❌ 不支持 |
| 性能 | 更优 | 一般 |

{% asset_img reactivity-flow.png 响应式流程图 %}

## 二、依赖收集

### 2.1 effect 函数

...

## 总结

Vue 3 的响应式系统基于 Proxy 实现...

---

*参考文档：[Vue 3 官方文档](https://vuejs.org/)*
```

### 7.3 添加图片

```bash
# 创建资源文件夹（如果不存在）
mkdir source/_posts/tech-study/Vue\ 3\ 响应式原理详解

# 将图片复制到资源文件夹
cp ~/Downloads/reactivity-flow.png source/_posts/tech-study/Vue\ 3\ 响应式原理详解/
```

### 7.4 本地预览

```bash
hexo clean && hexo g && hexo s
```

访问 `http://localhost:4000` 检查效果。

### 7.5 发布

```bash
git add .
git commit -m "New post: Vue 3 响应式原理详解"
git push
```

---

## 八、常见问题

### Q1：文章没有出现在博客上？

**检查清单：**

1. 文件是否在正确的目录？
2. Front Matter 格式是否正确？
3. 是否设置了 `status: draft`？
4. 是否执行了 `hexo clean && hexo g`？

### Q2：图片显示不出来？

**检查清单：**

1. 资源文件夹名称是否与文章文件名完全一致？
2. 图片路径是否正确？
3. 图片文件是否存在？
4. 是否使用了正确的引用语法？

### Q3：本地预览正常，线上不显示？

**原因：** GitHub Actions 部署可能还在进行中

**解决：** 等待 1-3 分钟，或检查 Actions 页面是否有报错

### Q4：如何修改已发布的文章？

1. 直接编辑 `.md` 文件
2. 本地预览确认无误
3. `git add . && git commit -m "Update: 文章标题" && git push`

---

## 总结

写一篇博客的完整流程：

```
创建文章 → 编辑内容 → 添加图片 → 本地预览 → 提交推送 → 自动部署
```

**关键要点：**

1. ✅ 使用分类模板创建文章
2. ✅ 遵循命名规范
3. ✅ 填写完整的 Front Matter
4. ✅ 图片放在同名资源文件夹
5. ✅ 本地预览确认无误
6. ✅ 推送后等待自动部署

---

*写作是最好的学习方式，开始你的第一篇博客吧！*
