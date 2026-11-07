# 站点互动与在线写作方案

## 需求与范围

读者可查看每篇文章的累计阅读量和已公开评论，可匿名留言。站长通过网页读取、新建、编辑 Markdown，并审核或撤下评论。正文、导航与搜索仍由静态构建提供，互动服务未配置或故障时可以正常阅读。

## 方案与架构

- 静态站按需调用可独立部署的 FastAPI 服务。浏览器只有服务地址 `VITE_PUBLIC_SERVICE_URL`，生产使用 HTTPS。服务只允许配置的站点源发起跨源请求；无浏览器 Origin 的命令行请求仍适用对应接口的鉴权规则。
- 服务启动时从该版静态构建生成的内容清单读取栏目文章的 `relativePath` 集合。匹配大小写和文件扩展名的原始值，根级 Markdown、目录 README、资源文件、未知或未发布文档不接受互动。重命名后的路径拥有独立记录。在线新建必须使用已有栏目目录，已有根级 Markdown 仍可打开和保存。
- 阅读量、去重记录、评论由 SQLite 持久化。浏览器用 `sessionStorage` 保存随机 UUID；服务按文章和会话标识的哈希去重，并在同一事务中写入去重记录与增加阅读量。会话不可用时仅查询。该数字表示本站记录的阅读会话次数。
- 匿名评论只收纯文本，提交后待审。通过后公开，撤下后不可见；浏览器按普通文本插值展示。限制请求体、评论长度与提交频次，避免在响应或日志输出凭据和原始请求内容。
- 在线作者使用服务端配置的高熵 Bearer token，网页只在页面组件内存保存，离开、刷新或退出时清除。复用桌面端 `ContentStore` 的六字段校验、更新时间维护、文件版本与原子保存。同一作者目录的服务进程共享 SQLite 文件锁，覆盖版本比较到写入的全过程。桌面后台和其他外部写入者使用独立目录，或与在线写作错开。发布从作者检出目录按现有流程完成，保存不触发 Git 命令。
- 后端与静态构建分离部署，SQLite 存放在持久卷，作者检出目录使用最小可写权限。在线写作可以单独关闭，已发表互动数据可继续读写。

## 契约

所有路由以 `/api/v1` 开头，成功响应为 JSON，错误为 `{code, message}`，响应禁止缓存。路径字段为未编码的 `frontend/content` 相对路径，查询参数由 HTTP 客户端编码。

| 方法与路由 | 请求 | 成功响应 |
| --- | --- | --- |
| GET `/article` | `article_path`，可选 `before` | `{views, comments, next_before}`，已公开评论按 ID 从新到旧分页 |
| POST `/views` | `{article_path, session_id}` | `{views}` |
| POST `/comments` | `{article_path, body, submission_id}` | 201，`{status: "accepted"}`；相同 UUID 与正文重试只接收一条 |
| GET `/admin/session` | Bearer | `{writing_enabled}` |
| GET `/admin/comments` | Bearer，`status` 和可选 `before` | `{comments, next_before}` |
| PATCH `/admin/comments/{id}` | Bearer，`{status: "published" \| "rejected"}` | 更新后的评论 |
| GET `/admin/documents` | Bearer | `{documents, directories}` |
| GET `/admin/document` | Bearer，`relative_path` | Markdown 详情 |
| POST `/admin/documents` | Bearer，`{relative_path, raw_content}` | 201，Markdown 详情 |
| PUT `/admin/document` | Bearer，`{relative_path, raw_content, expected_version}` | 保存后的 Markdown 详情 |

公开评论包含 `id`、`body` 和 `created_at`，管理端额外包含 `article_path` 和 `status`。文档列表包含 `relative_path` 和 `title`，详情再返回 `raw_content` 和 `version`。目录列表包含 `relative_path` 和 `label`。无效凭据返回 401，未启用在线写作或管理密钥返回 503，未知文章或文件返回 404，非法输入返回 400 或 422，过大请求返回 413，超限返回 429，内容版本冲突返回 409。

## 评审检查

需求覆盖匿名留言、按文章统计、站长写作。前后端统一相对路径、审核状态与鉴权边界。SQLite 唯一键与事务保护并发重复访问；只有发布清单中的文档可产生公开互动。写入复用既有内容校验，作者刷新可恢复最新文件，冲突时保留网页草稿并提示。验证使用临时数据库、临时作者目录和实际本地 HTTP，不访问真实线上部署或凭据。
