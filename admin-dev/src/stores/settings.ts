/**
 * 设置管理 Store
 * 管理 AI 模型配置等设置项，持久化到 localStorage
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'blog-admin-settings'

/**
 * AI 模型配置
 */
export interface AIModelConfig {
  id: string
  name: string
  baseUrl: string
  apiKey: string
  modelId: string
  isDefault?: boolean
}

/**
 * Git 平台配置
 */
export interface GitPlatformConfig {
  token: string
  owner: string
  repo: string
  branch: string
}

/**
 * 应用设置
 */
export interface AppSettings {
  aiModels: AIModelConfig[]
  activeModelId: string | null
  gitPlatforms: {
    github: GitPlatformConfig
    gitee: GitPlatformConfig
  }
}

/**
 * 从 localStorage 加载设置
 */
const DEFAULT_GIT_PLATFORM = (): GitPlatformConfig => ({
  token: '',
  owner: '',
  repo: '',
  branch: ''
})

function loadSettingsFromStorage(): AppSettings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return {
        aiModels: parsed.aiModels || [],
        activeModelId: parsed.activeModelId || null,
        gitPlatforms: {
          github: { ...DEFAULT_GIT_PLATFORM(), branch: 'main', ...parsed.gitPlatforms?.github },
          gitee: { ...DEFAULT_GIT_PLATFORM(), branch: 'master', ...parsed.gitPlatforms?.gitee }
        }
      }
    }
  } catch (error) {
    console.warn('从 localStorage 加载设置失败:', error)
  }
  return {
    aiModels: [],
    activeModelId: null,
    gitPlatforms: {
      github: { ...DEFAULT_GIT_PLATFORM(), branch: 'main' },
      gitee: { ...DEFAULT_GIT_PLATFORM(), branch: 'master' }
    }
  }
}

/**
 * 保存设置到 localStorage
 */
function saveSettingsToStorage(settings: AppSettings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch (error) {
    console.warn('保存设置到 localStorage 失败:', error)
  }
}

export const useSettingsStore = defineStore('settings', () => {
  // State
  const settings = ref<AppSettings>(loadSettingsFromStorage())

  // Getters
  const aiModels = computed(() => settings.value.aiModels)
  const activeModelId = computed(() => settings.value.activeModelId)
  
  const activeModel = computed(() => {
    if (!settings.value.activeModelId) return null
    return settings.value.aiModels.find(m => m.id === settings.value.activeModelId) || null
  })

  const hasModels = computed(() => settings.value.aiModels.length > 0)

  const gitPlatforms = computed(() => settings.value.gitPlatforms)

  function getGitPlatform(name: 'github' | 'gitee'): GitPlatformConfig {
    return settings.value.gitPlatforms[name]
  }

  function saveGitPlatform(name: 'github' | 'gitee', config: GitPlatformConfig): void {
    settings.value.gitPlatforms[name] = { ...config }
    saveSettingsToStorage(settings.value)
  }

  // Actions

  /**
   * 添加 AI 模型配置
   */
  function addModel(model: Omit<AIModelConfig, 'id'>): AIModelConfig {
    const newModel: AIModelConfig = {
      ...model,
      id: `model_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
    }
    settings.value.aiModels.push(newModel)
    
    // 如果是第一个模型，设为默认激活
    if (settings.value.aiModels.length === 1) {
      settings.value.activeModelId = newModel.id
    }
    
    saveSettingsToStorage(settings.value)
    return newModel
  }

  /**
   * 更新 AI 模型配置
   */
  function updateModel(id: string, updates: Partial<Omit<AIModelConfig, 'id'>>): boolean {
    const index = settings.value.aiModels.findIndex(m => m.id === id)
    if (index === -1) return false
    
    settings.value.aiModels[index] = {
      ...settings.value.aiModels[index],
      ...updates
    }
    saveSettingsToStorage(settings.value)
    return true
  }

  /**
   * 删除 AI 模型配置
   */
  function removeModel(id: string): boolean {
    const index = settings.value.aiModels.findIndex(m => m.id === id)
    if (index === -1) return false
    
    settings.value.aiModels.splice(index, 1)
    
    // 如果删除的是当前激活的模型，切换到第一个可用模型
    if (settings.value.activeModelId === id) {
      settings.value.activeModelId = settings.value.aiModels[0]?.id || null
    }
    
    saveSettingsToStorage(settings.value)
    return true
  }

  /**
   * 设置激活的模型
   */
  function setActiveModel(id: string): boolean {
    const model = settings.value.aiModels.find(m => m.id === id)
    if (!model) return false
    
    settings.value.activeModelId = id
    saveSettingsToStorage(settings.value)
    return true
  }

  /**
   * 获取模型配置
   */
  function getModel(id: string): AIModelConfig | undefined {
    return settings.value.aiModels.find(m => m.id === id)
  }

  /**
   * 清空所有模型配置
   */
  function clearModels(): void {
    settings.value.aiModels = []
    settings.value.activeModelId = null
    saveSettingsToStorage(settings.value)
  }

  return {
    // State
    settings,
    
    // Getters
    aiModels,
    activeModelId,
    activeModel,
    hasModels,
    gitPlatforms,

    // Actions
    addModel,
    updateModel,
    removeModel,
    setActiveModel,
    getModel,
    clearModels,
    getGitPlatform,
    saveGitPlatform
  }
})