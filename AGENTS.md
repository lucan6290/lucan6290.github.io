# Codex 本地开发规范

## 运行端口

- 博客前端必须运行在 `http://127.0.0.1:3400/`。
- 管理前端必须运行在 `http://127.0.0.1:14000/admin/`，端口固定使用 `14000`。
- 管理后端必须运行在 `http://127.0.0.1:18000/`，端口固定使用 `18000`。
- 当前环境为本地开发，不要为了规避端口占用改用其他端口。

## 博客前端

- 工作目录：`site`
- 启动命令：`npm run dev`
- 访问地址：`http://127.0.0.1:3400/`
- 博客前端本地开发必须使用热更新启动，即使用 `npm run dev`。
- 如果 `3400` 端口被占用，必须先清理占用进程，再启动博客前端。
- 不允许临时改成 `3401`、`5173` 或其他端口运行博客前端。

PowerShell 检查与清理示例：

```powershell
netstat -ano | Select-String ':3400'
Stop-Process -Id <PID> -Force
```

## 管理前端

- 工作目录：`admin/frontend`
- 启动命令：`npm run dev`
- 访问地址：`http://127.0.0.1:14000/admin/`
- 管理前端本地开发必须使用热更新启动，即使用 `npm run dev`。
- 管理前端端口必须固定为 `14000`。
- 不允许临时改成其他端口运行管理前端。

PowerShell 检查与清理示例：

```powershell
netstat -ano | Select-String ':14000'
Stop-Process -Id <PID> -Force
```

## 管理后端

- 工作目录：`admin/backend`
- Python 环境：`python310`
- 启动命令：`python -m uvicorn scr.main:app --reload --port 18000`
- 访问地址：`http://127.0.0.1:18000/`
- 后端本地开发必须使用热更新启动，即必须保留 `--reload`。
- 管理后端端口必须固定为 `18000`。
- 不允许临时改成其他端口运行管理后端。

PowerShell 检查与清理示例：

```powershell
netstat -ano | Select-String ':18000'
Stop-Process -Id <PID> -Force
```

## 执行要求

- 启动前先确认目标端口是否被占用。
- 若端口被旧的本项目开发服务占用，先停止旧进程，再按固定端口启动。
- 不修改 `site/build`、`site/.docusaurus` 等构建产物来解决端口问题。
