# data/content-schema — AGENTS.md

> 内容规则中心（事实源）。

## 内容

- `categories.yml`：分类注册表（显示名、排序、启用、别名、封面）
- `tags.yml`：标签注册表
- `blog_template.md` / `dacs_template.md`：文章模板

## 约定

- 前端不硬编码分类/标签中文名，以后端接口转换结果为准。
- 详见 `admin/docs/管理端前端数据规则.md`。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
