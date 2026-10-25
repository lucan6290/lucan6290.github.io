<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'
import type { AIModelConfigDTO, AIModelTestResultDTO, AIDraftResultDTO, ArticleType } from '@/types/api'

const appStore = useAppStore()

const loading = ref(false)
const models = ref<AIModelConfigDTO[]>([])
const selectedModelId = ref<string>('')
const testing = ref(false)
const generating = ref(false)
const rewriting = ref(false)

// 草稿生成表单
const draftForm = ref({
  type: 'blog' as ArticleType,
  title: '',
  outline: '',
  references: '',
  targetStyle: '技术博客'
})

const draftResult = ref<AIDraftResultDTO | null>(null)

// 改写表单
const rewriteForm = ref({
  content: '',
  instruction: ''
})

const rewriteResult = ref<{ content: string; changes: string[] } | null>(null)

// 新模型表单
const showModelForm = ref(false)
const modelForm = ref({
  id: '',
  name: '',
  provider: 'openai',
  baseUrl: '',
  modelId: '',
  apiKey: '',
  is_default: false
})

async function loadModels() {
  loading.value = true
  try {
    models.value = await api.getAIModels()
    if (models.value.length > 0 && !selectedModelId.value) {
      const defaultModel = models.value.find(m => m.isDefault) || models.value[0]
      selectedModelId.value = defaultModel.id
    }
  } catch {
    appStore.showToast('加载 AI 模型失败', 'error')
  } finally {
    loading.value = false
  }
}

async function handleTestModel() {
  if (!selectedModelId.value) return
  testing.value = true
  try {
    const result: AIModelTestResultDTO = await api.testAIModel(selectedModelId.value)
    if (result.success) {
      appStore.showToast('连接成功', 'success')
    } else {
      appStore.showToast('连接失败', 'error', 5000)
    }
  } catch {
    appStore.showToast('测试失败', 'error')
  } finally {
    testing.value = false
  }
}

async function handleGenerate() {
  if (!draftForm.value.title.trim()) {
    appStore.showToast('请输入文章标题', 'warning')
    return
  }
  generating.value = true
  draftResult.value = null
  try {
    const outline = draftForm.value.outline
      ? draftForm.value.outline.split('\n').filter(Boolean)
      : []
    const references = draftForm.value.references
      ? draftForm.value.references.split('\n').filter(Boolean)
      : []
    draftResult.value = await api.createAIDraft({
      type: draftForm.value.type,
      title: draftForm.value.title,
      outline,
      references,
      target_style: draftForm.value.targetStyle
    })
    appStore.showToast('草稿生成成功', 'success')
  } catch {
    appStore.showToast('草稿生成失败', 'error')
  } finally {
    generating.value = false
  }
}

async function handleRewrite() {
  if (!rewriteForm.value.content.trim() || !rewriteForm.value.instruction.trim()) {
    appStore.showToast('请输入内容和改写指令', 'warning')
    return
  }
  rewriting.value = true
  rewriteResult.value = null
  try {
    rewriteResult.value = await api.rewriteAIContent({
      content: rewriteForm.value.content,
      instruction: rewriteForm.value.instruction,
      model_id: selectedModelId.value || undefined
    })
    appStore.showToast('改写完成', 'success')
  } catch {
    appStore.showToast('改写失败', 'error')
  } finally {
    rewriting.value = false
  }
}

async function handleSaveModel() {
  if (!modelForm.value.name || !modelForm.value.modelId || !modelForm.value.baseUrl) {
    appStore.showToast('请填写模型名称、模型ID和API地址', 'warning')
    return
  }
  try {
    const saved = await api.saveAIModel({
      id: modelForm.value.id || crypto.randomUUID(),
      name: modelForm.value.name,
      provider: modelForm.value.provider,
      baseUrl: modelForm.value.baseUrl,
      modelId: modelForm.value.modelId,
      apiKey: modelForm.value.apiKey || undefined,
      isDefault: modelForm.value.is_default
    })
    appStore.showToast('模型配置已保存', 'success')
    showModelForm.value = false
    modelForm.value = { id: '', name: '', provider: 'openai', baseUrl: '', modelId: '', apiKey: '', is_default: false }
    await loadModels()
  } catch {
    appStore.showToast('保存失败', 'error')
  }
}

