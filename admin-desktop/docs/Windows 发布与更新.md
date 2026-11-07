# Windows 桌面发布与更新

## 设计与契约

Windows x64 采用 NSIS 安装包。继续使用 PyInstaller 的独立目录打包方式和 `content-backend/` 资源路径，连同 Python 运行时及库安装。普通 CI 只读，独立于站点部署，生成可复现的未签名构建。发布构建采用单独的手动工作流，先核对桌面标签、源代码与版本，再进入受保护的签名环境。

签名环境负责提供经过授权的 Windows 代码签名证书、RFC 3161 时间戳服务、Tauri 更新密钥与固定 HTTPS 频道地址。构建用证书签名后端程序及 Tauri 安装程序，校验签名和时间戳后，再提交安装包、Tauri 签名、SHA-256 及更新清单到发布草稿。更新配置编入正式安装包，用户设置和工作区不能改写。普通开发版、浏览器版和本地未签名包显示更新不可用。

设置页只在用户点击时检查更新。先下载并验证版本签名，最后单独确认安装，避免离开设置页后自动退出。安装程序启动失败时保留桌面窗口并显示错误，可重新检查。安装程序启动成功后，系统关闭应用持有的 Windows Job 句柄并清理自有后台进程。后端会话、仓库配置和文章目录使用原有存放路径，安装包不写入内容仓库。

## 实施检查

1. 为签名配置、桌面标签和更新清单写回归测试，先验证失败，再实现发布工具。
2. 在现有 Rust/Tauri 边界接入受配置保护的更新命令，在设置页挂载独立卡片。验证禁用、网络或签名失败、重新检查、下载完成后单独确认安装。
3. 运行前后端回归、锁定依赖的原生构建和 Windows x64 NSIS 打包。单独记录真实证书签名、干净机安装与升级验收。

需求、前后端方案、契约及架构自查通过。更新使用 Tauri 自带签名校验，不增加内容 HTTP 接口。更新授权使用发布配置，不复用内容令牌。跨层集成和代码评审以实际构建及回归记录为准。

## 本地构建

在 Windows x64 使用 PowerShell 7，安装 Node.js 24.11.1、Rust 1.98.0（`x86_64-pc-windows-msvc`）、MSVC、Windows SDK 和 uv 0.13.7。构建安装包时，Tauri 会下载并校验锁定版本的 NSIS 工具。

```powershell
cd admin-desktop
npm ci
uv venv --managed-python --python 3.12.15 src-backend/.venv
uv pip sync --python src-backend/.venv/Scripts/python.exe src-backend/requirements-windows-build.txt
npm run tauri:build
Get-FileHash src-tauri/target/x86_64-pc-windows-msvc/release/bundle/nsis/*-setup.exe -Algorithm SHA256
```

需要使用现有的 Windows x64 Python 环境时，将 `LUCHUAN_BUILD_PYTHON` 指向已安装构建锁定依赖的解释器。安装包内含 Python 运行时、内容服务和依赖，目标机无需安装 Python。目标机仍需要 WebView2，缺失时由 NSIS 引导安装。普通 CI 也会上传未签名包供验证。

## 正式发布配置

由仓库管理员配置 `desktop-windows-release` GitHub Environment，限制 `main` 并要求发布审批。签名任务使用专用 Windows x64 runner，标签为 `admin-desktop-signing`。签名 runner 应在审批后以隔离的临时实例加入，仅供可信发布任务，完成后销毁。签名证书由授权的密钥设备或证书提供者挂载到 runner 用户的 `CurrentUser\My`，私钥需能由 SignTool 非交互使用。runner 同时需有 Windows SDK 和支持 NSIS 的 7-Zip，可通过 `TAURI_WINDOWS_SIGNTOOL_PATH` 和 `LUCHUAN_7ZIP_PATH` 指定工具路径。

| 环境项 | 类型 | 用途 |
| --- | --- | --- |
| `LUCHUAN_CODESIGN_THUMBPRINT` | 变量 | 已授权代码签名证书的 40 位指纹 |
| `LUCHUAN_CODESIGN_TIMESTAMP_URL` | 变量 | 证书提供者认可的 HTTPS RFC 3161 时间戳服务 |
| `LUCHUAN_UPDATER_ENDPOINT` | 变量 | 由发布者控制的固定桌面更新 HTTPS 地址 |
| `LUCHUAN_UPDATER_PUBLIC_KEY` | 变量 | 由 `tauri signer generate` 生成的 `.pub` 文件内容 |
| `TAURI_SIGNING_PRIVATE_KEY` | Secret | 与以上公钥配对的 Tauri 更新私钥内容 |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Secret | Tauri 更新私钥口令 |

更新公钥和频道在构建时编入应用。私钥与 Authenticode 证书分开保管，发布工具检查两类签名。签名检查验证最终安装包以及从该安装包解出的桌面和内容服务可执行文件。Tauri 更新签名另行覆盖最终 NSIS 字节和版本号。更换更新密钥需先安排已安装客户端的信任迁移。

1. 核对 `package.json`、`package-lock.json`、`src-tauri/Cargo.toml`、`src-tauri/Cargo.lock` 和 `src-tauri/tauri.conf.json` 的版本及 `CHANGELOG.md`，把 `desktop-vX.Y.Z` 标签指向已审核的 `main` 提交。用 GitHub 规则保护 `desktop-v*` 标签。
2. 在 `main` 手动运行 `Release - admin-desktop Windows`，输入该标签。源检查及环境审批完成后，工作流核验并产出 Windows x64 安装包、`.sig`、`SHA256SUMS.txt` 与 `latest.json`，创建 GitHub 发布草稿。
3. 在干净 Windows x64 环境验证安装、首次选择内容库、重开恢复、退出后进程清理和旧版升级。确认草稿资产后，由发布者手动公开草稿，并把其中的 `latest.json` 原样发布到固定桌面更新地址。该地址可由独立的桌面发布渠道托管，避免受仓库其他用途的最新发布影响。

正式签名参考 [Tauri Windows Code Signing](https://v2.tauri.app/distribute/sign/windows/) 与 [Microsoft SignTool](https://learn.microsoft.com/windows/win32/seccrypto/signtool)。更新清单和运行时校验参考 [Tauri Updater](https://v2.tauri.app/plugin/updater/)。

## 本地验收记录

- Windows x64 已生成 0.1.0 未签名 NSIS 安装包，大小 19,306,967 字节，SHA-256 为 `5c1a61d2aa5c08d7e993ab527fc4351666edce82ca0f33bc29fd508fb0d86777`。已从 NSIS 解出后端和运行时，运行其中的 `luchuan-content.exe --help` 成功。该哈希对应独立发布链路工作树中的构建，后续合并构建有自己的哈希。
- 用临时 Tauri 密钥签名该包的副本，验证安装包字节、公钥、签名版本及清单生成。测试密钥已删除。篡改包、错误公钥和版本不一致均有回归用例。
- 正式 Authenticode 证书及更新渠道需要发布者提供。干净 Windows 的安装、卸载与实际升级仍需单独验收。
