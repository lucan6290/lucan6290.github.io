# application/content/workflows — AGENTS.md

> 内容工作流（编排 + 快照回滚）。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md` 第 10 节，链路见 `admin/docs/内容工作流接口说明.md`。

## 职责

跨文件/跨服务的文章创建编排：先快照，再写文件、同步侧边栏/首页/导航/索引，失败按快照回滚。

## 内容

- `article_workflow.py`：按 `type` 分发。
- `docs_article_workflow.py`：docs 文章创建。
- `blog_article_workflow.py`：blog 文章创建。
- `category_workflow.py`：分类创建。
- `utils.py`：工作流工具。

## 约定

- 单一能力服务放 services；跨文件跨服务带回滚放这里。
- 回滚策略与测试见 `tests/test_docs_article_workflow.py`、`tests/test_blog_sidebar_and_nav.py`。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
