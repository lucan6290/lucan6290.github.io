import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
// Tauri 前端构建配置
// 开发模式：Vite dev server (HMR)，Tauri 自动代理
// 生产构建：输出相对路径 dist，供 Tauri loadFile 加载
export default defineConfig(() => {
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
    envPrefix: ['VITE_', 'TAURI_']
  }
})
