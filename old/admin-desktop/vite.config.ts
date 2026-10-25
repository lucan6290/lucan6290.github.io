import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { readFileSync } from 'fs'

/** 读取 admin/backend/.env 中的管理员凭据（开发模式自动登录用） */
function readBackendAdminCredentials(): { username: string; password: string } {
  const envPath = resolve(import.meta.dirname, '..', 'admin', 'backend', '.env')
  let username = 'admin'
  let password = 'admin123'
  try {
    const content = readFileSync(envPath, 'utf-8')
    for (const line of content.split('\n')) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#')) continue
      const eqIdx = trimmed.indexOf('=')
      if (eqIdx === -1) continue
      const key = trimmed.slice(0, eqIdx).trim()
      const value = trimmed.slice(eqIdx + 1).trim()
      if (key === 'LUCHUAN_ADMIN_USERNAME') username = value
      if (key === 'LUCHUAN_ADMIN_PASSWORD') password = value
    }
  } catch {
    // .env 不存在时使用默认值
  }
  return { username, password }
}

// Tauri 前端构建配置
// 开发模式：Vite dev server (HMR)，Tauri 自动代理
// 生产构建：输出相对路径 dist，供 Tauri loadFile 加载
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const creds = readBackendAdminCredentials()

  return {
    plugins: [vue()],
    // 桌面端使用相对路径，适配 Tauri 的 file:// 或自定义协议加载
    base: './',
    resolve: {
      alias: {
        '@': resolve(import.meta.dirname, 'src')
      }
    },
    // Tauri dev 时使用固定端口，生产构建不需要 server
    server: {
      host: '127.0.0.1',
      port: 14200,
      strictPort: true
    },
    build: {
      outDir: 'dist',
      emptyOutDir: true,
      minify: 'esbuild',
      rollupOptions: {
        output: {
          manualChunks(id) {
            const normalizedId = id.replace(/\\/g, '/')

            // ByteMD 编辑器单独打包
            if (normalizedId.includes('bytemd') || normalizedId.includes('@bytemd')) {
              return 'editor'
            }
            // highlight.js 单独打包
            if (normalizedId.includes('highlight.js')) {
              return 'highlight'
            }
            // Vue 生态打包
            if (normalizedId.includes('/node_modules/vue/') || normalizedId.includes('vue-router') || normalizedId.includes('pinia')) {
              return 'vue-vendor'
            }
          }
        }
      },
      chunkSizeWarningLimit: 1500
    },
    // Tauri 需要的环境变量
    envPrefix: ['VITE_', 'TAURI_'],
    define: {
      'import.meta.env.VITE_ADMIN_USERNAME': JSON.stringify(creds.username),
      'import.meta.env.VITE_ADMIN_PASSWORD': JSON.stringify(creds.password),
    }
  }
})
