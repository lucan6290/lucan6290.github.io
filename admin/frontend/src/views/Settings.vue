<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NCard,
  NTabPane,
  NSpace,
  NTag,
  NH2,
  NP,
  NSelect,
  NInput,
  NInputNumber,
  NCheckbox,
  NButton,
  NDivider,
  NForm,
  NFormItem,
  NModal,
  NPopconfirm,
  NSwitch,
  useMessage,
  useDialog,
  type SelectOption
} from 'naive-ui'
import { useSettingsStore, type AIModelConfig } from '@/stores/settings'
import { useCategoriesStore } from '@/stores/categories'

const message = useMessage()
const dialog = useDialog()
const settingsStore = useSettingsStore()
const categoriesStore = useCategoriesStore()

// ==================== AI 模型配置 ====================
const isTesting = ref(false)
const testResult = ref<'success' | 'failed' | null>(null)
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

const selectedPreset = ref<string | null>(null)

// 模型选择选项
const modelOptions = computed<SelectOption[]>(() => {
  return settingsStore.aiModels.map(model => ({
    label: model.name,
    value: model.id
  }))
})

// 当前激活的模型
const currentModel = computed(() => settingsStore.activeModel)

// 打开添加模型对话框
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

// 打开编辑模型对话框
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
    selectedPreset.value = value
  }
}

// 保存模型
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

// 删除模型
function handleDeleteModel(id: string) {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除此模型配置吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      settingsStore.removeModel(id)
      message.success('模型已删除')
    }
  })
}

// 切换激活模型
function handleModelChange(id: string) {
  settingsStore.setActiveModel(id)
  message.success(`已切换到 ${settingsStore.getModel(id)?.name}`)
}

// 测试连接
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

// 清空所有模型
function handleClearModels() {
  dialog.warning({
    title: '确认清空',
    content: '确定要清空所有模型配置吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      settingsStore.clearModels()
      message.success('已清空所有模型配置')
    }
  })
}

// ==================== 分类管理 ====================
const newPrimaryName = ref('')
const newPrimarySlug = ref('')
const newPrimaryPrefix = ref('')
const newPrimaryCover = ref('')
const newPrimaryOrder = ref('10')
const newPrimaryEnabled = ref(true)
const newCategoryName = ref('')
const newCategoryPrefix = ref('')
const newCategoryOrder = ref('10')
const newCategoryEnabled = ref(true)
const selectedParentCategory = ref<string | null>(null)
const showPrimaryCategoryEditor = ref(false)
const showCategoryEditor = ref(false)
const categoryStatusOptions = [
  { label: '启用', value: 'enabled' },
  { label: '停用', value: 'disabled' }
]

// 添加一级分类
const handleAddPrimaryCategory = async () => {
  if (!newPrimaryName.value.trim()) {
    message.error('请输入一级分类显示名')
    return
  }

  if (!newPrimarySlug.value.trim()) {
    message.error('请输入一级分类目录')
    return
  }

  if (!newPrimaryPrefix.value.trim()) {
    message.error('请输入一级分类文件名前缀')
    return
  }

  const success = await categoriesStore.addPrimaryCategory({
    frontend_name1: newPrimaryName.value.trim(),
    category_slug: newPrimarySlug.value.trim(),
    note_prefix1: newPrimaryPrefix.value.trim(),
    cover: newPrimaryCover.value.trim(),
    sort_order: Number(newPrimaryOrder.value) || 10,
    enabled: newPrimaryEnabled.value,
    children: []
  })

  if (success) {
    message.success('一级分类添加成功')
    newPrimaryName.value = ''
    newPrimarySlug.value = ''
    newPrimaryPrefix.value = ''
    newPrimaryCover.value = ''
    newPrimaryOrder.value = '10'
    newPrimaryEnabled.value = true
    showPrimaryCategoryEditor.value = false
  } else {
    message.error('一级分类显示名、目录或文件名前缀已存在')
  }
}

const openPrimaryCategoryEditor = () => {
  showPrimaryCategoryEditor.value = true
}

