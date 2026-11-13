# 箓川码笺桌面管理端

基于 Tauri 2 + Vue 3，通过 `src-backend/` 中的本地 Python 内容服务管理工作区的 `frontend/content/`。

## 当前能力

- 按实际目录和动态栏目管理 Markdown，区分普通文章与 README 目录介绍。
- 文档管理提供可展开的目录树，支持按标题、正文、摘要、标签或路径搜索。编辑页提供源码与实时预览、可点击的大纲及内容库内的相对图片。
- 显式新建目录，按实际文件名新建文档，编辑完整 Markdown。普通文章自动生成六字段头部，填写标题、摘要后保存；工程说明、设计文档可选择说明用途，README/AGENTS 自动豁免。
- 原文保存保留 YAML 注释、数组、嵌套/未知字段与既有 BOM、换行；没有变化不写盘。具备六字段的普通文章真实修改时维护 updated，保留 date；不猜补历史日期。
- 恢复焦点或每 2 秒检查当前文档的外部变化：未修改时刷新，有本地修改时保留缓冲与原版本。
- 保存/删除携带文件内容版本；冲突拒绝覆盖，提供本地与磁盘对照、复制、明确重载、排他另存。
- 离开编辑器或关闭窗口时可保存、放弃或取消，保存失败不能视为保存成功。

外部编辑器和 AI 可直接修改 Markdown，桌面端会检测变化。

新建普通文章时在源码里填写 title 和 description，正文一级标题与 title 保持一致；未填摘要会拒绝保存。已有文档可选择“本次编辑用途”，说明文档按原文保存；重新打开恢复自动识别，必要时可再次明确用途。完整规则见 `docs/内容接口契约.md`，验证证据见 `docs/六字段文章模板验证记录.md`。

这是同机交替编辑保护。外部工具不参与同一写入协议时，不保证严格同时写入的互斥；不要将它当作多人实时编辑系统。


## 图片库

- 文章保存后可在编辑器选择图片、粘贴截图或把文件拖入源码区。配图保存到文章同级的完整文件名加 -images 目录。导入成功后在源码缓冲插入引用，文档仍需显式保存。多张导入时分别显示失败，已成功的图片仍可在媒体库浏览。
- 单张图片上限 12 MiB，支持 PNG、JPEG、GIF、WebP、AVIF、BMP、ICO 与不含脚本、外链和样式的 SVG。文件名保留中文和空格，链接中的 Markdown 分隔字符经过转义。同名文件追加 -2、-3，避免覆盖。
- 在媒体库按文档查看、预览和复制 Markdown 引用。删除前会列出引用和出现次数，并重新检查图片与引用的版本。确认删除后保留原文中的引用，可能需要手动修复。

## 移动、回链和图谱

在「文档管理」点击文档的「移动」，或选择目录后点击「移动当前目录」。填写新相对路径，先查看配图、受影响文档和博客 URL，再确认执行。移动目标的父目录需要已创建。链接修复使用当前库中的 Markdown，包含引用式链接，保留原文件头部、链接标题及锚点。计划失效时需重新查看影响。

编辑器可展开「反向链接」。在「知识图谱」选择中心文档，查看其他文档和中心之间的直接引用及方向。

## 写作与切换

编辑器使用标签页保留各自的磁盘版本和未保存源码。离开编辑器或关闭窗口时可保存、放弃或取消，需处理全部脏标签。关闭单个标签只处理该标签。收藏按博客内容根隔离，快速切换可按正文、标题或路径搜索。使用 Ctrl+P 打开快速切换，Ctrl+S 保存，Ctrl+B、Ctrl+I、Ctrl+K 编辑格式，Alt+R 切换阅读模式。

文章信息表单可调整标题、摘要、标签和置顶。应用到源码后仍须显式保存。标题和正文首个一级标题一同调整，日期仍按六字段规则维护。Markdown 工具栏直接编辑源码，阅读模式保留大纲和图片预览。

