/**
 * 一键启动博客全部开发服务
 * 用法：npm run dev
 *
 * 启动三个服务：
 *   1. 博客预览（Hexo）      → http://localhost:4000
 *   2. 管理后台前端（Vite）   → http://localhost:14000
 *   3. 管理后台后端（FastAPI） → http://localhost:15000
 */
import { spawn, execSync } from 'child_process'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ADMIN_DIR = resolve(__dirname, 'admin-dev')

/** @type {import('child_process').ChildProcess[]} */
const children = []

/**
 * 强制终止进程及其所有子进程
 * @param {import('child_process').ChildProcess} child
 */
function killTree(child) {
  if (child.pid) {
    try {
      if (process.platform === 'win32') {
        execSync(`taskkill /pid ${child.pid} /T /F`, { stdio: 'ignore' })
      } else {
        process.kill(-child.pid, 'SIGKILL')
      }
    } catch {
      // 进程可能已退出，忽略错误
    }
  }
}

/** 终止所有子进程 */
function killAll() {
  for (const child of children) {
    killTree(child)
  }
}

/**
 * 启动一个子进程
 * @param {string} cmd
 * @param {string[]} args
 * @param {string} cwd
 * @param {string} label
 * @param {string} color
 */
function run(cmd, args, cwd, label, color) {
  const child = spawn(cmd, args, { cwd, shell: true, stdio: 'pipe' })

  const reset = '\x1b[0m'
  const prefix = `${color}[${label}]${reset}`

  child.stdout.on('data', (data) => {
    process.stdout.write(`${prefix} ${data}`)
  })
  child.stderr.on('data', (data) => {
    process.stderr.write(`${prefix} ${data}`)
  })

  child.on('close', (code) => {
    console.log(`${prefix} 进程退出，code=${code}`)
  })

  children.push(child)
  return child
}

// ANSI 颜色
const cyan = '\x1b[36m'
const green = '\x1b[32m'
const yellow = '\x1b[33m'

console.log('')
console.log('  清理 Hexo 缓存...')

// 先清理缓存，确保配置变更生效
try {
  execSync('npx hexo clean', { cwd: __dirname, shell: true, stdio: 'pipe' })
  console.log('  缓存已清理')
} catch {
  console.log('  缓存清理失败（可忽略）')
}

console.log('')
console.log('  启动博客开发环境...')
console.log('  博客预览:     http://localhost:4000')
console.log('  管理后台前端:  http://localhost:14000')
console.log('  管理后台后端:  http://localhost:15000')
console.log('  按 Ctrl+C 停止所有服务')
console.log('')

// 1. 博客预览（Hexo）
run('npx', ['hexo', 'server'], __dirname, '博客预览', cyan)

// 2. 管理后台后端（Python FastAPI）
const venvPython = resolve(ADMIN_DIR, 'server-python', '.venv', 'Scripts', 'python.exe')
run(venvPython, ['main.py'], resolve(ADMIN_DIR, 'server-python'), '管理后端', green)

// 3. 管理后台前端（Vite）
run('npx', ['vite'], ADMIN_DIR, '管理前端', yellow)

// Ctrl+C 优雅退出
let cleaning = false
const cleanup = () => {
  if (cleaning) return
  cleaning = true
  console.log('\n正在停止所有服务...')
  killAll()
  console.log('所有服务已停止。')
  process.exit(0)
}

process.on('SIGINT', cleanup)
process.on('SIGTERM', cleanup)
