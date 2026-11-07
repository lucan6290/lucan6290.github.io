<script setup lang="ts">
import { ref } from 'vue'
import { ContentApiError } from '@/api/content'
import { contentMoves, type MoveKind, type MovePlan } from '@/api/contentMoves'

const props = defineProps<{ source: string; kind: MoveKind }>()
const emit = defineEmits<{ close: []; moved: [plan: MovePlan] }>()
const target = ref(props.source)
const plan = ref<MovePlan | null>(null)
const busy = ref(false)
const error = ref('')

function showError(cause: unknown) {
  error.value = cause instanceof Error ? cause.message : '移动请求失败'
  if (cause instanceof ContentApiError && cause.details) error.value += ' ' + JSON.stringify(cause.details)
}

async function preview() {
  plan.value = null
  error.value = ''
  busy.value = true
  try { plan.value = await contentMoves.plan(props.source, target.value.trim(), props.kind) }
  catch (cause) { showError(cause) }
  finally { busy.value = false }
}

async function apply() {
  if (!plan.value) return
  busy.value = true
  error.value = ''
  try { emit('moved', await contentMoves.apply(plan.value)) }
  catch (cause) { plan.value = null; showError(cause) }
  finally { busy.value = false }
}
</script>

<template>
  <div class="move-overlay" @keydown.esc="!busy && emit('close')">
    <section class="card move-dialog" role="dialog" aria-modal="true" aria-labelledby="move-dialog-title">
      <h2 id="move-dialog-title">移动或重命名{{ kind === 'directory' ? '目录' : '文档' }}</h2>
      <p>源路径 <code>{{ source }}</code></p>
      <form class="move-form" @submit.prevent="preview">
        <label>新的内容库相对路径
          <input v-model="target" class="input" :disabled="busy" required @input="plan = null" />
        </label>
        <button class="btn btn-secondary" type="submit" :disabled="busy || target.trim() === source">查看影响</button>
      </form>
      <p v-if="error" role="alert">{{ error }}</p>
      <p v-if="busy" role="status">正在检查或移动，请稍候…</p>
      <template v-if="plan">
        <p>将移动 {{ plan.moves.length }} 个路径，涉及 {{ plan.files.length }} 个文件。</p>
        <ul><li v-for="item in plan.moves" :key="item.before"><code>{{ item.before }} → {{ item.after }}</code></li></ul>
        <details :open="plan.files.length < 10">
          <summary>受影响文件（{{ plan.files.length }}）</summary>
          <ul><li v-for="item in plan.files" :key="item.before">
            <code>{{ item.before }}{{ item.after === item.before ? '' : ' → ' + item.after }}</code>
            {{ item.rewritten ? ' · 更新 Markdown 引用' : '' }}
          </li></ul>
        </details>
        <details v-if="plan.routes.length" :open="plan.routes.length < 10">
          <summary>博客 URL 变化（{{ plan.routes.length }}）</summary>
          <ul><li v-for="item in plan.routes" :key="item.before"><code>{{ item.before }} → {{ item.after }}</code></li></ul>
        </details>
      </template>
      <div class="move-actions">
        <button class="btn btn-secondary" type="button" :disabled="busy" @click="emit('close')">取消</button>
        <button v-if="plan" class="btn btn-primary" type="button" :disabled="busy" @click="apply">确认移动</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.move-overlay { position: fixed; inset: 0; display: grid; place-items: center; z-index: 1000; padding: 24px; background: rgba(0, 0, 0, .45); }
.move-dialog { width: min(720px, 100%); max-height: 85vh; overflow: auto; background: var(--bg-panel); overflow-wrap: anywhere; }
.move-form { display: flex; align-items: end; gap: 8px; }
.move-form label { flex: 1; min-width: 0; }
.move-dialog details { margin: 10px 0; }
.move-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
</style>
