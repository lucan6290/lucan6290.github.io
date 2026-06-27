---
title: 定制创建文章命令记录
date: 2026-05-27 13:58:25
updated: 2026-06-08 17:34:50

categories:
  - [成长随笔, 博客建设]

tags:
  - hexo
  - 自定义命令
  - 效率优化
  - 博客建设

description: "记录我为 Hexo 博客定制 `hexo np` 创建文章命令的过程，包括为什么要定制、解决了什么问题、最终效果以及如何实现。"

cover: /img/covers/growth-essay.svg

status: published
---

## 前言

在使用 Hexo 写博客的过程中，我发现每次创建新文章都需要手动处理很多繁琐的事情。为了提高效率，我定制了一个 `hexo np` 命令，自动完成文章创建的全流程。

---

## 一、为什么要定制这个命令？

### 1.1 原始命令的问题

Hexo 默认的 `hexo new` 命令存在以下问题：

| 问题 | 说明 |
|------|------|
| **文件命名不规范** | 直接使用标题作为文件名，不符合我的命名规范 `[前缀]-[前缀]-[主题].md` |
| **目录不自动创建** | 文件创建在 `source/_posts/` 根目录，不会自动放到分类子目录 |
| **Front Matter 不完整** | 只生成基础字段，缺少我需要的 `updated`、`cover`、`status` 等字段 |
| **分类需手动填写** | 每次都要手动填写 `categories`，容易出错 |

### 1.2 我的命名规范

我的博客有严格的命名规范：

```
[一级分类前缀]-[二级分类前缀]-[具体主题].md
```

**示例：**
- `ts-vue3-Vue3组合式API详解.md` — 技术研习 / Vue3
- `pr-docker-Docker环境配置踩坑.md` — 踩坑复盘 / Docker
- `ge-annual-2026年终技术总结.md` — 成长随笔 / 年度总结

**一级分类前缀对照：**

| 前缀 | 一级分类 | 目录 |
|------|---------|------|
| `ts` | 技术研习 | `source/_posts/tech-study/` |
| `pr` | 踩坑复盘 | `source/_posts/pitfall-review/` |
| `pp` | 项目实战 | `source/_posts/project-practice/` |
| `ge` | 成长随笔 | `source/_posts/growth-essay/` |
| `rs` | 资源分享 | `source/_posts/resource-sharing/` |

---

## 二、解决了什么问题？

### 2.1 问题清单

使用 `hexo np` 命令后，以下问题全部解决：

| 原问题 | 解决方案 |
|--------|---------|
| 文件命名不规范 | 自动按规范生成文件名 |
| 目录不自动创建 | 自动创建到对应分类目录 |
| Front Matter 不完整 | 自动生成完整的元数据模板 |
| 分类需手动填写 | 根据参数自动填写分类 |
| cover 需手动填写 | 根据一级分类自动分配 |
| 状态需手动填写 | 默认设置为 `draft` |

### 2.2 效率对比

| 操作 | 使用 `hexo new` | 使用 `hexo np` |
|------|----------------|----------------|
| 创建文件 | 1 步 | 1 步 |
| 重命名文件 | 手动 | 自动 |
| 移动到目录 | 手动 | 自动 |
| 填写 categories | 手动 | 自动 |
| 填写 cover | 手动 | 自动 |
| 添加其他字段 | 手动 | 自动 |
| **总步骤** | **6+ 步** | **1 步** |

---

## 三、最终效果

### 3.1 命令格式

```bash
hexo np <一级前缀> <二级前缀> <标题>
```

### 3.2 使用示例

```bash
# 创建技术研习文章
hexo np ts vue3 "Vue3组合式 API详解"

# 创建踩坑复盘文章
hexo np pr docker "Docker环境配置踩坑"

# 创建成长随笔文章
hexo np ge annual "2026年终技术总结"
```

### 3.3 生成结果

**命令：**
```bash
hexo np ts vue3 "Vue3组合式 API详解"
```

**生成的文件：**
```
source/_posts/tech-study/ts-vue3-Vue3组合式 API详解.md
```

**生成的 Front Matter：**
```yaml
---
title: Vue3组合式 API详解
date: 2026-05-27 13:58:25
updated:

categories:
  - [技术研习, vue3]

tags:

description:

cover: /img/covers/tech-study.svg
sticky:
slug:
status: draft
---

```

### 3.4 自动生成的字段说明

| 字段 | 自动值 | 说明 |
|------|--------|------|
| `title` | 用户输入的标题 | 文章标题 |
| `date` | 当前时间 | 创建时间 |
| `updated` | 空 | 后续更新时填写 |
| `categories` | `[一级分类, 二级前缀]` | 根据参数自动生成 |
| `tags` | 空 | 后续手动填写 |
| `description` | 空 | 后续手动填写 |
| `cover` | `/img/covers/[分类].svg` | 根据一级分类自动分配 |
| `sticky` | 空 | 需要置顶时填写 |
| `slug` | 空 | 需要自定义 URL 时填写 |
| `status` | `draft` | 默认草稿状态 |

---

## 四、如何实现？

### 4.1 脚本位置

在 Hexo 项目中创建脚本文件：

```
scripts/new-post.js
```

Hexo 会自动加载 `scripts/` 目录下的所有 `.js` 文件。

### 4.2 完整代码

