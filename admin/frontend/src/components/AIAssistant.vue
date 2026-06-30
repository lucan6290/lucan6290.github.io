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
  NPopover,
  NPopconfirm,
  useMessage,
  type SelectOption
} from 'naive-ui'
import { getAPI } from '@/api'
import { useSettingsStore, type AIModelConfig } from '@/stores/settings'
import type { AgentEvent, AIApprovalMode, AIModelPayload, EditorAgentOperation } from '@/types/ai-writing'

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
const approvalMenuOpen = ref(false)
const chatHistory = ref<Array<{ role: 'user' | 'assistant' | 'system'; content: string }>>([])
const isGenerating = ref(false)
const generatedContent = ref('')
const currentOperation = ref<EditorAgentOperation | null>(null)
const editSessionId = ref<string | null>(null)
const currentContentHash = ref<string | null>(null)
const agentEvents = ref<AgentEvent[]>([])
const pendingApproval = ref<{ sessionId: string; approvalId: string; payloadHash: string } | null>(null)
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

const approvalChoices: Array<{ value: AIApprovalMode; label: string; description: string; icon: string }> = [
  {
    value: 'request-approval',
    label: '请求批准',
    description: '编辑外部文件和使用联网时始终询问',
    icon: '☝'
  },
  {
    value: 'delegate-approval',
    label: '替我审批',
    description: '仅对检测到的风险操作请求批准',
    icon: '♧'
  },
  {
    value: 'full-access',
    label: '完全访问权限',
    description: '可不受限制地访问当前文章编辑能力',
    icon: '!'
  }
]

