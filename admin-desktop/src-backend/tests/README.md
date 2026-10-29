# 内容后端回归记录

执行：项目根 `python -m unittest discover -s admin-desktop/src-backend/tests -v`。

2026-10-29：27 项通过，写入全部使用 `TemporaryDirectory`，未操作真实笔记；另执行 `python -m compileall -q admin-desktop/src-backend` 通过。最终使用项目隔离环境 `.codex-tmp/admin-desktop-python/Scripts/python.exe` 验证固定依赖版本。

红绿证据：最初缺少 `app` 模块导致测试失败；实现后 15 项通过。补充用例发现 Windows 目录读取误报 500、无效 YAML/UTF-8 阻断列表、读取与 stat 间外部写入导致快照不一致三项失败；修正后 24 项通过。

审阅补充三项回归均先失败再修复：

- 第二次 CLI 启动端口失败会改写原服务会话。现在先持有监听 socket 再发布会话，Windows 使用 `SO_EXCLUSIVEADDRUSE`，socket 一直传入 `Server.run` 或 `ChangeReload`，退出后才释放。测试用临时监听 socket 验证竞争端口绑定失败、reload 工厂重建认证稳定与退出关闭，不占用 18000。启动方式依据 [Uvicorn 0.30.6 官方启动实现](https://github.com/encode/uvicorn/blob/0.30.6/uvicorn/main.py) 及其 Windows socket 共享流程。
- PyYAML 构造无效日期抛 `ValueError`。现在按 YAML 错误返回 400，外部含此错误的文档仍可在列表看到。
- Windows junction 不被 `is_symlink` 识别。扫描先校验解析路径边界，并跳过别名及已访问目录。实际创建越界、祖先回环与内部别名三类 junction 验证，清理仅使用 `os.rmdir` 删除 junction 本身，目标文档不受影响。

覆盖：原始 CRLF/BOM、未知及嵌套 YAML、注释保留、无头部、无变化不写盘、排他创建、并发保存、失败清理、原子替换失败保留原文、版本冲突、删除确认与资源保留、安全路径和越界链接、读取期间外部写入、CORS、会话随机 token、固定端口及 reload token 稳定。

跨语言用例直接调用 `frontend/scripts/lib/buildContent.mjs`，在同一临时内容样例上核对目录、README、隐藏路径、资源目录中的 Markdown、数字排序和展示标题。此调用只向临时 `generated` 目录写入。

与前台当前规则相关的边界：

- 一级空目录均保留；嵌套纯空目录仅在 `knowledge/blog/projects` 内保留。动态栏目内无文章/README 的空子目录不会进入常规列表。
- 资源名正则是 `images`、`assets` 和 `*-imgs`；`*-images` 仅在其内容都是资源时被排除。这是前台现有行为，后端未自行修改规则。
- Python 用数字前缀和稳定字符顺序返回列表；中文本地化展示排序由 Vue 的 `localeCompare` 完成，与前台浏览器排序保持一致。
- 前台缺失日期时使用文件时间；接口 `date/updated` 缺失时按契约返回 null，`modified_at` 独立返回文件修改时间。
- 列表遇无效 YAML/UTF-8 使用回退摘要继续展示；详情保持 400 并指出解析/编码错误。版本始终基于磁盘原始字节。

最终完整测试使用固定的 FastAPI 0.115.0、Uvicorn 0.30.6 及其余 `requirements.txt` 依赖。整体桌面集成由主执行者验证。外部进程不共享写锁时，摘要检查与替换之间仍存在设计已说明的竞争窗口，本模块不宣称严格并发写入保证。
