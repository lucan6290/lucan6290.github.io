/**
 * 同时启动前后端开发服务器（Python 后端 + Vite 前端）
 * 用法：npm run dev:all
 */
import { spawn, execSync } from 'child_process'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'
import { existsSync, rmSync, readdirSync } from 'fs'

const __dirname = dirname(fileURLToPath(import.meta.url))

/**
 * 强制终止进程及其所有子进程
 * @param {import('child_process').ChildProcess} child
 */
function killTree(child) {
  if (child.pid) {
    try {
      if (process.platform === 'win32') {
        // Windows: taskkill /T 杀掉整个进程树（包括 shell 子进程）
        execSync(`taskkill /pid ${child.pid} /T /F`, { stdio: 'ignore' })
      } else {
        process.kill(-child.pid, 'SIGKILL')
      }
    } catch {
      // 进程可能已退出，忽略错误
    }
  }
}

/**
 * 递归清除指定目录下所有 __pycache__ 目录
 * @param {string} baseDir
 */
function removePycache(baseDir) {
  try {
    for (const entry of readdirSync(baseDir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue
      const full = resolve(baseDir, entry.name)
      if (entry.name === '__pycache__') {
        rmSync(full, { recursive: true, force: true })
        console.log(`  已清除: ${full}`)
      } else {
        removePycache(full)
      }
    }
  } catch { /* 忽略权限错误 */ }
}

/** 清除运行时产生的缓存 */
function cleanCache() {
  console.log('正在清除运行时缓存...')

  // 清除 Vite 预构建依赖缓存
  const viteCache = resolve(__dirname, 'node_modules', '.vite')
  if (existsSync(viteCache)) {
    rmSync(viteCache, { recursive: true, force: true })
    console.log(`  已清除: ${viteCache}`)
  }

  // 递归清除 Python 字节码缓存
  removePycache(resolve(__dirname, 'server-python'))
}

/** @param {string} cmd @param {string[]} args @param {string} cwd @param {string} label */
function run(cmd, args, cwd, label) {
  const child = spawn(cmd, args, { cwd, shell: true, stdio: 'pipe' })
  const prefix = `[${label}]`

  child.stdout.on('data', (data) => {
    process.stdout.write(`${prefix} ${data}`)
  })
  child.stderr.on('data', (data) => {
    process.stderr.write(`${prefix} ${data}`)
  })

  child.on('close', (code) => {
    console.log(`${prefix} 进程退出，code=${code}`)
  })

  return child
}

console.log('正在启动博客管理后台...\n')

// Python 后端（使用项目内 venv）
const venvPython = resolve(__dirname, 'server-python', '.venv', 'Scripts', 'python.exe')
const server = run(venvPython, ['main.py'], 'server-python', '后端(Python)')
const frontend = run('npx', ['vite'], '.', '前端')

let cleaning = false

/** Ctrl+C / kill 命令触发的完整清理（含缓存清除） */
const cleanup = () => {
  if (cleaning) return
  cleaning = true
  console.log('\n正在停止所有服务...')
  killTree(server)
  killTree(frontend)
  cleanCache()
  console.log('所有服务已停止，缓存已清除。')
  process.exit(0)
}

// 子进程自行退出时的处理（不清理缓存）
server.on('close', () => {
  if (cleaning) return
  console.log('后端已退出，关闭前端...')
  killTree(frontend)
})
frontend.on('close', () => {
  if (cleaning) return
  console.log('前端已退出，关闭后端...')
  killTree(server)
})

process.on('SIGINT', cleanup)
process.on('SIGTERM', cleanup)