const approvalLabel = computed(() => {
  if (approvalMode.value === 'delegate-approval') return '替我审批'
  if (approvalMode.value === 'full-access') return '完全访问权限'
  return '请求批准'
})

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

  if (!currentModel.value && !props.articlePath) {
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

  if (!currentModel.value && !props.articlePath) {
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

function operationPreview(operation: EditorAgentOperation): string {
  const chunks = [`操作：${operation.type} / ${operation.scope}`, `摘要：${operation.summary}`]
  if (operation.oldText) chunks.push(`原文：\n${operation.oldText}`)
  if (operation.newText) chunks.push(`新内容：\n${operation.newText}`)
  if (operation.frontMatterPatch) chunks.push(`Front Matter：\n${JSON.stringify(operation.frontMatterPatch, null, 2)}`)
  return chunks.join('\n\n')
}

function appendAgentEvents(events: AgentEvent[] | undefined): void {
  if (!events?.length) return
  agentEvents.value.push(...events)
}

async function generateStructuredEdit(userInput: string) {
  const api = getAPI()
  if (!api.runEditorAgent) return
  const model = activeModelPayload()
  if (!model) {
    message.warning('请先配置 AI 模型')
    activeTab.value = 'settings'
    return
  }

  isGenerating.value = true
  generatedContent.value = ''
  currentOperation.value = null
  pendingApproval.value = null
  agentEvents.value = []

  try {
    const planRun = await api.runEditorAgent({
      sessionId: editSessionId.value || undefined,
      articlePath: props.articlePath,
      approvalMode: approvalMode.value,
      command: 'plan_current_article_edit',
      model,
      userInput,
      selection: hasSelection.value ? { text: props.selectedText } : undefined,
      context: { scope: hasSelection.value ? 'selection' : 'document' }
    })
    editSessionId.value = planRun.sessionId
    appendAgentEvents(planRun.events)
    if (planRun.status === 'failed') {
      const result = (planRun.result || {}) as any
      const reason = result.message || result.error?.message || result.validationErrors?.join('；') || 'Agent 编辑方案生成失败'
      throw new Error(reason)
    }
    const result = (planRun.result || {}) as any
    const operation = (result.operation || result.plan?.operation) as EditorAgentOperation | undefined
    if (!operation) {
      throw new Error('Agent 没有返回可执行的编辑操作')
    }
    currentOperation.value = operation
    const preview = result.preview || {}
    currentContentHash.value = preview?.beforeHash || currentContentHash.value || null
    generatedContent.value = preview?.diff || operationPreview(operation)
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
  if (!currentOperation.value || !props.articlePath || !editSessionId.value || !api.runEditorAgent) return

  isGenerating.value = true
  try {
    let response: any
    if (pendingApproval.value && api.resumeAgentApproval) {
      response = await api.resumeAgentApproval(pendingApproval.value.approvalId, {
        ...pendingApproval.value,
        approved: true
      })
      pendingApproval.value = null
    } else {
      response = await api.runEditorAgent({
        sessionId: editSessionId.value,
        articlePath: props.articlePath,
        approvalMode: approvalMode.value,
        confirmed: false,
        command: 'write_current_article',
        operation: currentOperation.value,
        expectedContentHash: currentContentHash.value || undefined
      })
    }
    appendAgentEvents(response?.events)
    if (response?.status === 'waiting_approval') {
      const approval = (response.result as any)?.approval
      if (approval) {
        pendingApproval.value = {
          sessionId: approval.sessionId,
          approvalId: approval.approvalId,
          payloadHash: approval.payloadHash
        }
        message.warning('当前修改需要确认，再次点击采纳将继续写入')
        return
      }
    }
    if (response?.status === 'failed') {
      throw new Error((response.result as any)?.message || 'Agent 写入失败')
    }
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

function handleApprovalSelect(value: AIApprovalMode) {
  approvalMode.value = value
  approvalMenuOpen.value = false
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

              <div v-if="agentEvents.length" class="agent-events">
                <div
                  v-for="(event, index) in agentEvents.slice(-8)"
                  :key="`${event.type}-${index}`"
                  class="agent-event"
                  :class="`event-${event.type}`"
                >
                  <span class="agent-event-type">{{ event.type }}</span>
                  <span>{{ event.message }}</span>
                </div>
              </div>

              <n-text v-if="pendingApproval" type="warning" class="approval-pending">
                当前修改等待确认，再次点击采纳将继续写入。
              </n-text>

              <!-- 采纳/放弃按钮 -->
              <template v-if="canAdopt && !isGenerating" #footer>
                <n-space justify="end">
                  <n-button size="small" @click="discardContent">放弃</n-button>
                  <n-button type="primary" size="small" @click="adoptContent">
                    {{ pendingApproval ? '确认写入' : '采纳' }}
                  </n-button>
                </n-space>
              </template>
            </n-card>
          </div>

          <!-- 输入区 -->
          <div class="chat-input">
            <div class="composer-shell">
              <n-input
                v-model:value="chatInput"
                type="textarea"
                placeholder="输入问题或指令..."
                :autosize="{ minRows: 4, maxRows: 8 }"
                :disabled="isGenerating"
                class="composer-input"
                @keydown.enter.ctrl.prevent="sendMessage()"
              />
              <div class="composer-toolbar">
                <div class="composer-left">
                  <n-popover
                    v-model:show="approvalMenuOpen"
                    trigger="click"
                    placement="top-start"
                    :show-arrow="false"
                    :disabled="isGenerating"
                    style="padding: 0;"
                  >
                    <template #trigger>
                      <button class="approval-trigger" type="button" :disabled="isGenerating">
                        <span class="approval-dot"></span>
                        <span>{{ approvalLabel }}</span>
                        <span class="approval-caret">⌄</span>
                      </button>
                    </template>
                    <div class="approval-menu">
                      <div class="approval-menu-header">
                        <span>应如何批准 AI 操作？</span>
                        <button class="approval-help" type="button">了解更多</button>
                      </div>
                      <button
                        v-for="choice in approvalChoices"
                        :key="choice.value"
                        class="approval-menu-item"
                        :class="{ selected: approvalMode === choice.value }"
                        type="button"
                        @click="handleApprovalSelect(choice.value)"
                      >
                        <span class="approval-menu-icon">{{ choice.icon }}</span>
                        <span class="approval-menu-copy">
                          <strong>{{ choice.label }}</strong>
                          <small>{{ choice.description }}</small>
                        </span>
                        <span v-if="approvalMode === choice.value" class="approval-check">✓</span>
                      </button>
                    </div>
                  </n-popover>
                </div>
                <div class="composer-right">
                  <n-select
                    v-if="modelOptions.length > 0"
                    :value="currentModel?.id"
                    :options="modelOptions"
                    size="small"
                    class="composer-model-select"
                    :consistent-menu-width="false"
                    @update:value="handleModelChange"
                  />
                  <span v-else class="composer-model-empty">未配置模型</span>
                  <button
                    v-if="isGenerating"
                    class="send-button stop-button"
                    type="button"
                    title="停止生成"
                    @click="stopGeneration"
                  >
                    ■
                  </button>
                  <button
                    v-else
                    class="send-button"
                    type="button"
                    title="发送"
                    :disabled="!chatInput.trim()"
                    @click="sendMessage()"
                  >
                    ↑
                  </button>
                </div>
              </div>
            </div>
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
  --assistant-ink: #202823;
  --assistant-muted: #7a837d;
  --assistant-line: rgba(30, 42, 35, 0.12);
  --assistant-primary: #2f704f;
  --assistant-primary-soft: rgba(47, 112, 79, 0.1);
  --assistant-surface: #ffffff;
  --assistant-wash: #f7f8f5;
}

.ai-assistant :deep(.n-drawer-content) {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 249, 246, 0.98));
}

.ai-assistant :deep(.n-drawer-header) {
  padding: 22px 24px 18px;
  border-bottom: 1px solid var(--assistant-line);
}

.ai-assistant :deep(.n-drawer-header__main) {
  color: var(--assistant-ink);
  font-size: 22px;
  font-weight: 760;
  letter-spacing: 0;
}

.ai-assistant :deep(.n-drawer-body-content-wrapper) {
  padding: 18px 24px 24px;
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
  margin-bottom: 14px;
  padding: 5px;
  background: rgba(235, 240, 234, 0.72);
  border: 1px solid rgba(37, 107, 82, 0.08);
  border-radius: 999px;
}

.tab-header :deep(.n-button) {
  flex: 1;
  --n-border-radius: 999px !important;
  font-weight: 720;
}

.chat-container {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 120px);
}

.quick-menu {
  margin-bottom: 12px;
  padding: 12px;
  background: rgba(245, 248, 241, 0.88);
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 12px;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 16px;
  min-height: 200px;
  max-height: none;
  padding-right: 4px;
  scrollbar-width: thin;
  scrollbar-color: rgba(37, 107, 82, 0.35) transparent;
}

.chat-history :deep(.n-empty) {
  margin-top: 56px;
  color: #a5aaa6;
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
  margin-bottom: 16px;
}

.agent-events {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(31, 52, 43, 0.1);
}

.agent-event {
  display: grid;
  grid-template-columns: 104px 1fr;
  gap: 8px;
  align-items: start;
  color: #4d5952;
  font-size: 12px;
  line-height: 1.45;
}

.agent-event-type {
  overflow: hidden;
  color: #2f704f;
  font-family: "Cascadia Mono", "Consolas", monospace;
  font-weight: 760;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-approval_required .agent-event-type,
.approval-pending {
  color: #a45e24;
}

.chat-input {
  margin-top: auto;
}

.composer-shell {
  padding: 12px;
  border: 1px solid rgba(31, 42, 35, 0.12);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow:
    0 16px 42px rgba(28, 39, 33, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.composer-shell:focus-within {
  border-color: rgba(47, 112, 79, 0.28);
  box-shadow:
    0 18px 48px rgba(28, 39, 33, 0.14),
    0 0 0 3px rgba(47, 112, 79, 0.08);
}

.composer-input :deep(.n-input) {
  background: transparent;
}

.composer-input :deep(.n-input-wrapper) {
  padding: 0;
}

.composer-input :deep(.n-input__border),
.composer-input :deep(.n-input__state-border) {
  display: none;
}

.composer-input :deep(.n-input__textarea-el),
.composer-input :deep(.n-input__placeholder) {
  color: #252d28;
  font-size: 14px;
  line-height: 1.65;
}

.composer-input :deep(.n-input__placeholder) {
  color: #adb3ae;
}

.composer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 10px;
}

.composer-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.composer-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 7px;
  flex: 0 0 auto;
  min-width: 0;
}

.composer-model-select {
  flex: 0 1 126px;
  width: min(126px, 32vw);
  min-width: 96px;
}

.composer-model-select :deep(.n-base-selection) {
  --n-height: 28px !important;
  --n-border: 1px solid transparent !important;
  --n-border-hover: 1px solid rgba(47, 112, 79, 0.14) !important;
  --n-border-active: 1px solid rgba(47, 112, 79, 0.22) !important;
  --n-border-focus: 1px solid rgba(47, 112, 79, 0.22) !important;
  --n-box-shadow-active: none !important;
  --n-box-shadow-focus: none !important;
  border-radius: 999px !important;
  background: rgba(244, 246, 242, 0.9);
}

.composer-model-select :deep(.n-base-selection-label) {
  padding: 0 3px 0 9px;
  background: transparent;
}

.composer-model-select :deep(.n-base-selection-input),
.composer-model-select :deep(.n-base-selection-placeholder) {
  color: #4e5851;
  font-size: 11px;
  font-weight: 650;
}

.composer-model-empty {
  color: #969f99;
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
}

.approval-menu {
  width: 360px;
  padding: 10px;
  border: 1px solid rgba(27, 36, 31, 0.1);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow:
    0 18px 42px rgba(24, 31, 27, 0.15),
    0 2px 8px rgba(24, 31, 27, 0.06);
}

.approval-menu-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 6px 8px;
  color: #9a9f9b;
  font-size: 12px;
  font-weight: 600;
}

.approval-help {
  border: 0;
  padding: 0;
  color: #7b807c;
  background: transparent;
  font-size: 12px;
  text-decoration: underline;
  cursor: pointer;
}

.approval-menu-item {
  display: grid;
  grid-template-columns: 22px 1fr 18px;
  gap: 10px;
  width: 100%;
  padding: 10px 8px;
  border: 0;
  border-radius: 10px;
  color: #242b27;
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background-color 0.16s ease, color 0.16s ease;
}

.approval-menu-item:hover {
  background: rgba(28, 38, 33, 0.055);
}

.approval-menu-item.selected {
  background: rgba(37, 107, 82, 0.06);
}

.approval-menu-icon {
  display: inline-flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 2px;
  color: #4e5952;
  font-size: 14px;
  line-height: 1;
}

.approval-menu-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.approval-menu-copy strong {
  color: #202723;
  font-size: 13px;
  font-weight: 720;
  line-height: 1.25;
}

.approval-menu-copy small {
  overflow: hidden;
  color: #858b87;
  font-size: 12px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.approval-check {
  align-self: center;
  justify-self: center;
  color: #2f704f;
  font-size: 14px;
  font-weight: 820;
}

.approval-trigger {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 28px;
  max-width: 118px;
  padding: 0 9px;
  border: 1px solid transparent;
  border-radius: 999px;
  color: #1970d6;
  background: rgba(25, 118, 210, 0.07);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: color 0.18s ease, background-color 0.18s ease, border-color 0.18s ease;
}

.approval-trigger:hover:not(:disabled) {
  border-color: rgba(25, 118, 210, 0.18);
  background: rgba(25, 118, 210, 0.11);
}

.approval-trigger:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.approval-trigger span:nth-child(2) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.approval-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
}

.approval-caret {
  color: currentColor;
  font-size: 11px;
  line-height: 1;
}

.send-button {
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 50%;
  color: #ffffff;
  background: linear-gradient(145deg, #9cb7aa, #6f9787);
  font-size: 19px;
  font-weight: 860;
  line-height: 1;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(61, 92, 78, 0.2);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease, opacity 0.18s ease;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: saturate(1.08);
  box-shadow: 0 14px 28px rgba(61, 92, 78, 0.26);
}

.send-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
  box-shadow: none;
}

.stop-button {
  background: linear-gradient(145deg, #c76757, #9d3f36);
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
