# 原生启动器

`src/lib.rs` 负责定位当前项目、固定 18000 本机连接、会话校验和自有后端进程生命周期。

- 开发版以 `frontend/content` 与 `admin-desktop` 定位仓库，显式环境变量 `LUCHUAN_PROJECT_ROOT` 优先且必须有效。安装版由用户选择并记住包含 `frontend/content` 的仓库根目录。
- 开发版会话存放在 `.codex-tmp/admin-desktop/session.json`，安装版存放在本地应用数据目录。两者均核对 `/health` 身份、根目录和认证，禁止打印 token。
- 不换端口，不接入其他项目服务，不终止外部启动的服务。
- 开发子进程隐藏启动并保留 reload；Windows Job 管理完整自有进程树，清理在真正退出时执行，不能在可取消的 CloseRequested 事件杀后端。
- 编辑器确认关闭需要 `core:window:allow-destroy`，权限配置见 capabilities/default.json。
- `npm run tauri:build` 用 `tauri.bundle.conf.json` 把独立内容后端及依赖放入安装包资源。安装版通过应用自己的进程管理启动它，保持固定端口。

验证 `cargo fmt --check`、`cargo check --offline`、`cargo test --offline`。