// 添加自定义分类
const handleAddCategory = async () => {
  if (!newCategoryName.value.trim()) {
    message.error('请输入二级分类显示名')
    return
  }

  if (!newCategoryPrefix.value.trim()) {
    message.error('请输入二级分类文件名前缀')
    return
  }

  if (!selectedParentCategory.value) {
    message.error('请选择所属一级分类')
    return
  }

  const success = await categoriesStore.addSecondaryCategory(
    selectedParentCategory.value,
    {
      frontend_name2: newCategoryName.value.trim(),
      note_prefix2: newCategoryPrefix.value.trim(),
      sort_order: Number(newCategoryOrder.value) || 10,
      enabled: newCategoryEnabled.value
    }
  )

  if (success) {
    message.success('分类添加成功')
    newCategoryName.value = ''
    newCategoryPrefix.value = ''
    newCategoryOrder.value = '10'
    newCategoryEnabled.value = true
    showCategoryEditor.value = false
  } else {
    message.error('分类前缀已存在或所属一级分类无效')
  }
}

const openCategoryEditor = () => {
  showCategoryEditor.value = true
}

// 删除自定义分类
const handleDeleteCategory = (parentPrefix: string, childPrefix: string, name: string) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除分类"${name}"吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await categoriesStore.removeSecondaryCategory(parentPrefix, childPrefix)
      message.success('分类已删除')
    }
  })
}

const handleCategoryStatusChange = async (
  parentPrefix: string,
  childPrefix: string,
  value: string
) => {
  const enabled = value === 'enabled'
  try {
    const success = await categoriesStore.updateSecondaryCategoryEnabled(parentPrefix, childPrefix, enabled)
    if (success) {
      message.success(`已${enabled ? '启用' : '停用'}该二级分类`)
    } else {
      message.error('未找到对应分类')
    }
  } catch (error: any) {
    message.error(`状态更新失败: ${error.message || '未知错误'}`)
  }
}

const handlePrimarySortOrderChange = async (
  primaryPrefix: string,
  value: number | null
) => {
  if (value === null || !Number.isFinite(value)) {
    message.error('排序必须是数字')
    return
  }

  try {
    const updateSortOrder = (categoriesStore as any).updatePrimaryCategorySortOrder
    let success = false

    if (typeof updateSortOrder === 'function') {
      success = await updateSortOrder(primaryPrefix, value)
    } else {
      const nextRegistry = categoriesStore.registry.map((category) => ({
        ...category,
        children: category.children.map((child) => ({ ...child }))
      }))
      const primary = nextRegistry.find((category) => category.note_prefix1 === primaryPrefix)

      if (primary) {
        primary.sort_order = value
        await categoriesStore.saveRegistry(nextRegistry)
        success = true
      }
    }

    if (success) {
      message.success('排序已更新')
    } else {
      message.error('未找到对应分类')
    }
  } catch (error: any) {
    message.error(`排序更新失败: ${error.message || '未知错误'}`)
  }
}

const handleCategorySortOrderChange = async (
  parentPrefix: string,
  childPrefix: string,
  value: number | null
) => {
  if (value === null || !Number.isFinite(value)) {
    message.error('排序必须是数字')
    return
  }

  try {
    const updateSortOrder = (categoriesStore as any).updateSecondaryCategorySortOrder
    let success = false

    if (typeof updateSortOrder === 'function') {
      success = await updateSortOrder(parentPrefix, childPrefix, value)
    } else {
      const nextRegistry = categoriesStore.registry.map((category) => ({
        ...category,
        children: category.children.map((child) => ({ ...child }))
      }))
      const child = nextRegistry
        .find((category) => category.note_prefix1 === parentPrefix)
        ?.children.find((item) => item.note_prefix2 === childPrefix)

      if (child) {
        child.sort_order = value
        await categoriesStore.saveRegistry(nextRegistry)
        success = true
      }
    }

    if (success) {
      message.success('排序已更新')
    } else {
      message.error('未找到对应分类')
    }
  } catch (error: any) {
    message.error(`排序更新失败: ${error.message || '未知错误'}`)
  }
}

onMounted(() => {
  categoriesStore.fetchRegistry()
})

</script>

