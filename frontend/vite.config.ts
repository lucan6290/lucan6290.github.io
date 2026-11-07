import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';
import { contentManifestPlugin } from './src/vite/contentManifestPlugin';
import { desktopSitePlugin } from './src/vite/desktopSitePlugin';

export default defineConfig({
  plugins: [vue(), contentManifestPlugin(), desktopSitePlugin()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '127.0.0.1',
    port: 3400,
    strictPort: true,
  },
  preview: {
    host: '127.0.0.1',
    port: 3400,
    strictPort: true,
  },
});
