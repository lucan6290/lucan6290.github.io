<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import {
  NDrawer,
  NDrawerContent,
  NCard,
  NButton,
  NInput,
  NInputNumber,
  NCheckbox,
  NSpace,
  NText,
  NTag,
  NIcon,
  NSelect,
  NModal,
  NForm,
  NFormItem,
  NInputGroup,
  NInputGroupLabel,
  NDivider,
  NSpin,
  NEmpty,
  NPopconfirm,
  useMessage,
  type SelectOption
} from 'naive-ui'
import { getAPI } from '@/api'
import { useSettingsStore, type AIModelConfig } from '@/stores/settings'
import ApprovalModeSelect from '@/components/ai-writing/ApprovalModeSelect.vue'
import type { AIApprovalMode, AIEditOperation, AIEditScope, AIModelPayload } from '@/types/ai-writing'

// Props
interface Props {
  articlePath?: string
  editorContent?: string
  selectedText?: string
  cursorPosition?: number
  hasUnsavedChanges?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  articlePath: '',
  editorContent: '',
  selectedText: '',
  cursorPosition: 0,
  hasUnsavedChanges: false
})

// Emits
const emit = defineEmits<{
  (e: 'insert-text', text: string, position?: number): void
  (e: 'replace-text', text: string, start: number, end: number): void
  (e: 'applied'): void
  (e: 'close'): void
}>()

// Store
const settingsStore = useSettingsStore()
const message = useMessage()

// 状态
const drawerVisible = ref(true)
const activeTab = ref<'chat' | 'settings'>('chat')
const chatInput = ref('')
const approvalMode = ref<AIApprovalMode>('request-approval')
const chatHistory = ref<Array<{ role: 'user' | 'assistant' | 'system'; content: string }>>([])
const isGenerating = ref(false)
const generatedContent = ref('')
const currentOperation = ref<AIEditOperation | null>(null)
const editSessionId = ref<string | null>(null)
const abortController = ref<AbortController | null>(null)

// 设置相关
const showModelEditor = ref(false)
const editingModel = ref<AIModelConfig | null>(null)
const modelForm = ref({
  name: '',
  baseUrl: '',
  apiKey: '',
  modelId: '',
  provider: 'custom',
  apiFormat: 'openai' as 'openai' | 'anthropic',
  anthropicBaseUrl: '',
  thinkingMode: 'disabled' as 'enabled' | 'disabled',
  reasoningEffort: 'high' as 'high' | 'max',
  agentMode: false,
  toolCalls: false,
  strictToolCalls: false,
  jsonMode: false,
  temperature: 0.3,
  maxTokens: 4096
})

const thinkingOptions: SelectOption[] = [
  { label: '关闭', value: 'disabled' },
  { label: '开启', value: 'enabled' }
]

const reasoningEffortOptions: SelectOption[] = [
  { label: 'High', value: 'high' },
  { label: 'Max', value: 'max' }
]

// 快捷菜单选项
const quickMenuOptions = [
  { label: '优化润色', value: 'optimize', prompt: '请优化润色以下内容，保持原意的同时让表达更加流畅、专业：' },
  { label: '续写内容', value: 'continue', prompt: '请续写以下内容，保持风格一致：' },
  { label: '改写风格', value: 'rewrite', prompt: '请改写以下内容，使其更加生动有趣：' },
  { label: '翻译（中译英）', value: 'translate-zh-en', prompt: '请将以下中文内容翻译成英文：' },
  { label: '翻译（英译中）', value: 'translate-en-zh', prompt: '请将以下英文内容翻译成中文：' },
  { label: '生成大纲', value: 'outline', prompt: '请根据以下内容生成一份结构清晰的大纲：' },
  { label: '全文生成', value: 'generate-full', prompt: '请根据以下大纲或主题生成一篇完整的文章：' },
  { label: '总结摘要', value: 'summarize', prompt: '请总结以下内容，生成一段精炼的摘要：' }
]

