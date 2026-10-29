import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { contentApi } from '@/api/content'

export type ThemeMode = 'light' | 'dark' | 'system'

export interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
}

export const useAppStore = defineStore('app', () => {
  // 主题
  const themeMode = ref<ThemeMode>(
    (localStorage.getItem('theme-mode') as ThemeMode) || 'system'
  )
  const isDark = computed(() => {
    if (themeMode.value === 'dark') return true
    if (themeMode.value === 'light') return false
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  function applyTheme() {
    document.documentElement.dataset.theme = isDark.value ? 'dark' : 'light'
  }

  function setTheme(mode: ThemeMode) {
    themeMode.value = mode
    localStorage.setItem('theme-mode', mode)
    applyTheme()
  }

  // 侧边栏
  const sidebarCollapsed = ref(false)
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  // 后端状态
  const backendReady = ref(false)
  const backendPort = ref<number | null>(null)
  const backendChecking = ref(false)

  async function checkBackendHealth(): Promise<boolean> {
    backendPort.value = 18000
    backendChecking.value = true
    try {
      const health = await contentApi.health()
      backendReady.value = health.service === 'xiaocancoding-content' && health.api_version === 1
      return backendReady.value
    } catch {
      backendReady.value = false
      return false
    } finally {
      backendChecking.value = false
    }
  }

  // Toast 通知
  const toasts = ref<ToastItem[]>([])
  let toastId = 0

  function showToast(message: string, type: ToastItem['type'] = 'info', duration = 3000) {
    const id = ++toastId
    toasts.value.push({ id, message, type })
    setTimeout(() => dismissToast(id), duration)
  }

  function dismissToast(id: number) {
    const index = toasts.value.findIndex((t) => t.id === id)
    if (index > -1) toasts.value.splice(index, 1)
  }

  // 初始化
  function init() {
    applyTheme()
    // 监听系统主题变化
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (themeMode.value === 'system') applyTheme()
    })
  }

  return {
    themeMode,
    isDark,
    setTheme,
    applyTheme,
    sidebarCollapsed,
    toggleSidebar,
    backendReady,
    backendPort,
    backendChecking,
    checkBackendHealth,
    toasts,
    showToast,
    dismissToast,
    init
  }
})