<template>
  <div class="settings page-shell">
    <div class="settings-header glass-panel">
      <p class="page-kicker">Preferences</p>
      <n-h2 class="page-title">设置</n-h2>
      <p class="page-subtitle">管理 AI 模型和分类体系。</p>
    </div>

    <n-tabs type="line" animated>
      <!-- AI 配置 -->
      <n-tab-pane name="ai" tab="AI 配置">
        <n-space vertical :size="24">
          <n-card title="AI 模型配置" class="setting-card">
            <n-space vertical :size="16">
              <!-- 模型列表 -->
              <n-space justify="space-between" align="center">
                <n-p strong>已配置模型</n-p>
                <n-space>
                  <n-button size="small" @click="openAddModel">添加模型</n-button>
                  <n-popconfirm
                    v-if="settingsStore.aiModels.length > 0"
                    @positive-click="handleClearModels"
                  >
                    <template #trigger>
                      <n-button size="small" type="error" ghost>清空所有</n-button>
                    </template>
                    确定要清空所有模型配置吗？
                  </n-popconfirm>
                </n-space>
              </n-space>

              <n-divider />

              <!-- 空状态 -->
              <div v-if="settingsStore.aiModels.length === 0" class="empty-models">
                <n-p depth="3">暂无模型配置，请点击"添加模型"按钮添加</n-p>
              </div>

              <!-- 模型卡片列表 -->
              <div v-else class="model-cards">
                <n-card
                  v-for="model in settingsStore.aiModels"
                  :key="model.id"
                  size="small"
                  :class="{ active: model.id === settingsStore.activeModelId }"
                  class="model-card"
                >
                  <n-space vertical size="small">
                    <n-space justify="space-between" align="center">
                      <n-p strong>{{ model.name }}</n-p>
                      <n-space size="small">
                        <n-button size="tiny" @click="openEditModel(model)">编辑</n-button>
                        <n-popconfirm @positive-click="handleDeleteModel(model.id)">
                          <template #trigger>
                            <n-button size="tiny" type="error">删除</n-button>
                          </template>
                          确定删除此模型吗？
                        </n-popconfirm>
                      </n-space>
                    </n-space>
                    <n-p depth="3" style="font-size: 12px;">
                      Model ID: {{ model.modelId }}
                    </n-p>
                    <n-p depth="3" style="font-size: 12px;">
                      Base URL: {{ model.baseUrl }}
                    </n-p>
                    <n-space size="small">
                      <n-tag v-if="model.agentMode" size="small" type="info">Agent</n-tag>
                      <n-tag v-if="model.toolCalls" size="small" type="success">Tool Calls</n-tag>
                      <n-tag v-if="model.jsonMode" size="small" type="success">JSON Output</n-tag>
                      <n-tag v-if="model.thinkingMode === 'enabled'" size="small" type="warning">
                        思考 {{ model.reasoningEffort || 'high' }}
                      </n-tag>
                    </n-space>
                    <n-space>
                      <n-tag
                        v-if="model.id === settingsStore.activeModelId"
                        type="success"
                        size="small"
                      >
                        当前激活
                      </n-tag>
                      <n-button
                        v-else
                        size="tiny"
                        type="primary"
                        ghost
                        @click="handleModelChange(model.id)"
                      >
                        激活
                      </n-button>
                    </n-space>
                  </n-space>
                </n-card>
              </div>

              <!-- 连接测试 -->
              <div v-if="currentModel" class="connection-test">
                <n-divider />
                <n-space vertical>
                  <n-p strong>连接测试</n-p>
                  <n-button
                    :loading="isTesting"
                    :disabled="!currentModel"
                    @click="testConnection"
                  >
                    测试当前模型连接
                  </n-button>
                  <n-p v-if="testResult === 'success'" type="success">
                    ✓ 连接成功
                  </n-p>
                  <n-p v-else-if="testResult === 'failed'" type="error">
                    ✗ 连接失败
                  </n-p>
                </n-space>
              </div>
            </n-space>
          </n-card>
        </n-space>
      </n-tab-pane>

      <!-- 分类管理 -->
      <n-tab-pane name="categories" tab="分类管理">
        <n-space vertical :size="24">
          <!-- 一级分类映射 -->
          <n-card title="一级分类映射" class="setting-card">
            <template #header-extra>
              <n-button
                class="category-add-trigger"
                circle
                size="small"
                type="primary"
                title="新增一级分类"
                aria-label="新增一级分类"
                @click="openPrimaryCategoryEditor"
              >
                +
              </n-button>
            </template>

            <div class="category-primary-table">
              <div class="category-primary-head">
                <span>Front Matter 一级分类</span>
                <span>目录</span>
                <span>一级前缀</span>
                <span>排序</span>
                <span>状态</span>
              </div>

              <div
                v-for="category in categoriesStore.registry"
                :key="category.note_prefix1"
                class="category-primary-row"
                :class="{ disabled: !category.enabled }"
              >
                <span class="category-primary-name">{{ category.frontend_name1 }}</span>
                <span class="category-primary-code">{{ category.category_slug }}</span>
                <span class="category-primary-code">{{ category.note_prefix1 }}</span>
                <n-input-number
                  class="category-primary-order-input"
                  size="tiny"
                  :value="category.sort_order"
                  :min="0"
                  :step="10"
                  :show-button="false"
                  @update:value="(value) => handlePrimarySortOrderChange(category.note_prefix1, value)"
                />
                <span
                  class="category-primary-status"
                  :class="{ disabled: !category.enabled }"
                >
                  {{ category.enabled ? '启用' : '停用' }}
                </span>
              </div>
            </div>
          </n-card>

          <!-- 自定义分类列表 -->
          <n-card
            v-if="categoriesStore.registry.length > 0"
            title="二级分类映射"
            class="setting-card"
          >
            <template #header-extra>
              <n-button
                class="category-add-trigger"
                circle
                size="small"
                type="primary"
                title="新增二级分类"
                aria-label="新增二级分类"
                @click="openCategoryEditor"
              >
                +
              </n-button>
            </template>

            <div class="category-registry-list">
              <div
                v-for="category in categoriesStore.registry"
                :key="category.note_prefix1"
                class="category-registry-group"
              >
                <div class="category-registry-title">
                  <div>
                    <span class="category-registry-name">{{ category.frontend_name1 }}</span>
                    <span class="category-registry-subtitle">一级分类映射</span>
                  </div>
                  <div class="category-registry-primary-map">
                    <span>Front Matter: {{ category.frontend_name1 }}</span>
                    <span>文件名: {{ category.note_prefix1 }}</span>
                  </div>
                </div>

                <div class="category-mapping-table">
                  <div class="category-mapping-head">
                    <span>Front Matter 二级分类</span>
                    <span>文件名前缀</span>
                    <span>排序</span>
                    <span>状态</span>
                    <span>操作</span>
                  </div>

                  <div
                    v-for="child in category.children"
                    :key="child.note_prefix2"
                    class="category-mapping-row"
                    :class="{ disabled: !child.enabled }"
                  >
                    <span class="category-mapping-name">{{ child.frontend_name2 }}</span>
                    <span class="category-mapping-prefix">{{ child.note_prefix2 }}</span>
                    <n-input-number
                      class="category-mapping-order-input"
                      size="tiny"
                      :value="child.sort_order"
                      :min="0"
                      :step="10"
                      :show-button="false"
                      @update:value="(value) => handleCategorySortOrderChange(category.note_prefix1, child.note_prefix2, value)"
                    />
                    <n-select
                      class="category-mapping-status-select"
                      :class="{ enabled: child.enabled, disabled: !child.enabled }"
                      size="tiny"
                      :value="child.enabled ? 'enabled' : 'disabled'"
                      :options="categoryStatusOptions"
                      @update:value="(value) => handleCategoryStatusChange(category.note_prefix1, child.note_prefix2, value)"
                    />
                    <n-button
                      size="tiny"
                      type="error"
                      quaternary
                      @click="handleDeleteCategory(category.note_prefix1, child.note_prefix2, child.frontend_name2)"
                    >
                      删除
                    </n-button>
                  </div>

                  <div v-if="category.children.length === 0" class="category-mapping-empty">
                    暂无二级分类
                  </div>
                </div>
              </div>
            </div>
          </n-card>
        </n-space>
      </n-tab-pane>
    </n-tabs>

    <!-- 一级分类新增弹窗 -->
    <n-modal
      v-model:show="showPrimaryCategoryEditor"
      preset="card"
      title="新增一级分类"
      style="width: min(520px, calc(100vw - 32px));"
    >
      <n-form label-placement="left" label-width="120">
        <n-form-item label="前端显示名">
          <n-input
            v-model:value="newPrimaryName"
            placeholder="例如：后端工程"
            @keyup.enter="handleAddPrimaryCategory"
          />
        </n-form-item>
        <n-form-item label="目录">
          <n-input
            v-model:value="newPrimarySlug"
            placeholder="例如：backend-engineering"
            @keyup.enter="handleAddPrimaryCategory"
          />
        </n-form-item>
        <n-form-item label="文件名前缀">
          <n-input
            v-model:value="newPrimaryPrefix"
            placeholder="例如：be"
            @keyup.enter="handleAddPrimaryCategory"
          />
        </n-form-item>
        <n-form-item label="封面">
          <n-input
            v-model:value="newPrimaryCover"
            placeholder="例如：/img/covers/backend-engineering.svg"
          />
        </n-form-item>
        <n-form-item label="排序">
          <n-input
            v-model:value="newPrimaryOrder"
            placeholder="数字越小越靠前"
          />
        </n-form-item>
        <n-form-item label="启用">
          <n-switch v-model:value="newPrimaryEnabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showPrimaryCategoryEditor = false">取消</n-button>
          <n-button
            type="primary"
            :disabled="!newPrimaryName || !newPrimarySlug || !newPrimaryPrefix"
            @click="handleAddPrimaryCategory"
          >
            保存
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 二级分类新增弹窗 -->
    <n-modal
      v-model:show="showCategoryEditor"
      preset="card"
      title="新增二级分类"
      style="width: min(520px, calc(100vw - 32px));"
    >
      <n-form label-placement="left" label-width="120">
        <n-form-item label="所属一级分类">
          <n-select
            v-model:value="selectedParentCategory"
            :options="categoriesStore.primaryCategories"
            placeholder="请选择一级分类"
          />
        </n-form-item>
        <n-form-item label="前端显示名">
          <n-input
            v-model:value="newCategoryName"
            placeholder="例如：AI 探索"
            @keyup.enter="handleAddCategory"
          />
        </n-form-item>
        <n-form-item label="文件名前缀">
          <n-input
            v-model:value="newCategoryPrefix"
            placeholder="例如：ai"
            @keyup.enter="handleAddCategory"
          />
        </n-form-item>
        <n-form-item label="排序">
          <n-input
            v-model:value="newCategoryOrder"
            placeholder="数字越小越靠前"
          />
        </n-form-item>
        <n-form-item label="启用">
          <n-switch v-model:value="newCategoryEnabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCategoryEditor = false">取消</n-button>
          <n-button
            type="primary"
            :disabled="!newCategoryName || !newCategoryPrefix || !selectedParentCategory"
            @click="handleAddCategory"
          >
            保存
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 模型编辑对话框 -->
    <n-modal
      v-model:show="showModelEditor"
      preset="card"
      :title="editingModel ? '编辑模型' : '添加模型'"
      style="width: 500px;"
    >
      <n-form label-placement="left" label-width="80">
        <!-- 模型预设（仅添加模式显示） -->
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
.settings {
  max-width: 1200px;
}

