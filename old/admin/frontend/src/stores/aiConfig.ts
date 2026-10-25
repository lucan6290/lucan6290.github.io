/**
 * AI 配置管理 Store
 * 管理 AI 模型配置，持久化到 localStorage
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * AI 模型配置接口
 */
export interface AIModelConfig {
  /** 模型名称 */
  name: string
  /** Base URL */
  baseUrl: string
  /** 模型 ID */
  modelId: string
  /** API Key */
  apiKey: string
  /** 是否为自定义模型 */
  isCustom: boolean
}

/**
 * 预设模型列表
 */
export const PRESET_MODELS: Array<Omit<AIModelConfig, 'apiKey' | 'isCustom'>> = [
  {
    name: 'DeepSeek V4 Pro（深度求索）',
    baseUrl: 'https://api.deepseek.com',
    modelId: 'deepseek-v4-pro'
  },
  {
    name: 'DeepSeek V4 Flash（深度求索）',
    baseUrl: 'https://api.deepseek.com',
    modelId: 'deepseek-v4-flash'
  },
  {
    name: 'Qwen（通义千问）',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    modelId: 'qwen-plus'
  },
  {
    name: 'GLM（智谱AI）',
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
    modelId: 'glm-4-flash'
  },
  {
    name: 'Kimi（月之暗面）',
    baseUrl: 'https://api.moonshot.cn/v1',
    modelId: 'moonshot-v1-8k'
  },
  {
    name: 'MiMo（小米）',
    baseUrl: '待确认',
    modelId: '待确认'
  }
]

const STORAGE_KEY = 'blog-admin-ai-config'

/**
 * 从 localStorage 加载配置
 */
function loadConfigFromStorage(): AIModelConfig {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const config = JSON.parse(stored) as AIModelConfig
      return {
        name: config.name || '',
        baseUrl: config.baseUrl || '',
        modelId: config.modelId || '',
        apiKey: config.apiKey || '',
        isCustom: config.isCustom || false
      }
    }
  } catch (error) {
    console.warn('从 localStorage 加载 AI 配置失败:', error)
  }
  // 返回默认配置
  return {
    name: '',
    baseUrl: '',
    modelId: '',
    apiKey: '',
    isCustom: false
  }
}

/**
 * 保存配置到 localStorage
 */
function saveConfigToStorage(config: AIModelConfig): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
  } catch (error) {
    console.warn('保存 AI 配置到 localStorage 失败:', error)
  }
}

export const useAIConfigStore = defineStore('aiConfig', () => {
  // State
  const config = ref<AIModelConfig>(loadConfigFromStorage())

  // Getters
  const hasConfig = computed(() => {
    return config.value.baseUrl && config.value.modelId && config.value.apiKey
  })

  const isPresetModel = computed(() => {
    return !config.value.isCustom && PRESET_MODELS.some(
      m => m.name === config.value.name
    )
  })

  // Actions

  /**
   * 设置模型配置
   * @param newConfig 新配置
   */
  function setConfig(newConfig: Partial<AIModelConfig>): void {
    config.value = { ...config.value, ...newConfig }
    saveConfigToStorage(config.value)
    console.log('AI 配置已更新:', config.value.name)
  }

  /**
   * 选择预设模型
   * @param modelIndex 预设模型索引
   */
  function selectPresetModel(modelIndex: number): void {
    if (modelIndex >= 0 && modelIndex < PRESET_MODELS.length) {
      const preset = PRESET_MODELS[modelIndex]
      setConfig({
        name: preset.name,
        baseUrl: preset.baseUrl,
        modelId: preset.modelId,
        isCustom: false
      })
    }
  }

  /**
   * 设置为自定义模型
   */
  function setCustomModel(): void {
    setConfig({
      name: '自定义',
      baseUrl: '',
      modelId: '',
      isCustom: true
    })
  }

  /**
   * 设置 API Key
   * @param apiKey API Key
   */
  function setApiKey(apiKey: string): void {
    setConfig({ apiKey })
  }

  /**
   * 测试连接
   * @returns 测试结果
   */
  async function testConnection(): Promise<{ success: boolean; message: string }> {
    if (!hasConfig.value) {
      return { success: false, message: '请先完成模型配置' }
    }

    try {
      // 调用 OpenAI 兼容接口测试连接
      const response = await fetch(`${config.value.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${config.value.apiKey}`
        },
        body: JSON.stringify({
          model: config.value.modelId,
          messages: [{ role: 'user', content: 'Hi' }],
          max_tokens: 5
        })
      })

      if (response.ok) {
        return { success: true, message: '连接成功！' }
      } else {
        const error = await response.text()
        return { success: false, message: `连接失败: ${response.status} ${error}` }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      return { success: false, message: `连接失败: ${errorMessage}` }
    }
  }

  /**
   * 重置配置
   */
  function resetConfig(): void {
    config.value = {
      name: '',
      baseUrl: '',
      modelId: '',
      apiKey: '',
      isCustom: false
    }
    saveConfigToStorage(config.value)
    console.log('AI 配置已重置')
  }

  return {
    // State
    config,

    // Getters
    hasConfig,
    isPresetModel,

    // Actions
    setConfig,
    selectPresetModel,
    setCustomModel,
    setApiKey,
    testConnection,
    resetConfig
  }
})
