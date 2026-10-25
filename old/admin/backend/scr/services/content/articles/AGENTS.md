# services/content/articles — AGENTS.md

> 文章业务服务。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

文章的查询/详情/保存/删除/移动/图片/校验/引用等单一能力服务。

## 内容

article_service / article_query_service / article_detail_service / article_save_service / article_delete_service / article_move_service / article_move_target_service / article_image_* / article_validation_service / article_frontmatter_validation_service / article_summary_service / article_path_service / article_id_service / article_reference_service / article_mutation_service / blog_article_service / docs_article_service 等。

## 约定

- 单一能力一个 service 文件（`xxx_service.py`）。
- 跨文件编排放 `application/content/workflows/`。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
