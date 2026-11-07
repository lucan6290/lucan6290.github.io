<script setup lang="ts">
import { onBeforeUnmount, ref, shallowReactive, watch } from 'vue'
import { aiErrorMessage, aiWritingApi } from '@/api/aiWriting'
import { AiDraftError, AiDraftSession, type AiOperation } from '@/utils/aiDraft'

const props = defineProps<{ buffer: string; documentKey: string | number }>()
const emit = defineEmits<{ accept: [next: string] }>()
const draft = shallowReactive(new AiDraftSession())
const instruction = ref('')
const error = ref('')
const notice = ref('')

watch(() => [props.buffer, props.documentKey] as const, ([, key], [, oldKey]) => {
  if (draft.pending || draft.suggestion) notice.value = '正文或文档已变化，旧建议已丢弃。'
  draft.invalidate()
  error.value = ''
  if (key !== oldKey) instruction.value = ''
}, { flush: 'sync' })
onBeforeUnmount(() => draft.invalidate())

async function compose(operation: AiOperation) {
  error.value = ''
  notice.value = ''
  const prompt = instruction.value.trim()
  if (!prompt) return

  let snapshot: ReturnType<AiDraftSession['begin']>
  try {
    snapshot = draft.begin(operation, props.buffer, props.documentKey)
  } catch (cause) {
    error.value = cause instanceof AiDraftError ? cause.message : '无法读取当前正文。'
    return
  }

  try {
    const body = snapshot.operation === 'rewrite' ? snapshot.before : undefined
    const result = await aiWritingApi.compose(snapshot.operation, prompt, body)
    draft.complete(snapshot, result.markdown)
  } catch (cause) {
    if (!draft.isCurrent(snapshot)) return
    draft.invalidate()
    error.value = cause instanceof AiDraftError
      ? cause.message
      : aiErrorMessage(cause, '无法获取建议，请检查本机服务或 AI 设置。')
  }
}

function accept() {
  const next = draft.accept(props.buffer, props.documentKey)
  if (next === null) return
  emit('accept', next)
  notice.value = '已更新编辑缓冲，点击编辑器的「保存」写入文档。'
}

function discard() {
  draft.invalidate()
  notice.value = '建议已丢弃。'
}
</script>

<template>
  <details class="card ai-writing-panel">
    <summary>AI 写作</summary>
    <div class="ai-writing-content">
      <p class="ai-hint">生成发送写作要求，改写还会将当前正文发送至配置的 AI 服务。<RouterLink to="/ai-writing">服务设置</RouterLink></p>
      <label class="ai-instruction">
        写作要求
        <textarea v-model="instruction" class="input" rows="3" maxlength="4000" placeholder="例如：将正文缩成三段，保留术语和代码示例" />
      </label>
      <div class="ai-actions">
        <button class="btn btn-primary" type="button" :disabled="draft.pending || !instruction.trim()" @click="compose('generate')">生成草稿</button>
        <button class="btn btn-secondary" type="button" :disabled="draft.pending || !instruction.trim()" @click="compose('rewrite')">改写正文</button>
        <span v-if="draft.pending" role="status">等待 AI 服务…</span>
      </div>
      <p v-if="error" class="ai-error" role="alert">{{ error }}</p>
      <p v-if="notice" class="ai-hint" role="status">{{ notice }}</p>
      <div v-if="draft.suggestion" class="ai-review">
        <div class="ai-comparison">
          <section aria-label="当前正文">
            <strong>当前正文</strong>
            <pre>{{ draft.suggestion.before || '（空正文）' }}</pre>
          </section>
          <section aria-label="建议正文">
            <strong>建议正文</strong>
            <pre>{{ draft.suggestion.after }}</pre>
          </section>
        </div>
        <div class="ai-actions">
          <button class="btn btn-primary" type="button" @click="accept">采用建议</button>
          <button class="btn btn-secondary" type="button" @click="discard">丢弃建议</button>
        </div>
      </div>
    </div>
  </details>
</template>

<style scoped>
.ai-writing-panel { margin-bottom: 16px; }
.ai-writing-panel summary { cursor: pointer; font-weight: 600; }
.ai-writing-content { display: grid; gap: 12px; margin-top: 12px; }
.ai-hint, .ai-error { margin: 0; }
.ai-hint { color: var(--text-secondary); }
.ai-error { color: var(--status-error); }
.ai-instruction { display: grid; gap: 6px; }
.ai-instruction textarea { height: auto; min-height: 80px; resize: vertical; }
.ai-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.ai-review { display: grid; gap: 12px; padding-top: 12px; border-top: 1px solid var(--border-subtle); }
.ai-comparison { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.ai-comparison section { padding: 12px; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); }
.ai-comparison pre { margin: 8px 0 0; max-height: 280px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font-family: var(--font-mono); }
@media (max-width: 720px) { .ai-comparison { grid-template-columns: 1fr; } }
</style>