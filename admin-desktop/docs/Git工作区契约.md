# 桌面 Git 工作区设计与接口契约

桌面端操作当前会话绑定的 Git 根目录，需要 Git 2.31 或更新版本。状态和文件差异只读，保存文章不触发 Git 操作。工作区显示实际分支、上游、基于本地跟踪引用的领先与落后数量，以及文件的暂存和工作区状态。远端操作的预览与确认才访问网络。

## 操作边界

- 提交以逐个选中的文件当前工作区版本为准，删除也是文件变更。已部分暂存的选中文件会提交其完整工作区版本，界面在预览前后提示。保留未选文件的工作区与暂存条目。重命名分别显示为原路径删除和新路径新增。初始提交只纳入所选文件。
- 用独立索引生成所选文件的精确树快照和本次提交差异。预览可能创建未被引用的 Git 对象。确认时持有标准索引锁，重新生成并核对树，准备保留未选条目的新索引，再创建对象并按预期旧提交更新分支。提交遵守 Git 身份和签名设置，此路径不运行 Git 提交钩子。需运行提交钩子的仓库可使用本机命令行提交。
- 更新要求已提交的本地分支、可识别的上游和干净工作区。确认后取回预览的目标，验证快进关系，持有标准索引锁更新当前工作区，再按预期旧提交更新预览中的分支。出现分叉、冲突、脏工作区或目标变化时停止。常规 Git 分支切换会受索引锁保护。
- 推送只发送预览中的提交和单个上游分支。后端固定经 Git 解析的远端地址，独立验证快进关系后使用明确旧提交的 ref lease，远端分支移动时拒绝写入。拒绝多推送目标、镜像、分叉和未绑定上游。推送可能触发远端仓库已配置的自动工作流。
- 远端操作拒绝映射到本地分支的跟踪引用及符号跟踪引用。操作成功后仅在上游配置和跟踪旧提交仍匹配时更新本地跟踪引用；发生外部变化时在结果中提示。远端传输使用已经核对的地址和本机凭据，HTTP 重定向会导致请求失败。
- 发布是独立的 GitHub Pages 工作流派发。后端启动环境显式设置 `LUCHUAN_GITHUB_PAGES_REPO=owner/repo` 和 `LUCHUAN_GITHUB_PAGES_BRANCH=main` 后启用。仅允许 GitHub 上游对应的分支、固定 `deploy.yml` 工作流、干净且与远端一致的 HEAD，使用已登录并具备权限的本机 `gh`。GitHub 按分支派发，分支可能在最后一次校验后被外部更新。成功表示 GitHub 接收派发请求，部署结果以 Actions 为准。
- Git 与 GitHub CLI 均以参数数组运行。路径为当前 Git 状态中的仓库相对文件名，使用字面匹配，拒绝越界、子模块和目录路径。依赖本机 Git 凭据及所选仓库的 Git 配置。后端不收集凭据或返回命令原始错误输出。

## HTTP

沿用桌面会话 Bearer 鉴权和 `{code,message,details?}` 错误结构。路由前缀 `/api/v1/git`。

| 方法和路径 | 输入 | 输出 |
| --- | --- | --- |
| GET `/status` | 无 | `{branch, head, upstream, operation, changes, publish_configured}`。branch 为分支名或 null，head 为完整 OID 或 null，operation 为进行中的 Git 操作或 null。upstream 为 null 或 `{remote, branch, ahead, behind}`，计数未知时为 null。changes 为 `[{path, staged, unstaged, conflicted, selectable}]`，状态字符来自 Git porcelain v2，点表示该侧未变更，问号表示未跟踪。 |
| GET `/diff` | 查询 `path` | `{path, staged, unstaged, truncated}`，两种文本差异分别返回，未跟踪文本使用空文件为基线；二进制差异使用 Git 摘要。 |
| POST `/preview` | `{action, paths?, message?}`，action 为 commit、update、push 或 publish；paths/message 仅提交使用 | `{token, action, branch, head, target, target_commit, paths, message, remote_head, remote_address, patch, truncated}`。target 为操作目的地；target_commit 是更新目标、推送或发布的提交；remote_address 省略 URL 的认证、查询和片段；patch 为所选工作区快照相对 HEAD 的差异。 |
| POST `/execute` | `{token, confirm: true}` | `{action, message, commit}`，commit 为相关完整提交 OID。 |

预览令牌仅当前后端会话可用，五分钟内有效，确认后即失效。未确认、过期、状态变化时拒绝操作。Git 缺失、无可用工作树或命令失败时返回明确错误，内容服务仍能使用。发布超时后先在 GitHub Actions 检查是否接收请求。

## 评审记录

需求覆盖状态、差异、所选提交、快进更新、安全推送和单独派发。方案、契约和架构自检通过，分别使用只读状态、明确作用域和短时确认来避免误操作。桌面 API 复用现有会话请求工具和错误处理，后端仅新增独立路由及 Git 模块。集成和代码评审以临时真实仓库及本地裸远端验证。
