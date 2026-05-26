# 博客内容分级策略 Spec

## Why

当前博客没有明确的内容分级策略，草稿、半成品、正式文章混在一起，无法区分文章的完成状态，影响读者体验和内容管理。

## What Changes

- 建立三级内容分级体系：草稿（Draft）、半成品（WIP）、正式文章（Published）
- 在文章 front matter 中添加 `status` 字段标识文章状态
- 不同状态的文章在站点中有不同的展示方式
- 提供筛选和隐藏未完成文章的能力

## Impact

- Affected specs: 文章管理、站点展示
- Affected code: 
  - `source/_posts/` 目录下的所有文章
  - 可能需要新增 Hexo 脚本处理状态过滤
  - 可能需要修改主题模板展示状态标识

## ADDED Requirements

### Requirement: 内容分级状态字段

系统 SHALL 支持在文章 front matter 中使用 `status` 字段标识文章状态。

**状态定义：**
| 状态 | 值 | 说明 |
|------|------|------|
| 草稿 | `draft` | 刚开始写，内容不完整，不应公开 |
| 半成品 | `wip` | Work In Progress，主要内容已有，但细节待完善 |
| 正式文章 | `published` | 完成度高，可以公开发布 |

**默认值：** 如果未指定 `status`，默认为 `published`

#### Scenario: 创建草稿文章
- **WHEN** 用户创建新文章并设置 `status: draft`
- **THEN** 该文章在生成站点时被排除或标记为草稿状态

#### Scenario: 创建半成品文章
- **WHEN** 用户创建文章并设置 `status: wip`
- **THEN** 该文章在站点中显示"WIP"标识，提示读者内容仍在完善中

#### Scenario: 创建正式文章
- **WHEN** 用户创建文章并设置 `status: published` 或不设置 status
- **THEN** 该文章正常显示，无额外标识

### Requirement: 草稿文章处理

系统 SHALL 在生成站点时排除 `status: draft` 的文章，不将其发布到公开站点。

#### Scenario: 生成站点时排除草稿
- **WHEN** 运行 `hexo generate` 或 `hexo deploy`
- **THEN** 所有 `status: draft` 的文章不会被生成到 `public/` 目录

### Requirement: 半成品文章标识

系统 SHALL 为 `status: wip` 的文章添加明显的视觉标识。

#### Scenario: 显示 WIP 标识
- **WHEN** 读者访问 `status: wip` 的文章
- **THEN** 文章标题或顶部显示"WIP"或"施工中"标识

### Requirement: 状态筛选能力

系统 SHALL 提供在本地预览时查看不同状态文章的能力。

#### Scenario: 本地预览包含所有状态
- **WHEN** 运行 `hexo server` 本地预览
- **THEN** 可以看到所有状态的文章（包括 draft 和 wip）

## MODIFIED Requirements

无

## REMOVED Requirements

无
