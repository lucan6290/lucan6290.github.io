# 站点互动服务

独立 FastAPI 服务为静态站提供累计阅读量和匿名评论。没有配置服务时，文章、搜索、导航和构建仍可用。

## 运行

在仓库根目录使用 Python 3.11+ 和独立虚拟环境。

```powershell
python -m pip install -r frontend/service/requirements.txt
$env:PUBLIC_SITE_ORIGIN = 'http://127.0.0.1:3400'
$env:PUBLIC_CONTENT_MANIFEST = (Resolve-Path frontend/src/generated/content-manifest.json).Path
$env:PUBLIC_INTERACTION_DB = Join-Path $env:TEMP 'xiaocancoding-interactions.sqlite3'
python -m uvicorn public_api:create_app --factory --app-dir frontend/service --host 127.0.0.1 --port 18400 --workers 1
```

先执行 `pnpm -C frontend build:content` 生成清单，并核对 18400 未被占用。该端口属于独立互动服务。另一个终端设置 `VITE_PUBLIC_SERVICE_URL=http://127.0.0.1:18400` 后启动 3400 的新前端。清单中只有正式文章，目录介绍、草稿和未知路径不接受评论和计数。

`PUBLIC_ADMIN_TOKEN` 留空时，匿名提交仍可用，管理员功能关闭，留言保留在待审队列。启用时由密码管理器或服务端密钥管理器生成并注入至少 32 字符的高熵随机令牌。通过管理员接口访问审核队列。浏览器只需服务地址，令牌通过 HTTPS Authorization 请求头发送，并仅保留在当前页面内存。

## 部署边界

静态站构建时设置 `VITE_PUBLIC_SERVICE_URL` 为 HTTPS 服务地址。把同一构建的 `frontend/src/generated/content-manifest.json` 提供给互动服务进程并重启以刷新文章白名单。配置 `PUBLIC_SITE_ORIGIN` 为协议、域名与可选端口组成的完整站点源，末尾不加路径或斜杠。部署在 TLS 反向代理后，服务只监听私有网络。代理应覆盖转发头，Uvicorn 只信任明确列出的代理 IP。也应在代理设置请求大小、并发和时间限制，避免记录 Authorization 或请求体。参见 [FastAPI 的 HTTPS 部署说明](https://fastapi.tiangolo.com/deployment/https/) 和 [可信代理说明](https://fastapi.tiangolo.com/advanced/behind-a-proxy/)。

SQLite 应位于本地持久卷并使用 SQLite 在线备份接口或停机一致性备份。阅读量按每篇文章的随机会话累计，同一会话重复打开、刷新和重试只计一次。会话 ID 由浏览器在会话存储生成，SQLite 保存哈希。更换文件路径会开启独立计数。匿名评论经管理员审核后显示，评论记录正文、关联文章、时间、状态及用于防重复提交的随机标识。评论每 10 分钟最多提交 5 次，阅读登记每分钟最多 120 次，失败认证每分钟最多 10 次，均按可信客户端地址计算固定窗口。限流只保存短期带密钥散列，窗口过期后在下一次受限请求时清理。

HTTP 详见 [方案与契约](../../docs/superpowers/specs/2026-11-07-public-site-service-design.md)。本地验证从根目录执行：

```powershell
python -m pip install -r frontend/service/requirements-test.txt
python -m unittest discover -s frontend/service/tests -v
```
