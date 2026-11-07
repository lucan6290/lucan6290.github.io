# 桌面 Git 工作区实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 从桌面端检查和选择 Git 变更，并显式确认本地提交、更新、推送和站点发布。

**Architecture:** 独立 Git 模块处理仓库、预览和操作；FastAPI 复用会话鉴权；Vue 复用现有请求与主题。

**Tech Stack:** Python 3.10+、Git、GitHub CLI、FastAPI、Vue 3、TypeScript。

**Spec:** [桌面 Git 工作区设计与接口契约](../../../admin-desktop/docs/Git工作区契约.md)

## 全局边界

独立工作树内修改。测试只操作临时 Git 仓库与本地裸远端。保留用户现有暂存，无自动更新，不访问真实发布接口。

## 实施和验证

- [x] 先写临时仓库回归，验证状态、双侧差异、首提交、混合暂存、中文和字面路径、预览过期或变动、冲突、推送、快进更新及派发确认。运行失败后实现 `git_workspace.py`，再运行相同测试。
- [x] 用测试应用挂载 `create_git_router(project_root)`，验证接口形状、严格确认和稳定错误。由集成分支复用 `app.py` 的 Bearer 鉴权与 HTTP 请求助手。
- [x] 实现 `src/api/gitWorkspace.ts`、`src/views/GitWorkspace.vue`。沿用桌面主题，把文件选择和差异并排，操作预览独立展示范围。验证 `npm test` 与 `npm run build`。
- [x] 运行完整 Python 回归与 `git diff --check`，核对测试结果及精确文件清单，创建本地功能提交。
