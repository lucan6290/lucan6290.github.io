<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NAlert,
  NButton,
  NCheckbox,
  NDropdown,
  NEmpty,
  NInput,
  NList,
  NListItem,
  NSelect,
  NTag,
  NText,
  useMessage,
  type DropdownOption,
  type SelectOption
} from 'naive-ui'
import { getAPI } from '@/api'
import ErrorState from '@/components/ai-writing/ErrorState.vue'
import OperationLog from '@/components/ai-writing/OperationLog.vue'
import RiskFlags from '@/components/ai-writing/RiskFlags.vue'
import { useAIWritingStore } from '@/stores/aiWriting'
import { useKnowledgeIndexStore } from '@/stores/knowledgeIndex'
import { usePostsStore } from '@/stores/posts'
import { useSettingsStore } from '@/stores/settings'
import type { PostInfo } from '@/types/api'
import type { AIApprovalMode, AIModelPayload, AIWritingMode } from '@/types/ai-writing'

interface AttachedMaterial {
  id: string
  name: string
  size: number
  status: 'ready' | 'unsupported' | 'too-large' | 'error'
  note: string
}

const router = useRouter()
const message = useMessage()
const api = getAPI()
const aiWriting = useAIWritingStore()
const knowledge = useKnowledgeIndexStore()
const settings = useSettingsStore()
const postsStore = usePostsStore()
const fileInputRef = ref<HTMLInputElement | null>(null)
const attachedMaterials = ref<AttachedMaterial[]>([])

const acceptedMaterialTypes = [
  '.md',
  '.markdown',
  '.txt',
  '.text',
  '.log',
  '.doc',
  '.docx',
  'text/markdown',
  'text/plain',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
].join(',')

const modeOptions: Array<{ value: AIWritingMode; label: string; icon: string; placeholder: string }> = [
  { value: 'agent', label: 'Agent模式', icon: '↯', placeholder: '写下想法、笔记、素材或粗糙文章，Agent 会整理成博客草稿' },
  { value: 'knowledge', label: '知识库模式', icon: '▣', placeholder: '询问本地文章，例如：我有哪些文章？写过 Codex 相关内容吗？' }
]

const approvalOptions: DropdownOption[] = [
  {
    label: '请求批准',
    key: 'request-approval',
    props: { description: '写入前始终询问' }
  },
  {
    label: '替我审批',
    key: 'delegate-approval',
    props: { description: '仅对低风险操作自动批准' }
  },
  {
    label: '完全访问权限',
    key: 'full-access',
    props: { description: '仅限 AI 写作边界内执行' }
  }
]

const categoryOptions = computed<SelectOption[]>(() =>
  aiWriting.registry.map(item => ({
    label: `${item.primaryName} (${item.prefix1})`,
    value: item.primarySlug
  }))
)

const modelSelectOptions = computed<SelectOption[]>(() =>
  settings.aiModels.map(model => ({
    label: model.name,
    value: model.id
  }))
)

const currentMode = computed(() =>
  modeOptions.find(item => item.value === aiWriting.activeMode) || modeOptions[0]
)

const currentInput = computed({
  get: () => {
    if (aiWriting.activeMode === 'knowledge') return knowledge.question
    return aiWriting.agentInput
  },
  set: (value: string) => {
    if (aiWriting.activeMode === 'knowledge') {
      knowledge.question = value
    } else {
      aiWriting.agentInput = value
    }
  }
})

const activeModelLabel = computed(() => settings.activeModel?.name || '未配置模型')

const approvalLabel = computed(() => {
  if (aiWriting.approvalMode === 'request-approval') return '请求批准'
  if (aiWriting.approvalMode === 'delegate-approval') return '替我审批'
  return '完全访问权限'
})

const canSubmit = computed(() => {
  if (aiWriting.activeMode === 'knowledge') {
    return Boolean(knowledge.question.trim()) && knowledge.indexStatus !== 'rebuilding'
  }
  return Boolean(aiWriting.agentInput.trim())
})

const isBusy = computed(() =>
  aiWriting.isGenerating || aiWriting.isCreatingDraft || knowledge.isAsking || knowledge.isScanning
)