.settings-header {
  margin-bottom: 20px;
  padding: 24px 26px;
  background:
    linear-gradient(110deg, rgba(37, 107, 82, 0.1), transparent 52%),
    var(--admin-surface);
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 850;
}

.setting-card {
  margin-bottom: 16px;
  overflow: hidden;
}

.empty-models {
  padding: 20px 0;
  text-align: center;
}

.model-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.model-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.model-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--admin-shadow-md);
}

.model-card.active {
  border: 1px solid rgba(47, 112, 85, 0.42);
  box-shadow: 0 0 0 3px rgba(47, 112, 85, 0.1);
}

.connection-test {
  margin-top: 16px;
}

.category-primary-table {
  overflow: hidden;
  border: 1px solid rgba(41, 63, 52, 0.09);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.7);
}

.category-primary-head,
.category-primary-row {
  display: grid;
  grid-template-columns: minmax(150px, 1.3fr) minmax(130px, 1fr) 92px 72px 72px;
  align-items: center;
  gap: 10px;
}

.category-primary-head {
  padding: 9px 12px;
  border-bottom: 1px solid rgba(41, 63, 52, 0.08);
  color: var(--admin-muted);
  background: rgba(244, 247, 241, 0.84);
  font-size: 12px;
  font-weight: 400;
}