async function handleDeleteModel(model: AIModelConfigDTO) {
  if (!confirm(`确定要删除模型「${model.name}」吗？`)) return
  try {
    models.value = await api.deleteAIModel(model.id)
    appStore.showToast('模型已删除', 'success')
  } catch {
    appStore.showToast('删除失败', 'error')
  }
}

onMounted(loadModels)
</script>

<template>
  <div>
    <div class="main-header">
      <div class="main-header-title">AI 写作</div>
      <div class="main-header-actions">
        <button class="btn btn-secondary btn-sm" @click="loadModels">刷新</button>
        <button class="btn btn-primary btn-sm" @click="showModelForm = !showModelForm">添加模型</button>
      </div>
    </div>

    <div class="main-content" v-if="!loading">
      <!-- 模型选择 -->
      <div class="card" style="margin-bottom: 16px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
          <h3 style="font-size: 15px; font-weight: 600;">AI 模型</h3>
          <button class="btn btn-secondary btn-sm" :disabled="testing || !selectedModelId" @click="handleTestModel">
            <span v-if="testing" class="spinner" style="width: 12px; height: 12px;"></span>
            {{ testing ? '测试中...' : '测试连接' }}
          </button>
        </div>
        <div v-if="models.length === 0" class="empty-state" style="padding: 16px;">
          <div class="empty-state-description">尚未配置 AI 模型，点击「添加模型」开始</div>
        </div>
        <div v-else style="display: flex; flex-direction: column; gap: 8px;">
          <div
            v-for="model in models"
            :key="model.id"
            class="list-item"
            :style="{ border: selectedModelId === model.id ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)' }"
            @click="selectedModelId = model.id"
          >
            <div class="list-item-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M12 2a7 7 0 1 1 0 14 7 7 0 0 1 0-14z" stroke="currentColor" stroke-width="1.5"/>
              </svg>
            </div>
            <div class="list-item-content">
              <div class="list-item-title">{{ model.name }} <span v-if="model.isDefault" class="badge badge-info">默认</span></div>
              <div class="list-item-meta">{{ model.provider }} · {{ model.modelId }}</div>
            </div>
            <div class="list-item-actions">
              <button class="btn btn-ghost btn-sm" style="color: var(--status-error);" @click.stop="handleDeleteModel(model)">删除</button>
            </div>
          </div>
        </div>

        <!-- 添加模型表单 -->
        <div v-if="showModelForm" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-subtle);">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div><label style="font-size: 13px; font-weight: 500;">名称</label><input class="input" v-model="modelForm.name" placeholder="如：GPT-4o" /></div>
            <div><label style="font-size: 13px; font-weight: 500;">提供商</label>
              <select class="select" v-model="modelForm.provider">
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="deepseek">DeepSeek</option>
                <option value="custom">自定义</option>
              </select>
            </div>
            <div><label style="font-size: 13px; font-weight: 500;">模型ID</label><input class="input" v-model="modelForm.modelId" placeholder="如：gpt-4o" /></div>
            <div><label style="font-size: 13px; font-weight: 500;">API 地址</label><input class="input" v-model="modelForm.baseUrl" placeholder="https://api.openai.com/v1" /></div>
            <div style="grid-column: 1 / -1;"><label style="font-size: 13px; font-weight: 500;">API Key</label><input class="input" v-model="modelForm.apiKey" type="password" placeholder="sk-..." /></div>
            <div style="display: flex; gap: 16px; align-items: center;">
              <label style="display: flex; align-items: center; gap: 6px; font-size: 13px;"><input type="checkbox" v-model="modelForm.is_default" /> 设为默认</label>
            </div>
          </div>
          <div style="margin-top: 12px; display: flex; gap: 8px;">
            <button class="btn btn-primary btn-sm" @click="handleSaveModel">保存</button>
            <button class="btn btn-secondary btn-sm" @click="showModelForm = false">取消</button>
          </div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <!-- 草稿生成 -->
        <div class="card">
          <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px;">生成草稿</h3>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <div>
              <label style="font-size: 13px; font-weight: 500; display: block; margin-bottom: 4px;">文章类型</label>
              <select class="select" v-model="draftForm.type">
                <option value="docs">知识库</option>
                <option value="blog">博客</option>
              </select>
            </div>
            <div>
              <label style="font-size: 13px; font-weight: 500; display: block; margin-bottom: 4px;">标题</label>
              <input class="input" v-model="draftForm.title" placeholder="文章标题" />
            </div>
            <div>
              <label style="font-size: 13px; font-weight: 500; display: block; margin-bottom: 4px;">大纲（每行一个要点）</label>
              <textarea class="textarea" v-model="draftForm.outline" placeholder="概述&#10;背景&#10;实现方案" style="min-height: 100px;" />
            </div>
            <div>
              <label style="font-size: 13px; font-weight: 500; display: block; margin-bottom: 4px;">参考资料（每行一个 URL）</label>
              <textarea class="textarea" v-model="draftForm.references" placeholder="https://..." style="min-height: 60px;" />
            </div>
            <div>
              <label style="font-size: 13px; font-weight: 500; display: block; margin-bottom: 4px;">目标风格</label>
              <input class="input" v-model="draftForm.targetStyle" placeholder="技术博客" />
            </div>
            <button class="btn btn-primary" :disabled="generating" @click="handleGenerate">
              <span v-if="generating" class="spinner" style="width: 12px; height: 12px;"></span>
              {{ generating ? '生成中...' : '生成草稿' }}
            </button>
          </div>
          <div v-if="draftResult" style="margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border-subtle);">
            <div style="font-size: 13px; font-weight: 600; margin-bottom: 8px;">生成结果</div>
            <div class="code-block" style="white-space: pre-wrap; max-height: 400px; overflow-y: auto;">{{ draftResult.body }}</div>
          </div>
        </div>

        <!-- 内容改写 -->
        <div class="card">
          <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px;">内容改写</h3>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <div>
              <label style="font-size: 13px; font-weight: 500; display: block; margin-bottom: 4px;">原始内容</label>
              <textarea class="textarea" v-model="rewriteForm.content" placeholder="粘贴要改写的内容..." style="min-height: 150px;" />
            </div>
            <div>
              <label style="font-size: 13px; font-weight: 500; display: block; margin-bottom: 4px;">改写指令</label>
              <input class="input" v-model="rewriteForm.instruction" placeholder="如：更简洁、更口语化" />
            </div>
            <button class="btn btn-primary" :disabled="rewriting" @click="handleRewrite">
              <span v-if="rewriting" class="spinner" style="width: 12px; height: 12px;"></span>
              {{ rewriting ? '改写中...' : '执行改写' }}
            </button>
          </div>
          <div v-if="rewriteResult" style="margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border-subtle);">
            <div style="font-size: 13px; font-weight: 600; margin-bottom: 8px;">改写结果</div>
            <div v-if="rewriteResult.changes.length > 0" style="margin-bottom: 8px;">
              <div v-for="(change, i) in rewriteResult.changes" :key="i" style="font-size: 12px; color: var(--text-secondary); margin-bottom: 2px;">· {{ change }}</div>
            </div>
            <div class="code-block" style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{{ rewriteResult.content }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else style="display: flex; align-items: center; justify-content: center; height: 300px;">
      <div class="spinner" style="width: 24px; height: 24px;"></div>
    </div>
  </div>
</template>
