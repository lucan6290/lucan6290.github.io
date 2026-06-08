<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NCard,
  NCollapse,
  NCollapseItem,
  NTabPane,
  NSpace,
  NRadioGroup,
  NRadioButton,
  NTag,
  NH2,
  NH3,
  NP,
  NSelect,
  NInput,
  NInputNumber,
  NButton,
  NDivider,
  NAlert,
  NIcon,
  NSpin,
  NTree,
  NForm,
  NFormItem,
  NPopconfirm,
  useMessage,
  useDialog,
  type SelectOption,
  type TreeOption
} from 'naive-ui'
import { useModeStore } from '@/stores/mode'
import { useSettingsStore, type AIModelConfig } from '@/stores/settings'
import { useCategoriesStore } from '@/stores/categories'

const message = useMessage()
const dialog = useDialog()
const modeStore = useModeStore()
const settingsStore = useSettingsStore()
const categoriesStore = useCategoriesStore()

// ==================== 模式切换 ====================
const modeOptions = [
  { label: '在线模式', value: 'online' },
  { label: '本地模式', value: 'local' }
]

const handleModeChange = (value: 'online' | 'local') => {
  modeStore.setMode(value)
  message.success(`已切换到${value === 'online' ? '在线' : '本地'}模式`)
}

// ==================== AI 模型配置 ====================
const isTesting = ref(false)
const testResult = ref<'success' | 'failed' | null>(null)
const showModelEditor = ref(false)
const editingModel = ref<AIModelConfig | null>(null)
const modelForm = ref({
  name: '',
  baseUrl: '',
  apiKey: '',
  modelId: ''
})

// 模型预设
const MODEL_PRESETS = [
  {
    label: 'DeepSeek（深度求索）',
    value: 'deepseek',
    name: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1',
    modelId: 'deepseek-chat'
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
    modelId: ''
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
    modelId: model.modelId
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
const newCategoryName = ref('')
const selectedParentCategory = ref<string | null>(null)

// 分类树数据
const categoryTreeData = computed<TreeOption[]>(() => {
  return categoriesStore.allCategories.map(category => ({
    key: category.slug,
    label: category.name,
    children: category.subCategories.map(sub => ({
      key: `${category.slug}-${sub.slug}`,
      label: sub.name,
      suffix: () => sub.isCustom ? '（自定义）' : ''
    }))
  }))
})

// 添加自定义分类
const handleAddCategory = () => {
  if (!newCategoryName.value.trim()) {
    message.error('请输入分类名称')
    return
  }

  if (!selectedParentCategory.value) {
    message.error('请选择所属一级分类')
    return
  }

  const success = categoriesStore.addCustomCategory(
    selectedParentCategory.value,
    newCategoryName.value.trim()
  )

  if (success) {
    message.success('分类添加成功')
    newCategoryName.value = ''
  } else {
    message.error('分类已存在')
  }
}

// 删除自定义分类
const handleDeleteCategory = (name: string) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除分类"${name}"吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      categoriesStore.removeCustomCategory(name)
      message.success('分类已删除')
    }
  })
}

// ==================== Git 平台配置 ====================
import { onMounted } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL

const githubForm = ref({ token: '', owner: '', repo: '', branch: 'main' })
const giteeForm = ref({ token: '', owner: '', repo: '', branch: 'master' })

// 历史选项
const gitOptions = ref<Record<string, Record<string, { label: string; value: string }[]>>>({
  github: { token: [], owner: [], repo: [], branch: [] },
  gitee: { token: [], owner: [], repo: [], branch: [] }
})

const githubTestResult = ref<'success' | 'failed' | null>(null)
const giteeTestResult = ref<'success' | 'failed' | null>(null)
const isTestingGithub = ref(false)
const isTestingGitee = ref(false)

// 从后端加载配置
async function loadGitConfig() {
  try {
    const res = await fetch(`${API_BASE}/api/git-config`)
    const json = await res.json()
    if (json.success && json.data) {
      const { config, options } = json.data
      if (config.github) githubForm.value = { ...githubForm.value, ...config.github }
      if (config.gitee) giteeForm.value = { ...giteeForm.value, ...config.gitee }
      if (options) gitOptions.value = options
    }
  } catch (e) {
    console.warn('加载 Git 配置失败:', e)
  }
}

