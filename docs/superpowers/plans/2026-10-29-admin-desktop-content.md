# 桌面内容适配第一阶段 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox syntax for tracking. 用户已确认实施第一阶段，无需重复请求实施授权。

**Goal:** 独立启动桌面内容后端，可靠新建、编辑与删除 frontend/content 文档，保护与编辑器、AI 交替操作时的未保存内容。

**Architecture:** Python 内容仓库负责路径、原文、版本和写入，FastAPI 暴露本机会话接口。Vue 使用独立 contentApi 和编辑会话状态，Tauri 只负责连接及自有进程生命周期。已固定契约后后端与编辑器可分配给独立工作者，主执行者负责列表、启动及集成。

**Tech Stack:** 现有 Vue 3 / TypeScript / Tauri 2 / Python / FastAPI / PyYAML；不迁移技术栈。

**Spec:** `docs/superpowers/specs/2026-10-29-admin-desktop-content-design.md`

## Global Constraints

- 仅实施第一阶段；图片、移动、AI、发布显示尚未适配。
- 不导入 old/，不触碰用户已有前台改动；不提交或修改 Git 历史，直接在用户指定工作区实施。
- 后端 18000、桌面开发 14200，开发后端使用 reload；新前台仍为 3400。
- 写入测试使用临时内容根；真实文档只读。
- 契约：`admin-desktop/docs/内容接口契约.md`；前后端使用相同字段名，不维持旧模型映射。

## Review Focus

- CRLF/BOM 经 textarea 后规范化造成整文件变化 → 编辑会话往返测试。
- 外部写入/删除和已发起的异步读取晚到 → 版本与会话切换测试。
- 同名创建、保存失败或版本冲突意外截断目标 → 后端临时目录集成测试。
- README、隐藏路径、资源与空目录和前台不同 → 共用场景对照测试。
- 端口占用时连接到错误项目、退出误杀外部服务 → 启动器检查与手动集成验证。

### Task 1: 独立内容后端

Files: 创建 `admin-desktop/src-backend/content_store.py`、`app.py`、`tests/test_content.py`、模块 AGENTS；修改 `main.py`、`requirements.txt`。

Interfaces: 按内容接口契约实现端点；`create_app(project_root: Path, token: str)` 用于测试与启动。`main.py --project-root ROOT --port 18000 [--reload] [--session-file PATH]`。外部依赖仅 fastapi、uvicorn、pydantic、PyYAML、httpx（测试）。

- [x] 编写测试：真实原文往返、数组/嵌套 YAML、不含头部、版本冲突、排他创建、安全路径、README/空目录、原子替换失败不改原文件。
- [x] 运行 `python -m unittest discover -s admin-desktop/src-backend/tests -v` 确认缺失功能导致失败。
- [x] 实现仓库与 HTTP 层，运行测试至通过。
- [x] 用临时内容样例与前台扫描规则对照，记录差异而不改前台。

### Task 2: 编辑会话与编辑器

Files: 创建 `src/types/content.ts`、`src/api/content.ts`、`src/utils/documentSession.ts`、`src/utils/documentSession.test.ts`、测试脚本；修改 `src/views/Editor.vue`、`package.json`（test script）。

Interfaces: contentApi `{health, list, read, version, create, save, remove, createDirectory}` 均对应契约；setContentConnection(base_url,token)。编辑器 URL 继续使用 `/editor?id=相对路径`，无 id 为新建，可用 query.directory 预选目录。

- [x] 会话测试先证明 BOM/CRLF 往返、脏缓冲遇外部更新不覆盖、删除保留、基线不被轮询推进、过期响应不能污染新文件。
- [x] 先运行失败测试，再实现纯状态模块与原始文本 API。
- [x] 编辑器接入目录选择、实际文件名、保存/另存、外部变更对照、复制及明确重载。
- [x] 加入 2 秒版本检查与焦点刷新、路由及窗口关闭保护；保存失败保留缓冲且阻止离开。
- [x] 运行 `npm test` 与 `npm run build` 验证。

### Task 3: 列表与桌面连接集成

Files: 修改 `src/views/Posts.vue`、`Dashboard.vue`、`Settings.vue`、`src/router.ts`、`src/App.vue`、`src/stores/app.ts`、`src/vite-env.d.ts`、`src-tauri/src/lib.rs`；新增 `src/views/Unavailable.vue`、相关导航文档。

Interfaces: 消费 Task 1/2 契约；Tauri 命令 `get_backend_connection -> {base_url, token, content_root}`，应用连接后再加载路由。关闭保护由编辑器注册处理；生命周期仅清理自有后端。

- [x] 列表支持目录、动态栏目、README 区分、显式建目录及版本化单文档删除；焦点刷新。
- [x] 仪表盘改用当前内容统计；禁用旧站配置、媒体、AI 功能；移除注册表入口。
- [x] 根目录发现改为 frontend/content；固定 18000 并验证 service/root；读本机会话文件，开发启动 reload，退出清理拥有的进程树。
- [x] 应用自动获取 Tauri 连接，浏览器开发支持输入会话 token；不再注入旧管理员密码。
- [x] 补 README、模块 AGENTS 与根导航，校验构建及 Rust 编译。

### Task 4: 集成验证与审阅

- [x] 运行全部后端和前端测试、桌面构建、前台原有测试；仅在前台差异需要时扩大构建。
- [x] 在临时内容根启动真实 HTTP，验证认证、同名创建、外部改动后 409、删除后 404、原文与前台发现结果。
- [x] 使用浏览器验证路由、保存冲突和离开保护；Tauri 原生生命周期尽可能编译/启动验证，环境限制明确记录。
- [x] 独立审阅新代码并修复关键问题；记录实际证据，不提交 Git。

## Progress

- 需求/方案：用户已确认。
- 契约/架构自检：通过；共享接口与任务边界一致。Task 1 与 Task 2 仅共享契约，无共享可写文件；Task 3 在 Task 2 的 API 文件存在后集成。
- 执行取舍：用户明确授权指定工作区实施，且限制默认只读 Git，不创建分支或 worktree。允许技能要求的独立子任务与审阅，不请求重复审批。

- 第一阶段代码与文档：完成。后端/编辑会话/原生启动分别实现，集成后由独立审阅者检查并复审修复项。
- 验证：锁定依赖后端27、桌面13、前台25、Rust8通过（另1辅助入口ignored）；桌面build、Rust fmt/check/test/build通过。
- 实际验证：浏览器新建目录/中文文档、外部修改409与原文保留、保存失败阻止离开、另存副本、干净文档外部刷新；原生自动连接现有同根服务；真实CLI --reload及重复启动不改旧会话通过。
- 已记录取舍：中文顺序由Vue本机localeCompare处理而不为Python引入ICU；原编辑器实际为textarea，本期保留其源码编辑方式；Windows进程树使用Job控制reload子进程。
- 边界：原生关闭弹窗未完成整段人工交互，保留已核查的监听/权限和自动化生命周期证据。正式安装包侧车及第二阶段未实施，详见验证记录。
- 未提交Git，未修改真实内容文件。保留用户并行产生的其它文档改动。
