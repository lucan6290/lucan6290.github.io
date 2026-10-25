# services/site — AGENTS.md

> 构建/部署/Git 同步。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 内容

- `build_service.py`：执行 Docusaurus 构建
- `deploy_service.py`：部署
- `git_sync_service.py`：Git 同步

## 约定

- 执行 `npm run build`、git 等外部命令。
- 危险操作走 `dry_run` / `confirm`。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