const canCreateDraft = computed(() => {
  if (!aiWriting.draftPlan || !aiWriting.draftValidation?.valid) return false
  if (aiWriting.agentDecision.blocked) return false
  if (aiWriting.draftPlan.clarificationRequired && !aiWriting.continueWithCurrentUnderstanding && Object.keys(aiWriting.clarificationAnswers).length === 0) {
    return false
  }
  return !aiWriting.isCreatingDraft && !aiWriting.createResultPath
})

function activeModelPayload(): AIModelPayload | null {
  const model = settings.activeModel
  if (!model) return null
  return {
    baseUrl: model.baseUrl,
    apiKey: model.apiKey,
    modelId: model.modelId,
    provider: model.provider,
    apiFormat: model.apiFormat,
    anthropicBaseUrl: model.anthropicBaseUrl,
    thinkingMode: model.thinkingMode,
    reasoningEffort: model.reasoningEffort,
    agentMode: model.agentMode,
    toolCalls: model.toolCalls,
    strictToolCalls: model.strictToolCalls,
    jsonMode: model.jsonMode,
    temperature: model.temperature ?? 0.3,
    maxTokens: model.maxTokens ?? 4096
  }
}

function setApproval(key: string | number): void {
  aiWriting.approvalMode = key as AIApprovalMode
}

function setActiveModel(id: string): void {
  if (!settings.setActiveModel(id)) {
    message.warning('模型配置不存在，请重新选择')
  }
}

function setMode(mode: AIWritingMode): void {
  if (isBusy.value) return
  aiWriting.activeMode = mode
}

function openMaterialPicker(): void {
  fileInputRef.value?.click()
}

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function getFileExtension(fileName: string): string {
  return fileName.split('.').pop()?.toLowerCase() || ''
}

function appendMaterialToInput(fileName: string, content: string): void {
  const trimmedContent = content.trim()
  if (!trimmedContent) return
  const materialBlock = [
    '',
    '',
    `【附件素材：${fileName}】`,
    trimmedContent,
    '【附件素材结束】'
  ].join('\n')
  currentInput.value = `${currentInput.value.trimEnd()}${materialBlock}`
}

async function handleMaterialFiles(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''
  if (files.length === 0) return

  const textExtensions = new Set(['md', 'markdown', 'txt', 'text', 'log'])
  const backendExtractExtensions = new Set(['docx'])
  const maxTextFileSize = 512 * 1024
  const maxBackendFileSize = 2 * 1024 * 1024
  let importedCount = 0

  for (const file of files) {
    const extension = getFileExtension(file.name)
    const id = `material_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`

    if (backendExtractExtensions.has(extension)) {
      if (file.size > maxBackendFileSize) {
        attachedMaterials.value.push({
          id,
          name: file.name,
          size: file.size,
          status: 'too-large',
          note: '超过 2MB'
        })
        continue
      }
      if (!api.extractWritingMaterial) {
        attachedMaterials.value.push({
          id,
          name: file.name,
          size: file.size,
          status: 'unsupported',
          note: '后端未启用解析'
        })
        continue
      }
      try {
        const result = await api.extractWritingMaterial(file)
        appendMaterialToInput(result.filename || file.name, result.content)
        attachedMaterials.value.push({
          id,
          name: file.name,
          size: file.size,
          status: 'ready',
          note: '已加入输入'
        })
        importedCount += 1
      } catch {
        attachedMaterials.value.push({
          id,
          name: file.name,
          size: file.size,
          status: 'error',
          note: '解析失败'
        })
      }
      continue
    }

    if (!textExtensions.has(extension)) {
      attachedMaterials.value.push({
        id,
        name: file.name,
        size: file.size,
        status: 'unsupported',
        note: extension === 'doc' ? '请另存为 docx/md/txt' : '格式不支持'
      })
      continue
    }

    if (file.size > maxTextFileSize) {
      attachedMaterials.value.push({
        id,
        name: file.name,
        size: file.size,
        status: 'too-large',
        note: '文件过大'
      })
      continue
    }

    try {
      const content = await file.text()
      appendMaterialToInput(file.name, content)
      attachedMaterials.value.push({
        id,
        name: file.name,
        size: file.size,
        status: 'ready',
        note: '已加入输入'
      })
      importedCount += 1
    } catch {
      attachedMaterials.value.push({
        id,
        name: file.name,
        size: file.size,
        status: 'error',
        note: '读取失败'
      })
    }
  }

  if (importedCount > 0) {
    message.success(`已添加 ${importedCount} 个素材文件`)
  }
  const unsupportedCount = attachedMaterials.value.filter(item => item.status !== 'ready').length
  if (unsupportedCount > 0) {
    message.warning('部分文件未加入输入，请使用 md/txt/log/docx 素材')
  }
}

