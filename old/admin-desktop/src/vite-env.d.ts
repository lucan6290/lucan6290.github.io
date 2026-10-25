/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly TAURI_DEBUG?: string
  readonly VITE_ADMIN_USERNAME?: string
  readonly VITE_ADMIN_PASSWORD?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Tauri 注入的全局变量
interface Window {
  __BACKEND_PORT__?: number
  __BACKEND_READY__?: boolean
  __ADMIN_USERNAME__?: string
  __ADMIN_PASSWORD__?: string
}
