# tests — AGENTS.md

> pytest 回归测试。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md` 第 11 节。

## 约定

- pytest，文件名 `test_*.py`，`addopts=-ra`。
- 契约测试命名 `test_*_api_contracts.py`。
- 工作流/回滚测试：`test_docs_article_workflow.py`、`test_blog_sidebar_and_nav.py`、`test_article_move.py`、`test_category_delete.py`。

## 运行

```powershell
cd admin/backend
python -m pytest
```

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