async function submitCurrentInput(): Promise<void> {
  if (!canSubmit.value) return
  if (aiWriting.activeMode === 'knowledge') {
    await askKnowledge()
  } else {
    await generateAgentPlan()
  }
}

async function generateAgentPlan(): Promise<void> {
  const model = activeModelPayload()
  if (!model) {
    message.warning('请先配置 AI 模型')
    router.push('/settings')
    return
  }
  await aiWriting.generateAgentPlan(model)
}

async function createDraft(): Promise<void> {
  const plan = aiWriting.draftPlan
  if (!plan || !canCreateDraft.value) return
  if (!api.commitAgentPlan) {
    message.error('后端未提供 Agent 草稿提交接口')
    return
  }

  aiWriting.isCreatingDraft = true
  aiWriting.addLog('info', '开始创建草稿', `${plan.prefix1}-${plan.prefix2}-${plan.title}.md`)

  try {
    const result = await api.commitAgentPlan({
      sessionId: aiWriting.sessionId,
      approvalMode: aiWriting.approvalMode,
      confirmed: true,
      idempotencyKey: `${aiWriting.sessionId}:${plan.prefix1}:${plan.prefix2}:${plan.title}`,
      plan
    })

    aiWriting.createResultPath = result.path
    aiWriting.addLog('success', '草稿创建成功', result.path)
    postsStore.addPostToCache({
      filename: result.path.split('/').pop()?.replace(/\.md$/, '') || plan.title,
      path: result.path,
      title: plan.title,
      category: plan.primarySlug,
      subCategory: plan.prefix2,
      tags: plan.tags,
      date: new Date().toISOString(),
      status: 'published',
      displayStatus: 'ok',
      displayStatusLabel: '正常',
      description: plan.description
    } satisfies PostInfo)
    message.success('草稿创建成功')
    router.push({ path: '/editor', query: { file: result.path } })
  } catch (err) {
    const detail = err instanceof Error ? err.message : '请检查后端创建和更新接口。'
    aiWriting.addLog('error', '草稿创建失败', detail)
    message.error(`草稿创建失败：${detail}`)
  } finally {
    aiWriting.isCreatingDraft = false
  }
}

async function askKnowledge(): Promise<void> {
  await knowledge.askKnowledge(activeModelPayload() || undefined)
  if (knowledge.error) message.error(knowledge.error.message)
}

async function scanKnowledge(): Promise<void> {
  await knowledge.scanIndex()
  if (knowledge.error) message.error(knowledge.error.message)
}

function updatePlanCategory(primarySlug: string): void {
  if (!aiWriting.draftPlan) return
  const category = aiWriting.registry.find(item => item.primarySlug === primarySlug)
  if (!category) return
  aiWriting.draftPlan.primarySlug = category.primarySlug
  aiWriting.draftPlan.primaryName = category.primaryName
  aiWriting.draftPlan.prefix1 = category.prefix1
  aiWriting.draftValidation = null
}

function formatWarnings(items: string[] | undefined): string {
  return items?.length ? items.join('；') : '无'
}

onMounted(() => {
  aiWriting.fetchCategoryRegistry()
  knowledge.loadIndex()
})
</script>

