# admin-desktop — 开发导航

桌面管理端直接管理 `../frontend/content`。先读 `README.md`、`docs/内容接口契约.md`、`docs/DOCUMENTATION_INDEX.md`，内容规则以 `../frontend/README.md` 和扫描回归为准。

- `src/`：Vue 壳、目录列表、原文编辑器与冲突状态，见 `src/AGENTS.md`。
- `src-backend/`：独立 Python/FastAPI 内容服务，见该目录 `AGENTS.md`。不得导入 `old/admin`。
- `src-tauri/`：本机连接与自有进程生命周期，见该目录 `AGENTS.md`。
- 内容唯一事实源为 Markdown；不直接编辑 `frontend/src/generated`，不维护旧站注册表/侧边栏。
- 固定端口：桌面开发 14200、内容后端 18000，新前台 3400。后端开发保留 `--reload`。
- 新建排他、保存/删除版本校验、外部变化不覆盖未保存缓冲；写入测试用临时根。
- 第二阶段能力尚未适配时保持明确不可用，不调用旧接口或伪造成功。
- 用户已有改动不得覆盖，不自行提交 Git。

验证：`npm test`、`npm run build`；项目根运行 `python -m unittest discover -s admin-desktop/src-backend/tests -v`；原生 `cargo test --offline`（在 src-tauri）。