.category-primary-row {
  min-height: 40px;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(41, 63, 52, 0.07);
}

.category-primary-row:last-child {
  border-bottom: none;
}

.category-primary-row.disabled {
  background: rgba(169, 102, 43, 0.05);
}

.category-primary-name {
  color: #26342e;
  font-size: 13px;
  font-weight: 400;
}

.category-primary-code {
  color: var(--admin-muted);
  font-family: "Cascadia Code", "JetBrains Mono", Consolas, monospace;
  font-size: 12px;
  font-weight: 400;
}

.category-primary-order-input {
  width: 64px;
}

.category-primary-order-input :deep(.n-input__input-el) {
  font-size: 12px;
  text-align: center;
}

.category-primary-status {
  width: max-content;
  padding: 2px 7px;
  border-radius: 999px;
  color: var(--admin-brand);
  background: rgba(37, 107, 82, 0.08);
  font-size: 12px;
  font-weight: 400;
}

.category-primary-status.disabled {
  color: #b85155;
  background: rgba(184, 81, 85, 0.1);
}

.category-slug {
  color: var(--admin-muted);
  font-size: 12px;
  font-family: "Cascadia Code", "JetBrains Mono", Consolas, monospace;
}

.category-add-trigger {
  font-size: 18px;
  font-weight: 400;
  line-height: 1;
}