// 模型预设
const MODEL_PRESETS = [
  {
    label: 'DeepSeek（深度求索）',
    value: 'deepseek',
    name: 'DeepSeek V4 Pro',
    baseUrl: 'https://api.deepseek.com',
    modelId: 'deepseek-v4-pro',
    provider: 'deepseek',
    apiFormat: 'openai' as const,
    anthropicBaseUrl: 'https://api.deepseek.com/anthropic',
    thinkingMode: 'enabled' as const,
    reasoningEffort: 'max' as const,
    agentMode: true,
    toolCalls: true,
    strictToolCalls: false,
    jsonMode: true,
    temperature: 0.3,
    maxTokens: 8192
  },
  {
    label: 'DeepSeek V4 Flash（深度求索）',
    value: 'deepseek-flash',
    name: 'DeepSeek V4 Flash',
    baseUrl: 'https://api.deepseek.com',
    modelId: 'deepseek-v4-flash',
    provider: 'deepseek',
    apiFormat: 'openai' as const,
    anthropicBaseUrl: 'https://api.deepseek.com/anthropic',
    thinkingMode: 'enabled' as const,
    reasoningEffort: 'high' as const,
    agentMode: true,
    toolCalls: true,
    strictToolCalls: false,
    jsonMode: true,
    temperature: 0.3,
    maxTokens: 8192
  },
  {
    label: 'Qwen（通义千问）',
    value: 'qwen',
    name: '通义千问',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    modelId: 'qwen-plus'
  },
  {
    label: 'GLM（智谱AI）',
    value: 'glm',
    name: '智谱AI',
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
    modelId: 'glm-4-flash'
  },
  {
    label: 'Kimi（月之暗面）',
    value: 'kimi',
    name: 'Kimi',
    baseUrl: 'https://api.moonshot.cn/v1',
    modelId: 'moonshot-v1-8k'
  },
  {
    label: 'MiMo（小米）',
    value: 'mimo',
    name: 'MiMo',
    baseUrl: 'https://platform.xiaomimimo.com/v1',
    modelId: 'mimo-chat'
  }
]

// 对话上下文最大轮次（保留最近 N 轮对话）
const MAX_CHAT_ROUNDS = 10

// 不同场景的系统提示词
const SYSTEM_PROMPTS: Record<string, string> = {
  'optimize': '你是一个专业的写作润色助手。请直接输出优化后的内容，不要添加额外的解释或说明。',
  'continue': '你是一个专业的写作助手，擅长续写内容并保持风格一致。请直接输出续写的内容，不要添加额外的解释。',
  'rewrite': '你是一个创意写作助手，擅长改写内容使其更加生动有趣。请直接输出改写后的内容。',
  'translate-zh-en': '你是一个专业的翻译助手，擅长将中文翻译为地道的英文。请直接输出翻译结果。',
  'translate-en-zh': '你是一个专业的翻译助手，擅长将英文翻译为流畅的中文。请直接输出翻译结果。',
  'outline': '你是一个专业的内容策划助手，擅长为文章生成结构清晰的大纲。请直接输出大纲内容。',
  'generate-full': '你是一个专业的写作助手，擅长根据大纲或主题生成完整的文章。请直接输出文章内容。',
  'summarize': '你是一个专业的内容总结助手，擅长提取文章核心内容生成精炼摘要。请直接输出摘要。',
  'default': '你是一个专业的写作助手，帮助用户改进文章内容。请直接输出处理后的内容，不要添加额外的解释或说明。'
}

const APPROVAL_PROMPTS: Record<AIApprovalMode, string> = {
  'request-approval': '当前权限为请求批准。你只能生成建议或待采纳内容，不要声称已经写入、保存、发布或删除任何内容。',
  'delegate-approval': '当前权限为替我审批。你可以给出低风险编辑建议，但删除、全文重写、分类变更和事实不确定内容必须提示用户确认。',
  'full-access': '当前权限为完全访问权限，但范围仅限当前 AI 写作助手任务。不得发布文章、提交 Git、删除文件、修改主题源码或绕过系统校验。'
}

// 预设选中状态
const selectedPreset = ref<string | null>(null)

// 模型选项
const modelOptions = computed<SelectOption[]>(() => {
  return settingsStore.aiModels.map(model => ({
    label: model.name,
    value: model.id
  }))
})

// 当前激活的模型
const currentModel = computed(() => settingsStore.activeModel)

// 是否有选中文本
const hasSelection = computed(() => props.selectedText && props.selectedText.length > 0)

// 是否可以采纳
const canAdopt = computed(() => generatedContent.value.length > 0)

