# 箓川码笺桌面管理端

基于 Tauri 2 + Vue 3 + 独立 Python 内容服务，直接管理当前仓库的 `frontend/content/`，不依赖旧 `admin/backend` 或 `old/`。

## 当前能力

- 按实际目录和动态栏目管理 Markdown，区分普通文章与 README 目录介绍。
- 显式新建目录，按实际文件名新建文档，编辑完整 Markdown。普通文章自动生成六字段头部，填写标题、摘要后保存；工程说明、设计文档可选择说明用途，README/AGENTS 自动豁免。
- 原文保存保留 YAML 注释、数组、嵌套/未知字段与既有 BOM、换行；没有变化不写盘。具备六字段的普通文章真实修改时维护 updated，保留 date；不猜补历史日期。
- 恢复焦点或每 2 秒检查当前文档的外部变化：未修改时刷新，有本地修改时保留缓冲与原版本。
- 保存/删除携带文件内容版本；冲突拒绝覆盖，提供本地与磁盘对照、复制、明确重载、排他另存。
- 离开编辑器或关闭窗口时可保存、放弃或取消，保存失败不能视为保存成功。

图片管理、文档移动、AI 写作、站点构建预览、Git 发布属于后续适配；当前相关页面明确显示尚未适配。外部编辑器和 AI 可直接修改 Markdown，桌面端会检测变化。

新建普通文章时在源码里填写 title 和 description，正文一级标题与 title 保持一致；未填摘要会拒绝保存。已有文档可选择“本次编辑用途”，说明文档按原文保存；重新打开恢复自动识别，必要时可再次明确用途。完整规则见 `docs/内容接口契约.md`，验证证据见 `docs/六字段文章模板验证记录.md`。

这是同机交替编辑保护。外部工具不参与同一写入协议时，不保证严格同时写入的互斥；不要将它当作多人实时编辑系统。

## 开发启动

先检查端口 `14200` 和 `18000`，不要换端口。新站 `3400` 可独立运行。

依赖：Node.js 22+、Python 3.10+、Rust stable、Windows WebView2/MSVC。推荐将后端环境放在 `src-backend/.venv`，原生启动器优先使用该环境，否则使用 PATH 中的 python。

```powershell
cd admin-desktop
npm install
python -m venv src-backend/.venv
src-backend/.venv/Scripts/python.exe -m pip install -r src-backend/requirements.txt
npm run tauri:dev
```

开发模式自动启动独立后端并保留 `--reload`。启动器检查 18000 服务身份、项目根、内容根及会话；仅连接本项目服务，仅清理自己启动的进程树。固定端口被其他服务占用时给出错误，需先处理占用。

可设置 `LUCHUAN_PROJECT_ROOT` 指向包含 `frontend/content` 与 `admin-desktop` 的项目根；显式路径无效不会猜测另一个项目。

## 浏览器开发

项目根启动后端，另一个终端启动桌面前端：

```powershell
python admin-desktop/src-backend/main.py --project-root . --port 18000 --reload
# 另一个终端
cd admin-desktop
npm run dev
```

打开 `http://127.0.0.1:14200/`。会话令牌在项目根 `.codex-tmp/admin-desktop/session.json` 的 token 字段，填入连接框；不会打印到后端日志。浏览器连接信息仅保留在当前标签的 sessionStorage；后端重启令牌更换时刷新并重新连接。原生应用自动读取本机会话，不需要输入。

## 验证

```powershell
# admin-desktop 目录
npm test
npm run build
# 项目根目录
python -m unittest discover -s admin-desktop/src-backend/tests -v
# admin-desktop/src-tauri 目录
cargo fmt --check
cargo check --offline
cargo test --offline
```

回归写入均使用临时内容根。跨语言测试将同组样例交给新前端扫描器，比对目录、README、隐藏内容、资源目录与标题规则；不写真实内容或前台 generated。

## 打包状态

`npm run build` 构建桌面前端。原生开发启动链路已经独立；安装包的后端 sidecar 尚未配置 externalBin/resources，不能把前端构建或 Rust 编译通过视为安装包已具备后端。正式应用可连接事先启动且身份一致的本项目内容服务；生产自动启动侧车在后续打包工作中完成。

## 文档与源码

- `docs/内容接口契约.md`：当前内容 API 主契约。
- `docs/DOCUMENTATION_INDEX.md`：模块规范与设计/实施记录。
- `src/`：当前内容页面、编辑状态和桌面壳。
- `src-backend/`：独立内容仓库与 HTTP 服务。
- `src-tauri/`：原生连接与自有进程生命周期。

旧 API 类型和未挂载的旧页面暂留作后续迁移参考，当前执行链路不调用旧站接口。GPL-3.0，见 LICENSE。
