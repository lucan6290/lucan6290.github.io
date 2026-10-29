# 原生启动器

`src/lib.rs` 负责定位当前项目、固定 18000 本机连接、会话校验和自有后端进程生命周期。

- 根目录依据 `frontend/content` 与 `admin-desktop`，显式环境变量 `LUCHUAN_PROJECT_ROOT` 优先且必须有效。
- 读取 `.codex-tmp/admin-desktop/session.json`，核对 `/health` 身份、根目录并实际检查认证，禁止打印 token。
- 不换端口，不接入其他项目服务，不终止外部启动的服务。
- 开发子进程隐藏启动并保留 reload；Windows Job 管理完整自有进程树，清理在真正退出时执行，不能在可取消的 CloseRequested 事件杀后端。
- 编辑器确认关闭需要 `core:window:allow-destroy`，权限配置见 capabilities/default.json。
- 正式 sidecar 打包未配置时给出明确错误，不声称生产包可自动启动后端。

验证 `cargo fmt --check`、`cargo check --offline`、`cargo test --offline`。