.category-registry-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-registry-group {
  padding: 14px;
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 8px;
  background: rgba(247, 250, 245, 0.66);
}

.category-registry-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 12px;
}

.category-registry-name {
  display: block;
  color: #26342e;
  font-size: 15px;
  font-weight: 400;
}

.category-registry-subtitle {
  display: block;
  margin-top: 2px;
  color: var(--admin-muted);
  font-size: 12px;
  font-weight: 400;
}

.category-registry-primary-map {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}

.category-registry-primary-map span {
  padding: 3px 8px;
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 999px;
  color: var(--admin-muted);
  background: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  font-weight: 400;
}

.category-mapping-table {
  overflow: hidden;
  border: 1px solid rgba(41, 63, 52, 0.09);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.7);
}

.category-mapping-head,
.category-mapping-row {
  display: grid;
  grid-template-columns: minmax(160px, 1.4fr) minmax(92px, 0.72fr) 58px 92px 60px;
  align-items: center;
  gap: 10px;
}

.category-mapping-head {
  padding: 9px 12px;
  border-bottom: 1px solid rgba(41, 63, 52, 0.08);
  color: var(--admin-muted);
  background: rgba(244, 247, 241, 0.84);
  font-size: 12px;
  font-weight: 400;
}

.category-mapping-head span:nth-child(3) {
  margin-left: -8px;
}

.category-mapping-row {
  min-height: 40px;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(41, 63, 52, 0.07);
}

.category-mapping-row:last-child {
  border-bottom: none;
}

.category-mapping-row.disabled {
  background: rgba(169, 102, 43, 0.05);
}

.category-mapping-name {
  color: #26342e;
  font-size: 13px;
  font-weight: 400;
}

.category-mapping-prefix {
  color: var(--admin-muted);
  font-family: "Cascadia Code", "JetBrains Mono", Consolas, monospace;
  font-size: 12px;
  font-weight: 400;
}

.category-mapping-order-input {
  width: 58px;
  justify-self: start;
  margin-left: -8px;
}

.category-mapping-order-input :deep(.n-input__input-el) {
  font-size: 12px;
  text-align: center;
}

.category-mapping-status-select {
  width: 92px;
}

.category-mapping-status-select :deep(.n-base-selection) {
  --n-height: 26px;
  border-radius: 999px;
  font-weight: 400;
}

.category-mapping-status-select.enabled :deep(.n-base-selection) {
  background: rgba(37, 107, 82, 0.08);
}

.category-mapping-status-select.enabled :deep(.n-base-selection-label),
.category-mapping-status-select.enabled :deep(.n-base-selection-input__content),
.category-mapping-status-select.enabled :deep(.n-base-suffix) {
  color: var(--admin-brand);
}

.category-mapping-status-select.disabled :deep(.n-base-selection) {
  background: rgba(184, 81, 85, 0.1);
}

.category-mapping-status-select.disabled :deep(.n-base-selection-label),
.category-mapping-status-select.disabled :deep(.n-base-selection-input__content),
.category-mapping-status-select.disabled :deep(.n-base-suffix) {
  color: #b85155;
}

.category-mapping-empty {
  padding: 14px 12px;
  color: var(--admin-muted);
  font-size: 13px;
  text-align: center;
}

.settings :deep(.n-tabs-nav) {
  margin-bottom: 18px;
  padding: 0 4px;
}

.settings :deep(.n-tabs-tab) {
  font-weight: 500;
}

.settings :deep(.n-form-item-label),
.settings :deep(.n-base-selection-label),
.settings :deep(.n-input__input-el),
.settings :deep(.n-tag) {
  font-weight: 400;
}

@media (max-width: 768px) {
  .category-primary-head {
    display: none;
  }

  .category-primary-row {
    grid-template-columns: 1fr auto;
    gap: 8px;
  }

  .category-primary-name {
    grid-column: 1 / -1;
  }

  .category-registry-title {
    flex-direction: column;
    gap: 8px;
  }

  .category-registry-primary-map {
    justify-content: flex-start;
  }

  .category-mapping-head {
    display: none;
  }

  .category-mapping-row {
    grid-template-columns: 1fr auto;
    gap: 8px;
  }

  .category-mapping-name {
    grid-column: 1 / -1;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings {
    padding: 18px;
  }
}
</style>