// 发送消息
async function sendMessage(content?: string) {
  const input = content || chatInput.value.trim()
  if (!input) return

  if (!currentModel.value) {
    message.warning('请先配置 AI 模型')
    activeTab.value = 'settings'
    return
  }

  // 添加用户消息
  chatHistory.value.push({ role: 'user', content: input })
  chatInput.value = ''

  // 裁剪对话历史，保留最近 N 轮
  trimChatHistory()

  // 开始生成
  if (props.articlePath) {
    if (props.hasUnsavedChanges) {
      message.warning('当前文章有未保存更改，请先保存后再使用结构化编辑')
      return
    }
    await generateStructuredEdit(input)
  } else {
    await generateResponse(input)
  }
}

// 处理快捷菜单
async function handleQuickMenu(option: typeof quickMenuOptions[0]) {
  if (!hasSelection.value) {
    message.warning('请先选中需要处理的文本')
    return
  }

  if (!currentModel.value) {
    message.warning('请先配置 AI 模型')
    activeTab.value = 'settings'
    return
  }

  const prompt = `${option.prompt}\n\n${props.selectedText}`
  chatHistory.value.push({ role: 'user', content: `${option.label}：${props.selectedText}` })

  // 裁剪对话历史
  trimChatHistory()

  if (props.articlePath) {
    if (props.hasUnsavedChanges) {
      message.warning('当前文章有未保存更改，请先保存后再使用结构化编辑')
      return
    }
    await generateStructuredEdit(prompt)
  } else {
    await generateResponse(prompt, option.value)
  }
}

function activeModelPayload(): AIModelPayload | null {
  if (!currentModel.value) return null
  return {
    baseUrl: currentModel.value.baseUrl,
    apiKey: currentModel.value.apiKey,
    modelId: currentModel.value.modelId,
    provider: currentModel.value.provider,
    apiFormat: currentModel.value.apiFormat,
    anthropicBaseUrl: currentModel.value.anthropicBaseUrl,
    thinkingMode: currentModel.value.thinkingMode,
    reasoningEffort: currentModel.value.reasoningEffort,
    agentMode: currentModel.value.agentMode,
    toolCalls: currentModel.value.toolCalls,
    strictToolCalls: currentModel.value.strictToolCalls,
    jsonMode: currentModel.value.jsonMode,
    temperature: currentModel.value.temperature ?? 0.3,
    maxTokens: currentModel.value.maxTokens ?? 4096
  }
}

function resolveScope(instruction: string): AIEditScope {
  const normalized = instruction.toLowerCase()
  if (normalized.includes('标题') || normalized.includes('description') || normalized.includes('front matter')) {
    return 'frontmatter'
  }
  if (normalized.includes('全文') || normalized.includes('重写') || normalized.includes('整体')) {
    return 'document'
  }
  if (hasSelection.value) return 'selection'
  return 'cursor'
}

function operationPreview(operation: AIEditOperation): string {
  const chunks = [`操作：${operation.type} / ${operation.scope}`, `摘要：${operation.summary}`]
  if (operation.oldText) chunks.push(`原文：\n${operation.oldText}`)
  if (operation.newText) chunks.push(`新内容：\n${operation.newText}`)
  if (operation.frontMatterPatch) chunks.push(`Front Matter：\n${JSON.stringify(operation.frontMatterPatch, null, 2)}`)
  if (operation.riskFlags.length) chunks.push(`风险：${operation.riskFlags.join('；')}`)
  return chunks.join('\n\n')
}

async function generateStructuredEdit(userInput: string) {
  const api = getAPI()
  const model = activeModelPayload()
  if (!model || !api.generateEditPlan) return

  isGenerating.value = true
  generatedContent.value = ''
  currentOperation.value = null

  try {
    const response = await api.generateEditPlan({
      sessionId: editSessionId.value || undefined,
      articlePath: props.articlePath,
      instruction: userInput,
      approvalMode: approvalMode.value,
      scope: resolveScope(userInput),
      selection: hasSelection.value ? { text: props.selectedText } : undefined,
      model
    })

    editSessionId.value = response.sessionId
    currentOperation.value = response.operation

    if (!response.operation) {
      generatedContent.value = response.validationErrors?.join('；') || 'AI 未生成可执行编辑方案'
      chatHistory.value.push({ role: 'assistant', content: generatedContent.value })
      return
    }

    generatedContent.value = operationPreview(response.operation)
    chatHistory.value.push({ role: 'assistant', content: generatedContent.value })
  } catch (error: any) {
    console.error('结构化编辑生成失败:', error)
    message.error(`生成失败: ${error.message || error}`)
  } finally {
    isGenerating.value = false
  }
}