<template>
  <div class="ai-chat-page">
    <header class="chat-titlebar">
      <div class="title-left">
        <h1>AI 辅助写作</h1>
        <span class="title-muted">从想法到草稿</span>
      </div>
      <div class="title-actions">
        <n-button class="title-action-button" quaternary size="small" @click="router.push('/settings')">打开设置</n-button>
        <n-button class="title-action-button" quaternary size="small" @click="aiWriting.resetSession">新会话</n-button>
      </div>
    </header>

    <main class="chat-main">
      <div class="mode-pill-row">
        <button
          v-for="mode in modeOptions"
          :key="mode.value"
          type="button"
          class="mode-pill"
          :class="{ active: aiWriting.activeMode === mode.value }"
          :disabled="isBusy"
          @click="setMode(mode.value)"
        >
          <span>{{ mode.icon }}</span>
          {{ mode.label }}
        </button>
      </div>

      <section class="conversation">
        <div class="conversation-entry muted-entry">
          <span class="entry-icon">●</span>
          <span>已连接 {{ activeModelLabel }}，当前权限为 {{ approvalLabel }}</span>
        </div>

        <div class="assistant-message intro-message">
          <p>
            你可以直接写一段灵感、粘贴粗糙笔记，或切换到知识库模式询问本地文章。
            Agent 模式会先生成可审核草稿方案；创建前仍会经过分类、前缀和风险校验。
          </p>
        </div>

        <error-state :error="aiWriting.agentError" compact />
        <error-state :error="knowledge.error" compact />

        <div v-if="aiWriting.draftPlan" class="assistant-message plan-message">
          <div class="entry-meta">
            <span>生成草稿方案</span>
            <n-tag :type="aiWriting.draftValidation?.valid ? 'success' : 'warning'" size="small">
              {{ aiWriting.draftValidation?.valid ? '校验通过' : '待修正' }}
            </n-tag>
          </div>

          <h2>{{ aiWriting.draftPlan.title }}</h2>
          <p>{{ aiWriting.draftPlan.userIntent }}</p>

          <div class="plan-grid">
            <label>
              一级分类
              <n-select
                :value="aiWriting.draftPlan.primarySlug"
                :options="categoryOptions"
                size="small"
                @update:value="updatePlanCategory"
              />
            </label>
            <label>
              二级前缀
              <n-input v-model:value="aiWriting.draftPlan.prefix2" size="small" />
            </label>
          </div>

          <div class="tag-line">
            <n-tag v-for="tag in aiWriting.draftPlan.tags" :key="tag" size="small">{{ tag }}</n-tag>
          </div>

          <div v-if="aiWriting.draftPlan.clarificationRequired" class="clarify-box">
            <strong>需要求证</strong>
            <div
              v-for="question in aiWriting.draftPlan.clarificationQuestions"
              :key="question"
              class="clarify-item"
            >
              <span>{{ question }}</span>
              <n-input
                :value="aiWriting.clarificationAnswers[question] || ''"
                size="small"
                placeholder="填写回答后可重新生成"
                @update:value="(value: string) => { aiWriting.clarificationAnswers[question] = value }"
              />
            </div>
            <n-checkbox v-model:checked="aiWriting.continueWithCurrentUnderstanding">
              按当前理解继续
            </n-checkbox>
          </div>

          <div class="preview-section">
            <h3>风险提示</h3>
            <risk-flags :flags="aiWriting.draftPlan.riskFlags" />
          </div>

          <div class="preview-section">
            <h3>正文预览</h3>
            <pre class="markdown-preview">{{ aiWriting.draftPlan.bodyMarkdown }}</pre>
          </div>

          <n-alert
            v-if="aiWriting.draftValidation && (!aiWriting.draftValidation.valid || aiWriting.draftValidation.warnings.length)"
            type="warning"
            title="校验结果"
            class="section-alert"
          >
            <div v-if="aiWriting.draftValidation.blockingErrors.length">
              阻断错误：{{ aiWriting.draftValidation.blockingErrors.join('；') }}
            </div>
            <div>警告：{{ formatWarnings(aiWriting.draftValidation.warnings) }}</div>
          </n-alert>

          <div class="message-actions">
            <n-button size="small" @click="generateAgentPlan">重新生成</n-button>
            <n-button
              type="primary"
              size="small"
              :loading="aiWriting.isCreatingDraft"
              :disabled="!canCreateDraft"
              @click="createDraft"
            >
              创建草稿
            </n-button>
          </div>
        </div>

        <div v-if="knowledge.answer" class="assistant-message knowledge-message">
          <div class="entry-meta">
            <span>知识库回答</span>
            <n-tag size="small" type="info">{{ knowledge.answer.questionType }}</n-tag>
          </div>
          <pre class="answer-body">{{ knowledge.answer.answer }}</pre>
          <risk-flags :flags="knowledge.answer.warnings" empty-text="暂无警告" />

          <div class="preview-section">
            <h3>来源</h3>
            <n-empty v-if="knowledge.answer.citations.length === 0" description="没有引用来源" size="small" />
            <n-list v-else>
              <n-list-item v-for="citation in knowledge.answer.citations" :key="`${citation.path}-${citation.heading || ''}`">
                <button class="source-link" type="button" @click="router.push({ path: '/editor', query: { file: citation.path } })">
                  {{ citation.title }}
                </button>
                <n-text depth="3" class="mono">{{ citation.path }}{{ citation.heading ? `#${citation.heading}` : '' }}</n-text>
              </n-list-item>
            </n-list>
          </div>
        </div>

        <div v-if="aiWriting.operationLog.length" class="assistant-message log-message">
          <div class="entry-meta">
            <span>最近操作</span>
            <n-tag size="small">{{ aiWriting.operationLog.length }} 条</n-tag>
          </div>
          <operation-log :items="aiWriting.operationLog.slice(0, 4)" />
        </div>
      </section>
    </main>

    <section class="composer-shell">
      <div class="composer">
        <input
          ref="fileInputRef"
          class="material-file-input"
          type="file"
          multiple
          :accept="acceptedMaterialTypes"
          @change="handleMaterialFiles"
        />
        <div v-if="attachedMaterials.length" class="attachment-strip">
          <div
            v-for="item in attachedMaterials"
            :key="item.id"
            class="attachment-chip"
            :class="`is-${item.status}`"
            :title="`${item.name} · ${formatBytes(item.size)} · ${item.note}`"
          >
            <span class="attachment-icon">文</span>
            <span class="attachment-name">{{ item.name }}</span>
            <span class="attachment-note">{{ item.note }}</span>
          </div>
        </div>
        <n-input
          v-model:value="currentInput"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 8 }"
          :placeholder="currentMode.placeholder"
          class="composer-input"
          @keydown.ctrl.enter.prevent="submitCurrentInput"
        />
        <div class="composer-toolbar">
          <div class="composer-left">
            <button class="round-tool" type="button" title="添加 md/txt/docx 素材文件" @click="openMaterialPicker">＋</button>
            <n-dropdown
              trigger="click"
              :options="approvalOptions"
              @select="setApproval"
            >
              <button class="approval-chip" type="button">
                {{ approvalLabel }}
                <span>⌄</span>
              </button>
            </n-dropdown>
            <n-checkbox v-if="aiWriting.activeMode === 'knowledge'" v-model:checked="knowledge.forceRescan">
              强制扫描
            </n-checkbox>
          </div>
          <div class="composer-right">
            <n-select
              :value="settings.activeModelId"
              :options="modelSelectOptions"
              size="small"
              class="model-select"
              placeholder="选择模型"
              :consistent-menu-width="false"
              @update:value="setActiveModel"
            />
            <button
              class="send-button"
              type="button"
              :disabled="!canSubmit || isBusy"
              @click="submitCurrentInput"
            >
              {{ isBusy ? '■' : '↑' }}
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.ai-chat-page {
  --ai-bg: #f7f6f1;
  --ai-surface: rgba(255, 255, 255, 0.86);
  --ai-surface-strong: #ffffff;
  --ai-ink: #17241f;
  --ai-muted: #758279;
  --ai-soft: #eef2eb;
  --ai-line: rgba(32, 48, 41, 0.11);
  --ai-line-strong: rgba(37, 107, 82, 0.22);
  --ai-primary: #256b52;
  --ai-primary-hover: #1f7a59;
  --ai-primary-soft: rgba(37, 107, 82, 0.11);
  --ai-copper: #a45e24;
  --ai-copper-soft: rgba(164, 94, 36, 0.12);
  --ai-slate: #486b86;
  --ai-shadow-sm: 0 8px 24px rgba(26, 42, 35, 0.07);
  --ai-shadow-md: 0 20px 60px rgba(24, 39, 33, 0.13);
  position: relative;
  min-height: 100%;
  padding: 0 28px 160px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.74), rgba(247, 246, 241, 0.92) 34%, var(--ai-bg)),
    repeating-linear-gradient(90deg, rgba(37, 107, 82, 0.035) 0, rgba(37, 107, 82, 0.035) 1px, transparent 1px, transparent 54px);
  color: var(--ai-ink);
  font-family: "Aptos", "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  overflow: hidden;
}

