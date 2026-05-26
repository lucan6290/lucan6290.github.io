# Hexo 博客图片资源管理指南

## 图片存储目录结构

```
source/img/
├── covers/          # 文章封面图
│   ├── agent-learning.svg
│   ├── hexo-setup.svg
│   └── job-hunting.svg
├── posts/           # 文章内嵌图片（架构图、流程图、截图等）
│   └── .gitkeep
├── avatar.svg       # 头像
├── default-cover.svg # 默认封面
└── favicon.svg      # 网站图标
```

## Hexo 图片引用方式

### 1. 文章封面图
在文章 front matter 中设置：
```yaml
cover: /img/covers/your-cover.svg
```

### 2. Markdown 内嵌图片
使用 Hexo 的 `asset_img` 标签（推荐）：
```markdown
{% asset_img architecture.png 系统架构图 %}
```
或使用相对路径（需开启 `post_asset_folder`）：
```markdown
![架构图](architecture.png)
```

### 3. 绝对路径引用
```markdown
![流程图](/img/posts/flowchart.png)
```

## 最佳实践

### 技术文章图片分类
1. **架构图** - 系统架构、组件关系图
2. **流程图** - 算法流程、工作流程
3. **终端截图** - 命令执行、输出结果
4. **代码截图** - 关键代码片段
5. **数据图表** - 性能对比、趋势图

### 命名规范
- 英文小写，用连字符分隔
- 包含文章主题和图片类型
- 示例：`agent-architecture.svg`, `hexo-install-screenshot.png`

### 图片优化
- 流程图用 SVG 格式（矢量图，清晰度高）
- 截图用 WebP 或 PNG 格式
- 大图压缩到合适尺寸（建议宽度 ≤ 1200px）

## Hexo 配置说明

`_config.yml` 中已开启：
```yaml
post_asset_folder: true  # 自动为每篇文章创建同名文件夹存放资源
```

这意味着每篇文章的图片可以放在：
```
source/_posts/文章文件名/
├── 文章.md
├── image1.png
└── image2.jpg
```

## 草稿功能
草稿文章放在 `source/_drafts/` 目录，不会发布到网站，便于写作和预览。

## 图片生成工具推荐
1. **Draw.io** - 流程图、架构图
2. **Excalidraw** - 手绘风格图表
3. **Carbon** - 代码截图美化
4. **TinyPNG** - 图片压缩