// 生成响应（流式）
async function generateResponse(userInput: string, scene?: string) {
  if (!currentModel.value) return

  isGenerating.value = true
  generatedContent.value = ''

  // 创建 AbortController
  abortController.value = new AbortController()

  // 根据场景选择系统提示词
  const baseSystemPrompt = scene ? (SYSTEM_PROMPTS[scene] || SYSTEM_PROMPTS['default']) : SYSTEM_PROMPTS['default']
  const systemPrompt = `${baseSystemPrompt}\n\n${APPROVAL_PROMPTS[approvalMode.value]}`

  try {
    const response = await fetch(`${currentModel.value.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentModel.value.apiKey}`
      },
      body: JSON.stringify({
        model: currentModel.value.modelId,
        messages: [
          { role: 'system', content: systemPrompt },
          ...chatHistory.value.slice(0, -1), // 不包括刚添加的用户消息
          { role: 'user', content: userInput }
        ],
        stream: true,
        thinking: currentModel.value.provider === 'deepseek'
          ? { type: currentModel.value.thinkingMode || 'disabled' }
          : undefined,
        reasoning_effort: currentModel.value.provider === 'deepseek' && currentModel.value.thinkingMode === 'enabled'
          ? currentModel.value.reasoningEffort || 'high'
          : undefined,
        max_tokens: currentModel.value.maxTokens || 4096
      }),
      signal: abortController.value.signal
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No reader available')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue

          try {
            const parsed = JSON.parse(data)
            const content = parsed.choices?.[0]?.delta?.content
            if (content) {
              generatedContent.value += content
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    // 添加助手消息到历史
    chatHistory.value.push({ role: 'assistant', content: generatedContent.value })

  } catch (error: any) {
    if (error.name === 'AbortError') {
      message.info('已停止生成')
    } else {
      console.error('生成失败:', error)
      message.error(`生成失败: ${error.message}`)
    }
  } finally {
    isGenerating.value = false
    abortController.value = null
  }
}

// 裁剪对话历史，保留最近 MAX_CHAT_ROUNDS 轮
function trimChatHistory() {
  // 每轮对话 = 1 user + 1 assistant 消息
  const maxMessages = MAX_CHAT_ROUNDS * 2
  if (chatHistory.value.length > maxMessages) {
    chatHistory.value = chatHistory.value.slice(-maxMessages)
  }
}

// 停止生成
function stopGeneration() {
  if (abortController.value) {
    abortController.value.abort()
  }
}

// 采纳内容
function adoptContent() {
  if (!canAdopt.value) return

  if (currentOperation.value && props.articlePath) {
    applyStructuredEdit()
    return
  }

  // 如果有选中文本，替换；否则插入
  if (hasSelection.value) {
    // 这里需要父组件提供选中范围信息
    emit('insert-text', generatedContent.value)
  } else {
    emit('insert-text', generatedContent.value)
  }

  message.success('已采纳内容')
  generatedContent.value = ''
}

async function applyStructuredEdit() {
  const api = getAPI()
  if (!currentOperation.value || !props.articlePath || !editSessionId.value || !api.applyEditPlan) return

  isGenerating.value = true
  try {
    await api.applyEditPlan({
      sessionId: editSessionId.value,
      articlePath: props.articlePath,
      approvalMode: approvalMode.value,
      confirmed: true,
      operation: currentOperation.value
    })
    message.success('编辑已应用')
    generatedContent.value = ''
    currentOperation.value = null
    emit('applied')
  } catch (error: any) {
    message.error(`应用失败: ${error.message || error}`)
  } finally {
    isGenerating.value = false
  }
}

// 放弃内容
function discardContent() {
  generatedContent.value = ''
  message.info('已放弃内容')
}

// 清空对话历史
function clearHistory() {
  chatHistory.value = []
  generatedContent.value = ''
  message.success('已清空对话历史')
}

// 模型管理
function openAddModel() {
  editingModel.value = null
  modelForm.value = {
    name: '',
    baseUrl: '',
    apiKey: '',
    modelId: '',
    provider: 'custom',
    apiFormat: 'openai',
    anthropicBaseUrl: '',
    thinkingMode: 'disabled',
    reasoningEffort: 'high',
    agentMode: false,
    toolCalls: false,
    strictToolCalls: false,
    jsonMode: false,
    temperature: 0.3,
    maxTokens: 4096
  }
  selectedPreset.value = null
  showModelEditor.value = true
}

function openEditModel(model: AIModelConfig) {
  editingModel.value = model
  modelForm.value = {
    name: model.name,
    baseUrl: model.baseUrl,
    apiKey: model.apiKey,
    modelId: model.modelId,
    provider: model.provider || 'custom',
    apiFormat: model.apiFormat || 'openai',
    anthropicBaseUrl: model.anthropicBaseUrl || '',
    thinkingMode: model.thinkingMode || 'disabled',
    reasoningEffort: model.reasoningEffort || 'high',
    agentMode: model.agentMode || false,
    toolCalls: model.toolCalls || false,
    strictToolCalls: model.strictToolCalls || false,
    jsonMode: model.jsonMode || false,
    temperature: model.temperature ?? 0.3,
    maxTokens: model.maxTokens ?? 4096
  }
  selectedPreset.value = null
  showModelEditor.value = true
}

// 选择预设模型
function handlePresetSelect(value: string) {
  const preset = MODEL_PRESETS.find(p => p.value === value)
  if (preset) {
    modelForm.value.name = preset.name
    modelForm.value.baseUrl = preset.baseUrl
    modelForm.value.modelId = preset.modelId
    modelForm.value.provider = preset.provider || 'custom'
    modelForm.value.apiFormat = preset.apiFormat || 'openai'
    modelForm.value.anthropicBaseUrl = preset.anthropicBaseUrl || ''
    modelForm.value.thinkingMode = preset.thinkingMode || 'disabled'
    modelForm.value.reasoningEffort = preset.reasoningEffort || 'high'
    modelForm.value.agentMode = preset.agentMode || false
    modelForm.value.toolCalls = preset.toolCalls || false
    modelForm.value.strictToolCalls = preset.strictToolCalls || false
    modelForm.value.jsonMode = preset.jsonMode || false
    modelForm.value.temperature = preset.temperature ?? 0.3
    modelForm.value.maxTokens = preset.maxTokens ?? 4096
    // API Key 需要用户自己填写
    selectedPreset.value = value
  }
}

function saveModel() {
  if (!modelForm.value.name || !modelForm.value.baseUrl || !modelForm.value.apiKey || !modelForm.value.modelId) {
    message.warning('请填写所有必填字段')
    return
  }

  if (editingModel.value) {
    // 更新
    settingsStore.updateModel(editingModel.value.id, modelForm.value)
    message.success('模型已更新')
  } else {
    // 添加
    settingsStore.addModel(modelForm.value)
    message.success('模型已添加')
  }

  showModelEditor.value = false
}

function deleteModel(id: string) {
  settingsStore.removeModel(id)
  message.success('模型已删除')
}

// 切换模型
function handleModelChange(id: string) {
  settingsStore.setActiveModel(id)
  message.success(`已切换到 ${settingsStore.getModel(id)?.name}`)
}

// 测试连接
const isTesting = ref(false)
const testResult = ref<'success' | 'failed' | null>(null)

async function testConnection() {
  if (!currentModel.value) {
    message.warning('请先选择一个模型')
    return
  }

  isTesting.value = true
  testResult.value = null

  try {
    const response = await fetch(`${currentModel.value.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentModel.value.apiKey}`
      },
        body: JSON.stringify({
          model: currentModel.value.modelId,
          messages: [{ role: 'user', content: 'Hi' }],
          thinking: currentModel.value.provider === 'deepseek'
            ? { type: currentModel.value.thinkingMode || 'disabled' }
            : undefined,
          reasoning_effort: currentModel.value.provider === 'deepseek' && currentModel.value.thinkingMode === 'enabled'
            ? currentModel.value.reasoningEffort || 'high'
            : undefined,
          max_tokens: 5
        })
      })

    if (response.ok) {
      testResult.value = 'success'
      message.success('连接测试成功')
    } else {
      testResult.value = 'failed'
      message.error(`连接测试失败: HTTP ${response.status}`)
    }
  } catch (error: any) {
    testResult.value = 'failed'
    message.error(`连接测试失败: ${error.message}`)
  } finally {
    isTesting.value = false
  }
}

