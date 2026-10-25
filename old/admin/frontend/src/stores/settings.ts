/**
 * 设置管理 Store
 * AI 模型配置由后端保存，前端只持久化当前选中的模型 ID。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAPI } from '@/api'
import type { AIModelConfigDTO } from '@/types/api'

const STORAGE_KEY = 'blog-admin-settings'

/**
 * AI 模型配置。
 * 后端列表不会返回 apiKey，编辑时留空表示不修改已保存密钥。
 */
export interface AIModelConfig extends AIModelConfigDTO {
  apiKey: string
  anthropicBaseUrl?: string
  agentMode?: boolean
  toolCalls?: boolean
  strictToolCalls?: boolean
  jsonMode?: boolean
}

/**
 * 应用设置
 */
export interface AppSettings {
  aiModels: AIModelConfig[]
  activeModelId: string | null
}

function createModelId(model: Partial<AIModelConfig>): string {
  const raw = model.modelId || model.name || 'model'
  const slug = raw
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return `${slug || 'model'}-${Date.now()}`
}

function isDeepSeekModel(model: Partial<AIModelConfig>): boolean {
  return model.provider === 'deepseek' || /deepseek/i.test(`${model.name} ${model.baseUrl} ${model.modelId}`)
}

function normalizeModel(model: Partial<AIModelConfig>): AIModelConfig {
  const isDeepSeek = isDeepSeekModel(model)
  return {
    id: model.id || createModelId(model),
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
    isDefault: model.isDefault ?? false
  }
}

function toBackendModel(model: AIModelConfig): AIModelConfigDTO & { apiKey?: string } {
  return {
    id: model.id,
    name: model.name,
    provider: model.provider || 'custom',
    baseUrl: model.baseUrl,
    apiKey: model.apiKey || '',
    modelId: model.modelId,
    apiFormat: model.apiFormat || 'openai',
    temperature: model.temperature ?? 0.3,
    maxTokens: model.maxTokens ?? 4096,
    thinkingMode: model.thinkingMode || 'disabled',
    reasoningEffort: model.reasoningEffort || 'high',
    isDefault: model.isDefault ?? false
  }
}

/**
 * 从 localStorage 加载当前选中模型 ID。
 */
function loadSettingsFromStorage(): AppSettings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return {
        aiModels: [],
        activeModelId: typeof parsed.activeModelId === 'string' ? parsed.activeModelId : null
      }
    }
  } catch (error) {
    console.warn('从 localStorage 加载设置失败:', error)
  }
  return {
    aiModels: [],
    activeModelId: null
  }
}

/**
 * 只保存本地 UI 偏好，不保存模型密钥。
 */
function saveSettingsToStorage(settings: AppSettings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ activeModelId: settings.activeModelId }))
  } catch (error) {
    console.warn('保存设置到 localStorage 失败:', error)
  }
}

export const useSettingsStore = defineStore('settings', () => {
  // State
  const settings = ref<AppSettings>(loadSettingsFromStorage())
  const isLoadingModels = ref(false)
  const modelLoadError = ref<string | null>(null)

  // Getters
  const aiModels = computed(() => settings.value.aiModels)
  const activeModelId = computed(() => settings.value.activeModelId)

  const activeModel = computed(() => {
    if (!settings.value.activeModelId) return null
    return settings.value.aiModels.find(m => m.id === settings.value.activeModelId) || null
  })

  const hasModels = computed(() => settings.value.aiModels.length > 0)

  function replaceModels(models: Partial<AIModelConfig>[]): void {
    const normalized = models.map(model => normalizeModel(model))
    settings.value.aiModels = normalized

    const activeExists = normalized.some(model => model.id === settings.value.activeModelId)
    if (!activeExists) {
      settings.value.activeModelId =
        normalized.find(model => model.isDefault)?.id ||
        normalized[0]?.id ||
        null
    }

    saveSettingsToStorage(settings.value)
  }

  // Actions

  /**
   * 从后端加载 AI 模型配置。
   */
  async function loadAIModels(): Promise<AIModelConfig[]> {
    const api = getAPI()
    if (!api.getAIModels) return settings.value.aiModels

    isLoadingModels.value = true
    modelLoadError.value = null
    try {
      const models = await api.getAIModels()
      replaceModels(models)
      return settings.value.aiModels
    } catch (error: any) {
      modelLoadError.value = error?.message || 'AI 模型配置加载失败'
      throw error
    } finally {
      isLoadingModels.value = false
    }
  }

  /**
   * 添加 AI 模型配置。
   */
  async function addModel(model: Omit<AIModelConfig, 'id'>): Promise<AIModelConfig> {
    const api = getAPI()
    if (!api.saveAIModel) throw new Error('后端未提供 AI 模型保存接口')

    const newModel = normalizeModel({
      ...model,
      id: createModelId(model)
    })
    const saved = await api.saveAIModel(toBackendModel(newModel))
    const normalized = normalizeModel(saved)
    settings.value.aiModels = [
      ...settings.value.aiModels.filter(item => item.id !== normalized.id),
      normalized
    ]
    settings.value.activeModelId = normalized.id
    saveSettingsToStorage(settings.value)
    return normalized
  }

  /**
   * 更新 AI 模型配置。
   */
  async function updateModel(id: string, updates: Partial<Omit<AIModelConfig, 'id'>>): Promise<boolean> {
    const api = getAPI()
    if (!api.saveAIModel) throw new Error('后端未提供 AI 模型保存接口')

    const current = settings.value.aiModels.find(m => m.id === id)
    if (!current) return false

    const nextModel = normalizeModel({
      ...current,
      ...updates,
      id
    })
    const saved = await api.saveAIModel(toBackendModel(nextModel))
    const normalized = normalizeModel(saved)
    const index = settings.value.aiModels.findIndex(m => m.id === id)
    if (index >= 0) settings.value.aiModels[index] = normalized
    saveSettingsToStorage(settings.value)
    return true
  }

  /**
   * 删除 AI 模型配置。
   */
  async function removeModel(id: string): Promise<boolean> {
    const api = getAPI()
    if (!api.deleteAIModel) throw new Error('后端未提供 AI 模型删除接口')

    const exists = settings.value.aiModels.some(m => m.id === id)
    if (!exists) return false

    const nextModels = await api.deleteAIModel(id)
    replaceModels(nextModels)
    return true
  }

  /**
   * 设置激活的模型。
   */
  function setActiveModel(id: string): boolean {
    const model = settings.value.aiModels.find(m => m.id === id)
    if (!model) return false

    settings.value.activeModelId = id
    saveSettingsToStorage(settings.value)
    return true
  }

  /**
   * 获取模型配置。
   */
  function getModel(id: string): AIModelConfig | undefined {
    return settings.value.aiModels.find(m => m.id === id)
  }

  /**
   * 清空所有模型配置。
   */
  async function clearModels(): Promise<void> {
    for (const model of [...settings.value.aiModels]) {
      await removeModel(model.id)
    }
    settings.value.aiModels = []
    settings.value.activeModelId = null
    saveSettingsToStorage(settings.value)
  }

  async function testModel(id: string): Promise<boolean> {
    const api = getAPI()
    if (!api.testAIModel) throw new Error('后端未提供 AI 模型测试接口')
    const result = await api.testAIModel(id)
    return result.success
  }

  return {
    // State
    settings,
    isLoadingModels,
    modelLoadError,

    // Getters
    aiModels,
    activeModelId,
    activeModel,
    hasModels,

    // Actions
    loadAIModels,
    addModel,
    updateModel,
    removeModel,
    setActiveModel,
    getModel,
    clearModels,
    testModel
  }
})