.chat-titlebar {
  position: sticky;
  top: 0;
  z-index: 8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 58px;
  margin: 0 -28px;
  padding: 0 22px;
  border-bottom: 1px solid var(--ai-line);
  background: rgba(248, 248, 244, 0.9);
  backdrop-filter: blur(22px);
}

.title-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.title-left h1 {
  margin: 0;
  color: var(--ai-ink);
  font-size: 17px;
  line-height: 1;
  font-weight: 820;
}

.title-muted {
  color: var(--ai-muted);
  font-size: 13px;
  font-weight: 650;
}

.title-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.title-action-button :deep(.n-button__content) {
  color: #40514a;
  font-weight: 720;
}

.title-action-button:hover :deep(.n-button__content) {
  color: var(--ai-primary);
}

.chat-main {
  width: min(860px, 100%);
  margin: 0 auto;
  padding-top: 26px;
}

.mode-pill-row {
  display: flex;
  justify-content: center;
  gap: 4px;
  width: fit-content;
  max-width: 100%;
  margin: 0 auto 30px;
  padding: 4px;
  border: 1px solid var(--ai-line);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.76);
  box-shadow: var(--ai-shadow-sm);
  backdrop-filter: blur(18px);
}

.mode-pill {
  min-width: 142px;
  height: 42px;
  padding: 0 22px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: #31443b;
  font-size: 15px;
  font-weight: 780;
  cursor: pointer;
  transition: color 0.18s ease, background-color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.mode-pill:hover:not(:disabled) {
  color: var(--ai-primary);
  background: rgba(37, 107, 82, 0.07);
}

.mode-pill.active {
  border-color: rgba(37, 107, 82, 0.26);
  color: #164c39;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(234, 243, 237, 0.96));
  box-shadow: 0 8px 20px rgba(37, 107, 82, 0.16), inset 0 0 0 1px rgba(255, 255, 255, 0.68);
  transform: translateY(-1px);
}

.mode-pill:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.mode-pill span {
  margin-right: 8px;
  color: var(--ai-copper);
  font-weight: 900;
}

.conversation {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 40px;
}

.conversation-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  padding: 7px 10px;
  border: 1px solid rgba(72, 107, 134, 0.12);
  border-radius: 999px;
  color: var(--ai-muted);
  background: rgba(255, 255, 255, 0.68);
  font-size: 13px;
  font-weight: 650;
}