// 切换抽屉
function toggleDrawer() {
  drawerVisible.value = !drawerVisible.value
}

// 暴露方法给父组件
defineExpose({
  toggleDrawer,
  handleQuickMenu
})
</script>

<template>
  <div class="ai-assistant">
    <!-- 收起状态的按钮 -->
    <div v-if="!drawerVisible" class="collapsed-button" @click="toggleDrawer">
      <n-button circle size="large">
        <template #icon>
          <n-icon size="24">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
            </svg>
          </n-icon>
        </template>
      </n-button>
    </div>

    <!-- 侧边栏 -->
    <n-drawer v-model:show="drawerVisible" :width="450" placement="right">
      <n-drawer-content title="AI 写作助手" closable>
        <!-- 标签切换 -->
        <div class="tab-header">
          <n-button
            :type="activeTab === 'chat' ? 'primary' : 'default'"
            @click="activeTab = 'chat'"
          >
            对话
          </n-button>
          <n-button
            :type="activeTab === 'settings' ? 'primary' : 'default'"
            @click="activeTab = 'settings'"
          >
            设置
          </n-button>
        </div>

        <!-- 对话界面 -->
        <div v-if="activeTab === 'chat'" class="chat-container">
          <!-- 快捷菜单 -->
          <div v-if="hasSelection" class="quick-menu">
            <n-text depth="3" style="font-size: 12px;">选中文本操作：</n-text>
            <n-space size="small" wrap>
              <n-button
                v-for="option in quickMenuOptions"
                :key="option.value"
                size="small"
                :disabled="isGenerating"
                @click="handleQuickMenu(option)"
              >
                {{ option.label }}
              </n-button>
            </n-space>
          </div>

          <!-- 模型选择 -->
          <div class="model-selector">
            <n-text depth="3" style="font-size: 12px;">当前模型：</n-text>
            <n-select
              v-if="modelOptions.length > 0"
              :value="currentModel?.id"
              :options="modelOptions"
              size="small"
              class="model-selector-select"
              @update:value="handleModelChange"
            />
            <n-text v-else depth="3" style="font-size: 12px;">
              未配置模型
            </n-text>
          </div>

          <approval-mode-select
            v-model:value="approvalMode"
            :disabled="isGenerating"
            class="drawer-approval"
          />

          <!-- 对话历史 -->
          <div class="chat-history">
            <n-empty v-if="chatHistory.length === 0" description="开始对话吧" />
            <div v-else class="messages">
              <div
                v-for="(msg, index) in chatHistory"
                :key="index"
                :class="['message', msg.role]"
              >
                <n-card size="small" :bordered="false">
                  <n-text>{{ msg.content }}</n-text>
                </n-card>
              </div>
            </div>
          </div>

          <!-- 生成中的内容 -->
          <div v-if="isGenerating || generatedContent" class="generating-content">
            <n-card size="small" title="生成结果">
              <n-spin v-if="isGenerating && !generatedContent" size="small" />
              <n-text v-else>{{ generatedContent }}</n-text>

              <!-- 采纳/放弃按钮 -->
              <template v-if="canAdopt && !isGenerating" #footer>
                <n-space justify="end">
                  <n-button size="small" @click="discardContent">放弃</n-button>
                  <n-button type="primary" size="small" @click="adoptContent">采纳</n-button>
                </n-space>
              </template>
            </n-card>
          </div>

          <!-- 输入区 -->
          <div class="chat-input">
            <n-input
              v-model:value="chatInput"
              type="textarea"
              placeholder="输入问题或指令..."
              :rows="3"
              :disabled="isGenerating"
              @keydown.enter.ctrl="sendMessage()"
            />
            <n-space justify="end" style="margin-top: 8px;">
              <n-button
                v-if="isGenerating"
                type="error"
                size="small"
                @click="stopGeneration"
              >
                停止
              </n-button>
              <n-button
                v-else
                type="primary"
                size="small"
                :disabled="!chatInput.trim()"
                @click="sendMessage()"
              >
                发送
              </n-button>
            </n-space>
          </div>

          <!-- 清空历史按钮 -->
          <div v-if="chatHistory.length > 0" style="margin-top: 8px;">
            <n-popconfirm @positive-click="clearHistory">
              <template #trigger>
                <n-button size="small" type="error" ghost>清空对话历史</n-button>
              </template>
              确定要清空对话历史吗？
            </n-popconfirm>
          </div>
        </div>

        <!-- 设置界面 -->
        <div v-else class="settings-container">
          <!-- 模型列表 -->
          <div class="model-list">
            <n-space justify="space-between" align="center">
              <n-text strong>模型配置</n-text>
              <n-button size="small" @click="openAddModel">添加模型</n-button>
            </n-space>

            <n-divider />

            <div v-if="settingsStore.aiModels.length === 0" class="empty-models">
              <n-empty description="暂无模型配置" />
            </div>

            <div v-else class="model-cards">
              <n-card
                v-for="model in settingsStore.aiModels"
                :key="model.id"
                size="small"
                :class="{ active: model.id === settingsStore.activeModelId }"
              >
                <n-space vertical size="small">
                  <n-space justify="space-between" align="center">
                    <n-text strong>{{ model.name }}</n-text>
                    <n-space size="small">
                      <n-button size="tiny" @click="openEditModel(model)">编辑</n-button>
                      <n-popconfirm @positive-click="deleteModel(model.id)">
                        <template #trigger>
                          <n-button size="tiny" type="error">删除</n-button>
                        </template>
                        确定删除此模型吗？
                      </n-popconfirm>
                    </n-space>
                  </n-space>
                  <n-text depth="3" style="font-size: 12px;">
                    {{ model.modelId }}
                  </n-text>
                  <n-text depth="3" style="font-size: 12px;">
                    {{ model.baseUrl }}
                  </n-text>
                  <n-space size="small">
                    <n-tag v-if="model.agentMode" size="small" type="info">Agent</n-tag>
                    <n-tag v-if="model.toolCalls" size="small" type="success">Tool Calls</n-tag>
                    <n-tag v-if="model.jsonMode" size="small" type="success">JSON Output</n-tag>
                    <n-tag v-if="model.thinkingMode === 'enabled'" size="small" type="warning">
                      思考 {{ model.reasoningEffort || 'high' }}
                    </n-tag>
                  </n-space>
                </n-space>
              </n-card>
            </div>
          </div>

          <!-- 连接测试 -->
          <div v-if="currentModel" class="connection-test">
            <n-divider />
            <n-space vertical>
              <n-text strong>连接测试</n-text>
              <n-button
                :loading="isTesting"
                :disabled="!currentModel"
                @click="testConnection"
              >
                测试当前模型连接
              </n-button>
              <n-text v-if="testResult === 'success'" type="success">
                ✓ 连接成功
              </n-text>
              <n-text v-else-if="testResult === 'failed'" type="error">
                ✗ 连接失败
              </n-text>
            </n-space>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>

    <!-- 模型编辑对话框 -->
    <n-modal
      v-model:show="showModelEditor"
      preset="card"
      :title="editingModel ? '编辑模型' : '添加模型'"
      style="width: 500px;"
    >
      <n-form label-placement="left" label-width="80">
        <!-- 模型预设 -->
        <n-form-item v-if="!editingModel" label="模型预设">
          <n-select
            :value="selectedPreset"
            :options="MODEL_PRESETS"
            placeholder="选择预置模型（可选）"
            clearable
            @update:value="handlePresetSelect"
          />
        </n-form-item>
        <n-form-item label="名称" required>
          <n-input v-model:value="modelForm.name" placeholder="例如：GPT-4" />
        </n-form-item>
        <n-form-item label="Base URL" required>
          <n-input
            v-model:value="modelForm.baseUrl"
            placeholder="例如：https://api.openai.com/v1"
          />
        </n-form-item>
        <n-form-item label="API Key" required>
          <n-input
            v-model:value="modelForm.apiKey"
            type="password"
            show-password-on="click"
            placeholder="输入 API Key"
          />
        </n-form-item>
        <n-form-item label="Model ID" required>
          <n-input
            v-model:value="modelForm.modelId"
            placeholder="例如：gpt-4"
          />
        </n-form-item>
        <n-form-item v-if="modelForm.provider === 'deepseek'" label="Anthropic">
          <n-input
            v-model:value="modelForm.anthropicBaseUrl"
            placeholder="https://api.deepseek.com/anthropic"
          />
        </n-form-item>
        <n-form-item label="思考模式">
          <n-select
            v-model:value="modelForm.thinkingMode"
            :options="thinkingOptions"
          />
        </n-form-item>
        <n-form-item v-if="modelForm.thinkingMode === 'enabled'" label="思考强度">
          <n-select
            v-model:value="modelForm.reasoningEffort"
            :options="reasoningEffortOptions"
          />
        </n-form-item>
        <n-form-item label="能力">
          <n-space vertical>
            <n-checkbox v-model:checked="modelForm.agentMode">Agent 模式</n-checkbox>
            <n-checkbox v-model:checked="modelForm.toolCalls">工具调用</n-checkbox>
            <n-checkbox v-model:checked="modelForm.strictToolCalls">Strict Tool Calls（Beta）</n-checkbox>
            <n-checkbox v-model:checked="modelForm.jsonMode">JSON Output</n-checkbox>
          </n-space>
        </n-form-item>
        <n-form-item label="温度">
          <n-input-number
            v-model:value="modelForm.temperature"
            :min="0"
            :max="2"
            :step="0.1"
            style="width: 100%;"
          />
        </n-form-item>
        <n-form-item label="最大输出">
          <n-input-number
            v-model:value="modelForm.maxTokens"
            :min="256"
            :max="384000"
            :step="256"
            style="width: 100%;"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModelEditor = false">取消</n-button>
          <n-button type="primary" @click="saveModel">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.ai-assistant {
  position: relative;
}

