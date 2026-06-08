import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve, extname } from 'path'
import { existsSync, createReadStream, statSync } from 'fs'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
  plugins: [
    vue(),
    // 开发模式下直接从文件系统提供文章图片
    {
      name: 'serve-blog-images',
      configureServer(server) {
        const postsDir = resolve(__dirname, '../source/_posts')

        const contentTypes: Record<string, string> = {
          '.png': 'image/png',
          '.jpg': 'image/jpeg',
          '.jpeg': 'image/jpeg',
          '.gif': 'image/gif',
          '.svg': 'image/svg+xml',
          '.webp': 'image/webp',
          '.ico': 'image/x-icon',
          '.bmp': 'image/bmp',
        }

        server.middlewares.use((req, res, next) => {
          if (!req.url?.startsWith('/source/_posts/')) return next()

          // URL 中的中文会被编码（如 %E9%83%A8%E7%BD%B2），需要解码才能匹配文件系统路径
          const relativePath = decodeURIComponent(req.url.replace('/source/_posts/', ''))
          const filePath = resolve(postsDir, relativePath)

          // 安全检查：确保路径在 postsDir 内
          if (!filePath.startsWith(postsDir)) return next()
          if (!existsSync(filePath) || !statSync(filePath).isFile()) return next()

          const ext = extname(filePath).toLowerCase()
          res.setHeader('Content-Type', contentTypes[ext] || 'application/octet-stream')
          res.setHeader('Cache-Control', 'no-cache')
          createReadStream(filePath).pipe(res)
        })
      }
    }
  ],
  base: '/admin/',
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: parseInt(env.VITE_PORT || '14000'),
    proxy: {
      '/api': {
        target: env.VITE_API_BASE_URL || 'http://localhost:15000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: '../source/admin',
    emptyOutDir: true,
    // 压缩配置
    minify: 'esbuild',
    // 分包策略
    rollupOptions: {
      output: {
        manualChunks(id) {
          // naive-ui 单独打包
          if (id.includes('naive-ui')) {
            return 'naive-ui'
          }
          // vue 生态单独打包
          if (id.includes('vue/') || id.includes('vue-router') || id.includes('pinia')) {
            return 'vue-vendor'
          }
          // bytemd 编辑器单独打包
          if (id.includes('bytemd') || id.includes('@bytemd')) {
            return 'editor'
          }
          // highlight.js 单独打包
          if (id.includes('highlight.js')) {
            return 'highlight'
          }
        }
      }
    },
    // 提高 chunk 大小警告阈值
    chunkSizeWarningLimit: 1000
  }
}})