# Tasks

- [x] Task 1: 设计内容分级策略文档
  - [x] SubTask 1.1: 确定状态字段名称和可选值
  - [x] SubTask 1.2: 定义每种状态的展示规则
  - [x] SubTask 1.3: 确定默认行为（未指定 status 时）

- [x] Task 2: 创建 Hexo 脚本处理草稿文章
  - [x] SubTask 2.1: 创建脚本在生成时排除 `status: draft` 的文章
  - [x] SubTask 2.2: 确保本地预览（hexo server）时可以看到草稿

- [x] Task 3: 为 WIP 文章添加视觉标识
  - [x] SubTask 3.1: 通过 CSS 或模板添加 WIP 标识样式
  - [x] SubTask 3.2: 在文章标题或顶部显示标识

- [x] Task 4: 更新现有文章
  - [x] SubTask 4.1: 检查现有文章的完成状态
  - [x] SubTask 4.2: 为现有文章添加合适的 status 字段

- [x] Task 5: 更新博客规范文档
  - [x] SubTask 5.1: 在博客长期发展规范中添加内容分级策略说明

# Task Dependencies

- Task 2 依赖 Task 1（需要先确定状态定义）
- Task 3 依赖 Task 1
- Task 4 依赖 Task 1 和 Task 2
- Task 5 依赖 Task 1