.collapsed-button {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 1000;
  cursor: pointer;
  filter: drop-shadow(0 16px 32px rgba(31, 45, 38, 0.2));
}

.tab-header {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  padding: 5px;
  background: rgba(37, 107, 82, 0.08);
  border: 1px solid rgba(37, 107, 82, 0.1);
  border-radius: 12px;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.quick-menu {
  margin-bottom: 12px;
  padding: 12px;
  background: rgba(245, 248, 241, 0.88);
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 12px;
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.model-selector-select {
  flex: 1 1 176px;
  min-width: 168px;
  max-width: 220px;
}

.model-selector-select :deep(.n-base-selection-label) {
  padding: 0 6px 0 10px;
}

.model-selector-select :deep(.n-base-selection-input),
.model-selector-select :deep(.n-base-selection-placeholder) {
  font-size: 12px;
  font-weight: 680;
}

.drawer-approval {
  margin-bottom: 12px;
  padding: 10px;
  border: 1px solid rgba(37, 107, 82, 0.1);
  border-radius: 8px;
  background: rgba(250, 252, 247, 0.72);
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 12px;
  min-height: 200px;
  max-height: 400px;
  padding-right: 4px;
  scrollbar-width: thin;
  scrollbar-color: rgba(37, 107, 82, 0.35) transparent;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message {
  max-width: 90%;
}

.message.user {
  align-self: flex-end;
}

.message.user .n-card {
  background: rgba(37, 107, 82, 0.12);
  border: 1px solid rgba(37, 107, 82, 0.12);
}

.message.assistant {
  align-self: flex-start;
}

.message.assistant .n-card {
  background: #f5f8f1;
  border: 1px solid rgba(31, 52, 43, 0.1);
}

.generating-content {
  margin-bottom: 12px;
}

.chat-input {
  margin-top: auto;
}

.settings-container {
  height: 100%;
}

.model-list {
  margin-bottom: 16px;
}

.empty-models {
  padding: 20px 0;
}

.model-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-cards .n-card {
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.model-cards .n-card:hover {
  border-color: rgba(37, 107, 82, 0.2);
  box-shadow: var(--admin-shadow-sm);
}

.model-cards .n-card.active {
  border: 1px solid rgba(47, 112, 85, 0.42);
  box-shadow: 0 0 0 3px rgba(47, 112, 85, 0.1);
}

.connection-test {
  margin-top: 16px;
}
</style>