## 站点预览与构建

编辑器可在浏览器中打开当前已保存文章，设置页可打开站点首页。站点使用当前工作区的 `frontend/`，首次使用先在该目录运行 `pnpm install`，并确保桌面应用能从 PATH 找到 Node.js。预览固定使用 `127.0.0.1:3400`，可复用能确认属于当前工作区的 Vite 服务。生产构建生成 `frontend/dist/`，界面显示退出结果、产物位置和构建日志。

## 开发启动

桌面开发界面固定使用 `14200`。Windows 下 `npm run tauri:dev` 会先检查该端口：仅自动停止能确认属于本项目且父进程已退出的 Vite，否则提示占用进程及 PID。新站 `3400` 可独立运行。

依赖：Node.js 22+、Python 3.10+、Rust stable、Windows WebView2/MSVC。推荐将后端环境放在 `src-backend/.venv`，原生启动器优先使用该环境，否则使用 PATH 中的 python。

```powershell
cd admin-desktop
npm install
python -m venv src-backend/.venv
src-backend/.venv/Scripts/python.exe -m pip install -r src-backend/requirements.txt
npm run tauri:dev
```

开发模式自动启动独立后端并保留 `--reload`。后端优先使用 `18000`，遇到占用或 Windows 预留时改用系统分配的本机端口。启动器校验服务身份、项目根、内容根和会话；可以复用匹配的独立联调后端。仅管理自己启动的进程树。运行中断线时会尝试恢复连接，编辑器保留未保存内容。

仪表盘、文档列表和搜索共用按工作区隔离的 SQLite 内容索引。首次读取时建库，后续刷新校验 Markdown 的内容哈希，复用未变文件的摘要和搜索文本。外部增删、重命名和内容变更在刷新时同步，即使改写后保留了文件大小和修改时间。开发版的索引放在 `.codex-tmp/admin-desktop/`，安装版放在应用的本地数据目录。文章保存继续写入原 Markdown。索引不可用时，内容服务直接扫描 Markdown。

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

## Windows 安装包

在 Windows x64 构建机上，从 `admin-desktop` 安装锁定依赖并生成未签名 NSIS 安装包：

```powershell
npm ci
uv venv --managed-python --python 3.12.15 src-backend/.venv
uv pip sync --python src-backend/.venv/Scripts/python.exe src-backend/requirements-windows-build.txt
npm run tauri:build
```

安装包位于 `src-tauri/target/x86_64-pc-windows-msvc/release/bundle/nsis/`，包含独立内容后端及 Python 运行时。工具版本、正式签名、更新渠道与验收流程见 [Windows 发布与更新](docs/Windows%20发布与更新.md)。

首次启动选择博客仓库根目录或其中的 `frontend/content/`。连接成功后记住该位置，后续打开会自动启动并连接本机后端。选择的仓库仅需包含内容目录，桌面端源码可以不在其中。 可以在设置中切换工作区。选择新目录后，应用先检查内容服务，再切换页面与下次启动位置。会话、日志及上次选择的位置存放在当前用户的本地应用数据目录 `cn.xiaocancoding.admin` 下。

安装版采用相同的本机端口回退策略，关闭时停止本次应用启动的后端。保存直接写入博客内容目录，博客开发服务运行时会重新生成内容；线上发布仍走博客自己的构建与部署流程。

## 文档与源码

- `docs/内容接口契约.md`：当前内容 API 主契约。
- `docs/DOCUMENTATION_INDEX.md`：模块规范与设计/实施记录。
- `src/`：当前内容页面、编辑状态和桌面壳。
- `src-backend/`：独立内容仓库与 HTTP 服务。
- `src-tauri/`：原生连接与自有进程生命周期。

旧 API 类型和未挂载的旧页面暂留作后续迁移参考，当前执行链路不调用旧站接口。GPL-3.0，见 LICENSE。