.entry-icon {
  color: var(--ai-primary);
  font-size: 9px;
  filter: drop-shadow(0 0 6px rgba(37, 107, 82, 0.38));
}

.assistant-message {
  font-size: 15px;
  line-height: 1.75;
  color: #26342e;
}

.assistant-message p {
  margin: 0;
}

.intro-message {
  position: relative;
  padding: 16px 18px;
  border-left: 3px solid var(--ai-primary);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.66);
  box-shadow: 0 1px 0 rgba(37, 107, 82, 0.08);
}

.plan-message,
.knowledge-message,
.log-message {
  padding: 18px;
  border: 1px solid var(--ai-line);
  border-radius: 8px;
  background: var(--ai-surface);
  box-shadow: var(--ai-shadow-sm);
  backdrop-filter: blur(18px);
}

.entry-meta,
.message-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.entry-meta {
  margin-bottom: 10px;
  color: var(--ai-muted);
  font-size: 13px;
  font-weight: 720;
}

.plan-message h2 {
  margin: 0 0 10px;
  color: #13221b;
  font-size: 23px;
  line-height: 1.35;
  font-weight: 850;
}

.plan-grid {
  display: grid;
  grid-template-columns: 1fr 160px;
  gap: 12px;
  margin: 16px 0;
}

.plan-grid label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #5e6f65;
  font-size: 12px;
  font-weight: 760;
}

.tag-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
}

.clarify-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 14px 0;
  padding: 14px;
  border: 1px solid rgba(164, 94, 36, 0.18);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(255, 251, 243, 0.96), rgba(253, 244, 231, 0.82));
  color: #5f3c20;
}

