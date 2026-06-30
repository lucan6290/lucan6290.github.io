import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
  plugins: [vue()],
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
        target: env.VITE_API_BASE_URL || 'http://127.0.0.1:18000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    // 压缩配置
    minify: 'esbuild',
    // 分包策略
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalizedId = id.replace(/\\/g, '/')

          // naive-ui 按组件目录拆包，避免整套 UI 库聚合成一个超大 chunk
          const naiveMatch = normalizedId.match(/\/node_modules\/naive-ui\/es\/([^/]+)/)
          if (naiveMatch) {
            const section = naiveMatch[1]
            if (section.startsWith('_') || section === 'styles') {
              return 'naive-ui-core'
            }
            return `naive-ui-${section}`
          }
          if (normalizedId.includes('/node_modules/naive-ui/')) {
            return 'naive-ui-core'
          }
          if (
            normalizedId.includes('/node_modules/vueuc/') ||
            normalizedId.includes('/node_modules/vooks/') ||
            normalizedId.includes('/node_modules/evtd/') ||
            normalizedId.includes('/node_modules/seemly/') ||
            normalizedId.includes('/node_modules/treemate/') ||
            normalizedId.includes('/node_modules/date-fns/')
          ) {
            return 'naive-ui-vendor'
          }
          // vue 生态单独打包
          if (normalizedId.includes('/node_modules/vue/') || normalizedId.includes('vue-router') || normalizedId.includes('pinia')) {
            return 'vue-vendor'
          }
          // bytemd 编辑器单独打包
          if (normalizedId.includes('bytemd') || normalizedId.includes('@bytemd')) {
            return 'editor'
          }
          // highlight.js 单独打包
          if (normalizedId.includes('highlight.js')) {
            return 'highlight'
          }
        }
      }
    },
    // Mermaid 的 ELK 流程图能力会生成一个懒加载 chunk，实际不进入首屏包
    chunkSizeWarningLimit: 1500
  }
}})
