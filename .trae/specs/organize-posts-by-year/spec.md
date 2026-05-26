# 文章目录组织优化 Spec

## Why

当前博客所有文章都在 `source/_posts/` 单一目录下，随着文章数量增长，文件管理会变得困难。按一级分类组织文章可以：
- 更好地组织内容
- 便于管理和查找
- 与分类体系保持一致

## What Changes

- 提供按一级分类组织文章目录的方案
- 新文章自动按分类存放
- 现有文章可迁移到对应分类目录

## Impact

- Affected specs: 文件组织、文章管理
- Affected code: 
  - `source/_posts/` 目录结构
  - `_config.yml` 中的 `new_post_name` 配置
  - 文章的 front matter 可能需要调整

## ADDED Requirements

### Requirement: 按一级分类组织文章

系统 SHALL 支持按一级分类组织文章目录结构。

**目录结构：**
```
source/_posts/
├── tech-study/           # 技术研习
│   ├── ai-claude-code-入门与安装.md
│   ├── ai-agent-入门笔记.md
│   └── ai-ocr模型生产环境部署.md
├── pitfall-review/       # 踩坑复盘
│   └── ...
├── project-practice/     # 项目实战
│   └── ...
├── growth-essay/         # 成长随笔
│   ├── growth-求职经历总结.md
│   ├── tool-hexo-博客搭建记录.md
│   └── growth-博客文章命名规范.md
└── resource-sharing/     # 资源分享
    └── ...
```

**优点：**
- 与分类体系一致，结构清晰
- 便于按分类管理文章
- 支持分类级别的批量操作

**缺点：**
- 文章可能需要跨分类移动
- 新建文章时需要指定分类目录

### Requirement: 配置支持

系统 SHALL 支持自定义文章存放路径。

**方案一：手动指定路径**
```bash
hexo new "文章标题" --path tech-study/文章标题
```

**方案二：使用 scaffolds 模板**
为每个一级分类创建独立的模板：
```bash
hexo new tech-study "文章标题"  # 自动使用 tech-study 模板
hexo new growth-essay "文章标题"  # 自动使用 growth-essay 模板
```

#### Scenario: 创建新文章时指定分类目录
- **WHEN** 运行 `hexo new "文章标题" --path tech-study/文章标题`
- **THEN** 文章创建在 `source/_posts/tech-study/` 目录下

#### Scenario: 使用分类模板创建文章
- **WHEN** 运行 `hexo new tech-study "文章标题"`
- **THEN** 文章自动创建在对应分类目录，并预设分类字段

## MODIFIED Requirements

无

## REMOVED Requirements

无

## 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| 按年份组织 | 时间线清晰 | 与内容无关 |
| 按一级分类组织 | 与内容相关，便于管理 | 需要手动指定路径 |
| 保持现状 | 无需改动 | 文件多时查找困难 |

**推荐：按一级分类组织**