.clarify-box strong {
  color: #7b471c;
  font-weight: 820;
}

.clarify-item {
  display: grid;
  grid-template-columns: 1fr 240px;
  gap: 10px;
  align-items: center;
}

.preview-section {
  margin-top: 16px;
}

.preview-section h3 {
  margin: 0 0 8px;
  color: #23352d;
  font-size: 14px;
  font-weight: 820;
}

.markdown-preview,
.answer-body {
  margin: 0;
  max-height: 360px;
  overflow: auto;
  padding: 15px 16px;
  border: 1px solid rgba(37, 107, 82, 0.12);
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(250, 251, 248, 0.98), rgba(245, 247, 243, 0.98));
  color: #1f2e27;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  box-shadow: inset 0 1px 2px rgba(24, 39, 33, 0.04);
}

.section-alert {
  margin-top: 14px;
  border-radius: 8px;
}

.message-actions {
  justify-content: flex-end;
  margin-top: 16px;
}

.source-link {
  display: block;
  border: 0;
  padding: 0;
  color: var(--ai-primary);
  background: transparent;
  font-weight: 700;
  cursor: pointer;
  text-align: left;
  transition: color 0.18s ease;
}

.source-link:hover {
  color: var(--ai-copper);
}

.composer-shell {
  position: fixed;
  left: calc(212px + (100vw - 212px - 840px) / 2);
  bottom: 22px;
  z-index: 12;
  width: min(840px, calc(100vw - 280px));
}

.composer {
  min-height: 116px;
  padding: 15px;
  border: 1px solid rgba(37, 107, 82, 0.16);
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(250, 250, 247, 0.94));
  box-shadow: var(--ai-shadow-md), inset 0 1px 0 rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(26px);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.composer:focus-within {
  border-color: rgba(37, 107, 82, 0.36);
  box-shadow: 0 22px 68px rgba(24, 39, 33, 0.16), 0 0 0 4px rgba(37, 107, 82, 0.08);
}

.composer-input :deep(.n-input) {
  background: transparent;
}

.composer-input :deep(.n-input-wrapper) {
  padding: 0 2px;
}

.composer-input :deep(.n-input__border),
.composer-input :deep(.n-input__state-border) {
  display: none;
}

.composer-input :deep(.n-input__textarea-el),
.composer-input :deep(.n-input__placeholder) {
  color: #1f2e27;
  font-size: 15px;
  line-height: 1.68;
}

.composer-input :deep(.n-input__placeholder) {
  color: #9aa39c;
}

.composer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
}

