# 箓川码笺

箓川码笺（xiaocancoding）是一个个人技术站和知识库。读者通过 Vue 静态站点浏览文章，作者通过 Tauri 桌面 App 管理同一份 Markdown 内容。

[访问站点](https://lucan6290.github.io)

## 目录

| 目录 | 职责 |
| --- | --- |
| [frontend/](frontend/README.md) | 读者站点、内容生成、搜索与静态构建 |
| [frontend/content/](frontend/content/) | Markdown 与配图，站点和桌面 App 共用的内容事实源 |
| [admin-desktop/](admin-desktop/README.md) | 桌面管理 App，包含 Vue 界面、Tauri 原生层与本地 Python 内容服务 |
| [frontend/service/](frontend/service/README.md) | 可选的公开互动、评论审核和在线写作服务 |
| [docs/](docs/DOCUMENTATION_INDEX.md) | 开发规范、内容指南与工程文档 |

## 本地开发

在仓库根目录执行以下命令启动读者站点。

```powershell
cd frontend
pnpm install
pnpm dev
```

站点使用 `http://127.0.0.1:3400/`，`pnpm build` 输出到 `frontend/dist/`。构建和发布配置见 [站点开发说明](frontend/README.md#构建)。

桌面 App 的开发启动、浏览器调试和 Windows 安装包见 [桌面端说明](admin-desktop/README.md)。原生应用自动管理本地内容服务。开发端口、接口和构建说明集中在 [桌面端文档索引](admin-desktop/docs/DOCUMENTATION_INDEX.md)。

## 内容规则

在 `frontend/content/` 中新增目录和 Markdown 即可生成分类和文章。六字段 Front Matter、时间语义及配图规则见 [内容写作指南](docs/SITE_CONTENT_GUIDE.md)。

## 许可

仓库源代码采用 [MIT 许可](LICENSE)。原创文章、笔记和图片等非代码内容不在该许可范围内。转载本站原创文章时请注明“箓川码笺”及原文链接。
