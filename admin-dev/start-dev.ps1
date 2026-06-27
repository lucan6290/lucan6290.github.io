$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  throw "未找到后端 Python 虚拟环境：$python"
}

Write-Host "启动管理后台后端：http://localhost:15000" -ForegroundColor Green
$backendProcess = Start-Process `
  -FilePath $python `
  -ArgumentList @("main.py") `
  -WorkingDirectory $backend `
  -PassThru

Write-Host "启动管理后台前端：http://localhost:14000/admin/" -ForegroundColor Green
$frontendProcess = Start-Process `
  -FilePath "npm.cmd" `
  -ArgumentList @("run", "dev") `
  -WorkingDirectory $frontend `
  -PassThru

Write-Host ""
Write-Host "前后端已启动。关闭此窗口不会自动停止服务。" -ForegroundColor Yellow
Write-Host "后端 PID: $($backendProcess.Id)"
Write-Host "前端 PID: $($frontendProcess.Id)"
Write-Host ""
Write-Host "停止命令：" -ForegroundColor Cyan
Write-Host "Stop-Process -Id $($backendProcess.Id),$($frontendProcess.Id) -Force"
