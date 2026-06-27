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
  provider?: string
  apiFormat?: 'openai' | 'anthropic'
  anthropicBaseUrl?: string
  thinkingMode?: 'enabled' | 'disabled'
  reasoningEffort?: 'high' | 'max'
  agentMode?: boolean
  toolCalls?: boolean
  strictToolCalls?: boolean
  jsonMode?: boolean
  temperature?: number
  maxTokens?: number
  isDefault?: boolean
}

/**
 * 应用设置
 */
export interface AppSettings {
  aiModels: AIModelConfig[]
  activeModelId: string | null
}

function createDeepSeekModel(modelId: 'deepseek-v4-pro' | 'deepseek-v4-flash', apiKey = ''): AIModelConfig {
  const isFlash = modelId === 'deepseek-v4-flash'
  return {
    id: `${modelId}-default`,
    name: isFlash ? 'DeepSeek V4 Flash' : 'DeepSeek V4 Pro',
    baseUrl: 'https://api.deepseek.com',
    apiKey,
    modelId,
    provider: 'deepseek',
    apiFormat: 'openai',
    anthropicBaseUrl: 'https://api.deepseek.com/anthropic',
    thinkingMode: 'enabled',
    reasoningEffort: isFlash ? 'high' : 'max',
    agentMode: true,
    toolCalls: true,
    strictToolCalls: false,
    jsonMode: true,
    temperature: 0.3,
    maxTokens: 8192,
    isDefault: true
  }
}

function createDefaultModels(apiKey = ''): AIModelConfig[] {
  return [
    createDeepSeekModel('deepseek-v4-pro', apiKey),
    createDeepSeekModel('deepseek-v4-flash', apiKey)
  ]
}

function isDeepSeekModel(model: Partial<AIModelConfig>): boolean {
  return model.provider === 'deepseek' || /deepseek/i.test(`${model.name} ${model.baseUrl} ${model.modelId}`)
}

function ensureDefaultModels(models: AIModelConfig[]): AIModelConfig[] {
  const deepSeekApiKey = models.find(model => isDeepSeekModel(model) && model.apiKey)?.apiKey || ''
  const nextModels = [...models]

  for (const defaultModel of createDefaultModels(deepSeekApiKey)) {
    const hasModel = nextModels.some(model => model.modelId === defaultModel.modelId)
    if (!hasModel) nextModels.push(defaultModel)
  }

  return nextModels
}

function normalizeModel(model: Partial<AIModelConfig>): AIModelConfig {
  const isDeepSeek = isDeepSeekModel(model)
  const normalized: AIModelConfig = {
    id: model.id || `model_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    name: model.name || (isDeepSeek ? 'DeepSeek V4 Pro' : '未命名模型'),
    baseUrl: model.baseUrl || (isDeepSeek ? 'https://api.deepseek.com' : ''),
    apiKey: model.apiKey || '',
    modelId: model.modelId || (isDeepSeek ? 'deepseek-v4-pro' : ''),
    provider: model.provider || (isDeepSeek ? 'deepseek' : 'custom'),
    apiFormat: model.apiFormat || 'openai',
    anthropicBaseUrl: model.anthropicBaseUrl || (isDeepSeek ? 'https://api.deepseek.com/anthropic' : ''),
    thinkingMode: model.thinkingMode || (isDeepSeek ? 'enabled' : 'disabled'),
    reasoningEffort: model.reasoningEffort || (isDeepSeek ? 'max' : 'high'),
    agentMode: model.agentMode ?? isDeepSeek,
    toolCalls: model.toolCalls ?? isDeepSeek,
    strictToolCalls: model.strictToolCalls ?? false,
    jsonMode: model.jsonMode ?? isDeepSeek,
    temperature: model.temperature ?? 0.3,
    maxTokens: model.maxTokens ?? (isDeepSeek ? 8192 : 4096),
    isDefault: model.isDefault
  }

  if (isDeepSeek && ['deepseek-chat', 'deepseek-reasoner'].includes(normalized.modelId)) {
    normalized.modelId = 'deepseek-v4-pro'
    normalized.baseUrl = 'https://api.deepseek.com'
    normalized.thinkingMode = 'enabled'
    normalized.reasoningEffort = 'max'
  }

  return normalized
}

/**
 * 从 localStorage 加载设置
 */
function loadSettingsFromStorage(): AppSettings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      const models: AIModelConfig[] = Array.isArray(parsed.aiModels)
        ? parsed.aiModels.map((model: Partial<AIModelConfig>) => normalizeModel(model))
        : []
      const aiModels = ensureDefaultModels(models)
      const activeModelId = aiModels.some(model => model.id === parsed.activeModelId)
        ? parsed.activeModelId
        : aiModels[0]?.id || null
      return {
        aiModels,
        activeModelId
      }
    }
  } catch (error) {
    console.warn('从 localStorage 加载设置失败:', error)
  }
  return {
    aiModels: createDefaultModels(),
    activeModelId: 'deepseek-v4-pro-default'
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

  // Actions

  /**
   * 添加 AI 模型配置
   */
  function addModel(model: Omit<AIModelConfig, 'id'>): AIModelConfig {
    const newModel = normalizeModel({
      ...model,
      id: `model_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
    })
    settings.value.aiModels.push(newModel)
    syncDeepSeekApiKey(newModel)
    
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
      ...normalizeModel({
        ...settings.value.aiModels[index],
        ...updates
      })
    }
    syncDeepSeekApiKey(settings.value.aiModels[index])
    saveSettingsToStorage(settings.value)
    return true
  }

  function syncDeepSeekApiKey(sourceModel: AIModelConfig): void {
    if (!isDeepSeekModel(sourceModel) || !sourceModel.apiKey) return

    settings.value.aiModels = settings.value.aiModels.map(model => {
      if (model.id === sourceModel.id || !isDeepSeekModel(model) || model.apiKey) {
        return model
      }
      return { ...model, apiKey: sourceModel.apiKey }
    })
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

    // Actions
    addModel,
    updateModel,
    removeModel,
    setActiveModel,
    getModel,
    clearModels
  }
})