// 保存配置到后端 .env 文件
async function saveGitConfig(platform: 'github' | 'gitee') {
  const form = platform === 'github' ? githubForm.value : giteeForm.value
  try {
    const res = await fetch(`${API_BASE}/api/git-config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [platform]: form })
    })
    const json = await res.json()
    if (json.success) {
      message.success(`${platform === 'github' ? 'GitHub' : 'Gitee'} 配置已保存`)
      await loadGitConfig() // 刷新选项
    } else {
      message.error('保存失败')
    }
  } catch (e: any) {
    message.error(`保存失败: ${e.message}`)
  }
}

// 删除历史选项
async function deleteGitHistoryItem(platform: string, field: string, value: string) {
  try {
    await fetch(`${API_BASE}/api/git-config/history/${platform}/${field}/${encodeURIComponent(value)}`, { method: 'DELETE' })
    await loadGitConfig()
    message.success('已删除')
  } catch (e: any) {
    message.error(`删除失败: ${e.message}`)
  }
}

async function testGithubConnection() {
  if (!githubForm.value.token) {
    message.warning('请先填写 GitHub Token')
    return
  }
  isTestingGithub.value = true
  githubTestResult.value = null
  try {
    const res = await fetch('https://api.github.com/user', {
      headers: { Authorization: `token ${githubForm.value.token}` }
    })
    if (res.ok) {
      const user = await res.json()
      githubTestResult.value = 'success'
      message.success(`连接成功，用户: ${user.login}`)
    } else {
      githubTestResult.value = 'failed'
      message.error(`连接失败: HTTP ${res.status}`)
    }
  } catch (e: any) {
    githubTestResult.value = 'failed'
    message.error(`连接失败: ${e.message}`)
  } finally {
    isTestingGithub.value = false
  }
}

async function testGiteeConnection() {
  if (!giteeForm.value.token) {
    message.warning('请先填写 Gitee Token')
    return
  }
  isTestingGitee.value = true
  giteeTestResult.value = null
  try {
    const res = await fetch(`https://gitee.com/api/v5/user?access_token=${giteeForm.value.token}`)
    if (res.ok) {
      const user = await res.json()
      giteeTestResult.value = 'success'
      message.success(`连接成功，用户: ${user.login}`)
    } else {
      giteeTestResult.value = 'failed'
      message.error(`连接失败: HTTP ${res.status}`)
    }
  } catch (e: any) {
    giteeTestResult.value = 'failed'
    message.error(`连接失败: ${e.message}`)
  } finally {
    isTestingGitee.value = false
  }
}

onMounted(loadGitConfig)
</script>

<template>
  <div class="settings">
    <n-h2 class="page-title">设置</n-h2>

    <n-tabs type="line" animated>
      <!-- 基础设置 -->
      <n-tab-pane name="basic" tab="基础设置">
        <n-space vertical :size="24">
          <!-- 模式切换 -->
          <n-card title="模式切换" class="setting-card">
            <n-space vertical :size="16">
              <n-p>选择博客管理的工作模式：</n-p>
              <n-radio-group
                :value="modeStore.mode"
                @update:value="handleModeChange"
                name="mode-group"
              >
                <n-radio-button
                  v-for="option in modeOptions"
                  :key="option.value"
                  :value="option.value"
                  :label="option.label"
                />
              </n-radio-group>
              <n-space :size="8">
                <n-tag :type="modeStore.isOnline ? 'success' : 'warning'">
                  当前模式：{{ modeStore.isOnline ? '在线模式' : '本地模式' }}
                </n-tag>
              </n-space>
              <n-alert type="info" title="模式说明">
                <template v-if="modeStore.isOnline">
                  在线模式：通过 GitHub API 管理博客，需要网络连接，支持多人协作。
                </template>
                <template v-else>
                  本地模式：直接操作本地文件，无需网络，适合离线开发。
                </template>
              </n-alert>
            </n-space>
          </n-card>
        </n-space>
      </n-tab-pane>

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
          <!-- 分类树 -->
          <n-card title="现有分类体系" class="setting-card">
            <n-tree
              :data="categoryTreeData"
              block-line
              expand-on-click
              default-expand-all
            />
          </n-card>

          <!-- 新增分类 -->
          <n-card title="新增二级分类" class="setting-card">
            <n-space vertical :size="16">
              <n-form label-placement="left" label-width="120">
                <n-form-item label="所属一级分类">
                  <n-select
                    v-model:value="selectedParentCategory"
                    :options="categoriesStore.primaryCategories"
                    placeholder="请选择一级分类"
                    style="width: 300px"
                  />
                </n-form-item>
                <n-form-item label="二级分类名称">
                  <n-input
                    v-model:value="newCategoryName"
                    placeholder="请输入二级分类名称"
                    style="width: 300px"
                    @keyup.enter="handleAddCategory"
                  />
                </n-form-item>
              </n-form>
              <n-space>
                <n-button
                  type="primary"
                  :disabled="!newCategoryName || !selectedParentCategory"
                  @click="handleAddCategory"
                >
                  添加分类
                </n-button>
              </n-space>
            </n-space>
          </n-card>

          <!-- 自定义分类列表 -->
          <n-card
            v-if="categoriesStore.customCategories.length > 0"
            title="自定义分类"
            class="setting-card"
          >
            <n-space vertical :size="8">
              <n-space
                v-for="category in categoriesStore.customCategories"
                :key="category.slug"
                align="center"
              >
                <n-tag type="info" closable @close="handleDeleteCategory(category.name)">
                  {{ category.name }}
                </n-tag>
                <span class="category-slug">{{ category.slug }}</span>
              </n-space>
            </n-space>
          </n-card>
        </n-space>
      </n-tab-pane>

      <!-- Git 平台配置 -->
      <n-tab-pane name="git" tab="Git 平台">
        <n-collapse>
          <!-- GitHub -->
          <n-collapse-item title="GitHub" name="github">
            <n-form label-placement="left" label-width="100">
              <n-form-item label="Token">
                <n-input
                  v-model:value="githubForm.token"
                  type="password"
                  show-password-on="click"
                  placeholder="ghp_xxxxxxxxxxxx"
                />
              </n-form-item>
              <n-form-item label="Owner">
                <n-select
                  v-model:value="githubForm.owner"
                  :options="gitOptions.github.owner"
                  filterable
                  tag
                  placeholder="输入或选择 Owner"
                />
              </n-form-item>
              <n-form-item label="仓库">
                <n-select
                  v-model:value="githubForm.repo"
                  :options="gitOptions.github.repo"
                  filterable
                  tag
                  placeholder="输入或选择仓库"
                />
              </n-form-item>
              <n-form-item label="分支">
                <n-select
                  v-model:value="githubForm.branch"
                  :options="gitOptions.github.branch"
                  filterable
                  tag
                  placeholder="输入或选择分支"
                />
              </n-form-item>
            </n-form>
            <n-space style="margin-top: 8px;">
              <n-button type="primary" @click="saveGitConfig('github')">保存</n-button>
              <n-button :loading="isTestingGithub" @click="testGithubConnection">测试连接</n-button>
              <n-tag v-if="githubTestResult === 'success'" type="success" size="small">✓ 连接成功</n-tag>
              <n-tag v-else-if="githubTestResult === 'failed'" type="error" size="small">✗ 连接失败</n-tag>
            </n-space>
          </n-collapse-item>

          <!-- Gitee -->
          <n-collapse-item title="Gitee" name="gitee">
            <n-form label-placement="left" label-width="100">
              <n-form-item label="Token">
                <n-input
                  v-model:value="giteeForm.token"
                  type="password"
                  show-password-on="click"
                  placeholder="Gitee 个人访问令牌"
                />
              </n-form-item>
              <n-form-item label="Owner">
                <n-select
                  v-model:value="giteeForm.owner"
                  :options="gitOptions.gitee.owner"
                  filterable
                  tag
                  placeholder="输入或选择 Owner"
                />
              </n-form-item>
              <n-form-item label="仓库">
                <n-select
                  v-model:value="giteeForm.repo"
                  :options="gitOptions.gitee.repo"
                  filterable
                  tag
                  placeholder="输入或选择仓库"
                />
              </n-form-item>
              <n-form-item label="分支">
                <n-select
                  v-model:value="giteeForm.branch"
                  :options="gitOptions.gitee.branch"
                  filterable
                  tag
                  placeholder="输入或选择分支"
                />
              </n-form-item>
            </n-form>
            <n-space style="margin-top: 8px;">
              <n-button type="primary" @click="saveGitConfig('gitee')">保存</n-button>
              <n-button :loading="isTestingGitee" @click="testGiteeConnection">测试连接</n-button>
              <n-tag v-if="giteeTestResult === 'success'" type="success" size="small">✓ 连接成功</n-tag>
              <n-tag v-else-if="giteeTestResult === 'failed'" type="error" size="small">✗ 连接失败</n-tag>
            </n-space>
          </n-collapse-item>
        </n-collapse>
      </n-tab-pane>
    </n-tabs>

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
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  margin-bottom: 24px;
}

.setting-card {
  margin-bottom: 16px;
}

.empty-models {
  padding: 20px 0;
  text-align: center;
}

.model-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-card.active {
  border: 2px solid #18a058;
}

.connection-test {
  margin-top: 16px;
}

.category-slug {
  color: #999;
  font-size: 12px;
  font-family: monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings {
    padding: 16px;
  }
}
</style>