.composer-left,
.composer-right {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.round-tool {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(37, 107, 82, 0.1);
  border-radius: 50%;
  color: #5c6b62;
  background: #edf2ed;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  transition: color 0.18s ease, background-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

.round-tool:hover {
  color: var(--ai-primary);
  background: #e3ede6;
  box-shadow: 0 8px 18px rgba(37, 107, 82, 0.12);
  transform: translateY(-1px);
}

.approval-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid rgba(37, 107, 82, 0.14);
  border-radius: 999px;
  color: #1f684d;
  background: var(--ai-primary-soft);
  font-weight: 760;
  cursor: pointer;
  transition: color 0.18s ease, background-color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.approval-chip:hover {
  border-color: rgba(37, 107, 82, 0.28);
  background: rgba(37, 107, 82, 0.16);
  box-shadow: 0 8px 18px rgba(37, 107, 82, 0.1);
}

.model-select {
  flex: 0 1 176px;
  min-width: 168px;
  max-width: 210px;
}

.model-select :deep(.n-base-selection) {
  --n-height: 30px !important;
  --n-border: 1px solid transparent !important;
  --n-border-hover: 1px solid rgba(37, 107, 82, 0.18) !important;
  --n-border-active: 1px solid rgba(37, 107, 82, 0.26) !important;
  --n-border-focus: 1px solid rgba(37, 107, 82, 0.26) !important;
  --n-box-shadow-active: none !important;
  --n-box-shadow-focus: none !important;
  border-radius: 999px !important;
  background: rgba(238, 242, 235, 0.76);
}

.model-select :deep(.n-base-selection-label) {
  padding: 0 6px 0 10px;
  background: transparent;
}

.model-select :deep(.n-base-selection-input),
.model-select :deep(.n-base-selection-placeholder) {
  color: #40514a;
  font-size: 12px;
  font-weight: 680;
}

.model-select :deep(.n-base-selection-placeholder) {
  color: #8b968f;
}

.send-button {
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 50%;
  color: white;
  background:
    linear-gradient(145deg, #2f7a55, #174a38);
  font-size: 20px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(37, 107, 82, 0.26);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}

.send-button:hover:not(:disabled) {
  box-shadow: 0 14px 30px rgba(37, 107, 82, 0.32);
  filter: saturate(1.06);
  transform: translateY(-1px);
}

.send-button:disabled {
  cursor: not-allowed;
  opacity: 0.42;
  box-shadow: none;
}

.material-file-input {
  display: none;
}

.attachment-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.attachment-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  height: 30px;
  padding: 0 9px 0 7px;
  border: 1px solid rgba(37, 107, 82, 0.14);
  border-radius: 999px;
  background: rgba(37, 107, 82, 0.08);
  color: #24493a;
  font-size: 12px;
  font-weight: 720;
}

.attachment-chip.is-unsupported,
.attachment-chip.is-too-large,
.attachment-chip.is-error {
  border-color: rgba(164, 94, 36, 0.2);
  background: rgba(164, 94, 36, 0.1);
  color: #6c431f;
}

.attachment-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 6px;
  color: white;
  background: var(--ai-primary);
  font-size: 11px;
  font-weight: 820;
}

.attachment-chip.is-unsupported .attachment-icon,
.attachment-chip.is-too-large .attachment-icon,
.attachment-chip.is-error .attachment-icon {
  background: var(--ai-copper);
}

.attachment-name {
  overflow: hidden;
  max-width: 220px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-note {
  color: rgba(36, 73, 58, 0.64);
  font-weight: 650;
}

.attachment-chip.is-unsupported .attachment-note,
.attachment-chip.is-too-large .attachment-note,
.attachment-chip.is-error .attachment-note {
  color: rgba(108, 67, 31, 0.72);
}

.ai-chat-page :deep(.n-tag) {
  border-radius: 999px;
  font-weight: 720;
}

.ai-chat-page :deep(.n-button) {
  --n-border-radius: 8px !important;
  font-weight: 750;
}

.ai-chat-page :deep(.n-button--primary-type) {
  --n-color: var(--ai-primary) !important;
  --n-color-hover: var(--ai-primary-hover) !important;
  --n-color-pressed: #1d563f !important;
  --n-border: 1px solid var(--ai-primary) !important;
  --n-border-hover: 1px solid var(--ai-primary-hover) !important;
}

.ai-chat-page :deep(.n-input .n-input__border),
.ai-chat-page :deep(.n-base-selection .n-base-selection__border) {
  border-radius: 8px;
}

.ai-chat-page :deep(.n-checkbox .n-checkbox-box) {
  border-radius: 5px;
}

.ai-chat-page :deep(.n-list) {
  border-radius: 8px;
  background: transparent;
}

.mono {
  display: block;
  margin-top: 4px;
  font-family: "Cascadia Mono", "Consolas", monospace;
  font-size: 12px;
}

@media (max-width: 1200px) {
  .composer-shell {
    left: 24px;
    right: 24px;
    width: auto;
  }
}

@media (max-width: 760px) {
  .ai-chat-page {
    padding: 0 14px 160px;
  }

  .chat-titlebar {
    margin: 0 -14px;
    padding: 0 12px;
  }

  .title-muted {
    display: none;
  }

  .mode-pill-row {
    width: 100%;
    overflow-x: auto;
    justify-content: flex-start;
  }

  .mode-pill {
    min-width: 126px;
    padding: 0 16px;
    font-size: 14px;
  }

  .plan-grid,
  .clarify-item {
    grid-template-columns: 1fr;
  }

  .composer-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .composer-left,
  .composer-right {
    width: 100%;
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .model-select {
    flex-basis: min(210px, calc(100% - 48px));
    min-width: min(168px, calc(100% - 48px));
  }
}
</style>
