import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

if (process.platform !== 'win32' || process.arch !== 'x64') {
  throw new Error('此安装包需要在 Windows x64 上构建')
}

const desktop = fileURLToPath(new URL('../', import.meta.url))
const venv = fileURLToPath(new URL('../src-backend/.venv/Scripts/python.exe', import.meta.url))
const python = process.env.LUCHUAN_BUILD_PYTHON || (existsSync(venv) ? venv : 'python')
const architecture = spawnSync(python, ['-c', 'import platform, struct; print(platform.machine(), struct.calcsize("P"))'], { cwd: desktop, encoding: 'utf8' })
if (architecture.error) throw architecture.error
if (architecture.status !== 0 || architecture.stdout.trim().toUpperCase() !== 'AMD64 8') {
  throw new Error('构建独立内容服务需要 Windows x64 Python')
}
const output = spawnSync(python, [
  '-m', 'PyInstaller', '--noconfirm', '--onedir', '--name', 'luchuan-content',
  '--distpath', 'src-tauri/.bundle/dist', '--workpath', 'src-tauri/.bundle/work',
  '--specpath', 'src-tauri/.bundle', '--hidden-import', 'uvicorn.loops.asyncio',
  '--hidden-import', 'uvicorn.protocols.http.h11_impl', '--hidden-import', 'uvicorn.lifespan.on',
  'src-backend/main.py',
], { cwd: desktop, stdio: 'inherit' })
if (output.error) throw output.error
process.exitCode = output.status ?? 1
