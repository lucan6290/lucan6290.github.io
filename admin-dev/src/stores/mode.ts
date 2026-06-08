/**
 * 模式管理 Store
 * 管理在线/本地模式切换，持久化到 localStorage
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ModeType } from '@/types/api'

const STORAGE_KEY = 'blog-admin-mode'

/**
 * 从 localStorage 加载模式
 */
function loadModeFromStorage(): ModeType {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'online' || stored === 'local') {
      return stored
    }
  } catch (error) {
    console.warn('从 localStorage 加载模式失败:', error)
  }
  // 默认使用在线模式
  return 'online'
}

/**
 * 保存模式到 localStorage
 */
function saveModeToStorage(mode: ModeType): void {
  try {
    localStorage.setItem(STORAGE_KEY, mode)
  } catch (error) {
    console.warn('保存模式到 localStorage 失败:', error)
  }
}

export const useModeStore = defineStore('mode', () => {
  // State
  const mode = ref<ModeType>(loadModeFromStorage())

  // Getters
  const isOnline = computed(() => mode.value === 'online')
  const isLocal = computed(() => mode.value === 'local')

  // Actions

  /**
   * 设置模式
   * @param newMode 新模式
   */
  function setMode(newMode: ModeType): void {
    mode.value = newMode
    saveModeToStorage(newMode)
    console.log(`模式已切换为: ${newMode}`)
  }

  /**
   * 切换在线/本地模式
   */
  function toggleMode(): void {
    const newMode = mode.value === 'online' ? 'local' : 'online'
    setMode(newMode)
  }

  /**
   * 重置为默认模式（在线模式）
   */
  function resetMode(): void {
    setMode('online')
  }

  return {
    // State
    mode,

    // Getters
    isOnline,
    isLocal,

    // Actions
    setMode,
    toggleMode,
    resetMode
  }
})