```javascript
'use strict';

const path = require('path');
const fs = require('fs');

const PREFIX_TO_DIR = {
  'ts': { dir: 'tech-study', category: '技术研习', cover: '/img/covers/tech-study.svg' },
  'pr': { dir: 'pitfall-review', category: '踩坑复盘', cover: '/img/covers/pitfall-review.svg' },
  'pp': { dir: 'project-practice', category: '项目实战', cover: '/img/covers/project-practice.svg' },
  'ge': { dir: 'growth-essay', category: '成长随笔', cover: '/img/covers/growth-essay.svg' },
  'rs': { dir: 'resource-sharing', category: '资源分享', cover: '/img/covers/resource-sharing.svg' }
};

hexo.extend.console.register('np', '创建新文章（手动指定前缀）', {
  usage: '<一级前缀> <二级前缀> <标题>',
  arguments: [
    { name: '一级前缀', desc: 'ts(技术研习) / pr(踩坑复盘) / pp(项目实战) / ge(成长随笔) / rs(资源分享)' },
    { name: '二级前缀', desc: '技术栈/主题前缀，如 vue3, docker, annual 等' },
    { name: '标题', desc: '文章标题' }
  ]
}, function(args) {
  const hexo = this;
  
  const prefix1 = args._[0];
  const prefix2 = args._[1];
  const title = args._[2];
  
  if (!prefix1 || !prefix2 || !title) {
    console.log('错误: 参数不完整');
    console.log('\n用法: hexo np <一级前缀> <二级前缀> <标题>');
    console.log('\n一级前缀:');
    console.log('  ts - 技术研习 (source/_posts/tech-study/)');
    console.log('  pr - 踩坑复盘 (source/_posts/pitfall-review/)');
    console.log('  pp - 项目实战 (source/_posts/project-practice/)');
    console.log('  ge - 成长随笔 (source/_posts/growth-essay/)');
    console.log('  rs - 资源分享 (source/_posts/resource-sharing/)');
    console.log('\n示例:');
    console.log('  hexo np ts vue3 "Vue3组合式 API详解"');
    console.log('  → source/_posts/tech-study/ts-vue3-Vue3组合式 API详解.md');
    return;
  }
  
  const config = PREFIX_TO_DIR[prefix1];
  if (!config) {
    console.log(`错误: 无效的一级前缀 "${prefix1}"`);
    console.log('可用前缀: ts, pr, pp, ge, rs');
    return;
  }
  
  const fileName = `${prefix1}-${prefix2}-${title}.md`;
  const targetDir = path.join(hexo.source_dir, '_posts', config.dir);
  
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }
  
  const filePath = path.join(targetDir, fileName);
  
  if (fs.existsSync(filePath)) {
    console.log(`错误: 文件已存在: ${filePath}`);
    return;
  }
  
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 19).replace('T', ' ');
  
  const content = `---
title: ${title}
date: ${dateStr}
updated:

categories:
  - [${config.category}, ${prefix2}]

tags:

description:

cover: ${config.cover}
sticky:
slug:
status: draft
---

`;

  fs.writeFileSync(filePath, content);
  
  console.log(`\n✅ 文章创建成功!`);
  console.log(`   文件: ${filePath}`);
  console.log(`   分类: ${config.category} / ${prefix2}`);
  console.log(`   前缀: ${prefix1}-${prefix2}-`);
  console.log(`   状态: draft (草稿)`);
});
```

### 4.3 核心逻辑说明

#### 4.3.1 注册命令

```javascript
hexo.extend.console.register('np', '描述', options, callback);
```

使用 Hexo API 注册自定义控制台命令。

#### 4.3.2 参数解析

```javascript
const prefix1 = args._[0];  // 一级前缀
const prefix2 = args._[1];  // 二级前缀
const title = args._[2];    // 标题
```

`args._` 是 minimist 解析的位置参数数组。

#### 4.3.3 目录创建

```javascript
const targetDir = path.join(hexo.source_dir, '_posts', config.dir);

if (!fs.existsSync(targetDir)) {
  fs.mkdirSync(targetDir, { recursive: true });
}
```

自动创建分类目录（如果不存在）。

#### 4.3.4 文件生成

```javascript
fs.writeFileSync(filePath, content);
```

写入完整的 Front Matter 模板。

### 4.4 如何使用

**步骤：**

1. 将脚本文件保存到 `scripts/new-post.js`
2. 根据你的分类体系修改 `PREFIX_TO_DIR` 配置
3. 根据你的 cover 图片路径修改 `cover` 字段
4. 运行 `hexo np <一级前缀> <二级前缀> <标题>` 创建文章

**自定义配置：**

如果你想使用不同的分类体系，只需修改 `PREFIX_TO_DIR` 对象：

```javascript
const PREFIX_TO_DIR = {
  'tech': { dir: 'tech', category: '技术', cover: '/img/tech.svg' },
  'life': { dir: 'life', category: '生活', cover: '/img/life.svg' },
  // 添加你自己的分类...
};
```

---

## 五、总结

通过定制 `hexo np` 命令，我实现了：

| 成果 | 说明 |
|------|------|
| **效率提升** | 从 6+ 步减少到 1 步 |
| **规范统一** | 所有文章自动符合命名规范 |
| **减少错误** | 分类、目录自动匹配，不会出错 |
| **模板完整** | Front Matter 包含所有需要的字段 |

**核心价值：**

> 把重复的机械操作自动化，把精力集中在内容创作上。

---

## 附录：相关文档

- [Hexo API - Console](https://hexo.io/zh-cn/api/console)
- [博客架构与长期发展规划](ge-blog-博客架构与长期发展规划.md)
- [博客写作完整指南](ge-blog-博客写作完整指南.md)

---

*记录过程，沉淀经验*