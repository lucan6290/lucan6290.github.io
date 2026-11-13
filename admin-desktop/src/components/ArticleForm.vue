<script setup lang="ts">
import { computed, ref } from 'vue'
import { request } from '@/api/content'

interface Fields { title: string; description: string; tags: string[]; sticky: boolean }
const props = defineProps<{ text: string }>()
const emit = defineEmits<{ apply: [before: string, after: string] }>()
const visible = ref(false)
const fields = ref<Fields | null>(null)
const tags = ref('')
const initial = ref('')
const source = ref('')
const error = ref('')
const busy = ref(false)
const stale = computed(() => fields.value !== null && props.text !== source.value)
const valuesKey = () => JSON.stringify([fields.value?.title, fields.value?.description, fields.value?.sticky, tags.value])
const hasUnapplied = () => fields.value !== null && valuesKey() !== initial.value
const allowDiscard = () => !hasUnapplied() || window.confirm('文章表单还有未应用的内容。放弃表单修改？')
function discard() { fields.value = null; visible.value = false }
defineExpose({ hasUnapplied, allowDiscard, discard })

async function load() {
  const before = props.text
  busy.value = true
  error.value = ''
  try {
    const result = await request<Fields>('/api/v1/article-form/read', 'POST', { raw_content: before })
    source.value = before
    fields.value = result
    tags.value = result.tags.join('\n')
    initial.value = valuesKey()
  } catch (cause) {
    fields.value = null
    error.value = cause instanceof Error ? cause.message : '无法读取表单字段'
  } finally { busy.value = false }
}

function toggle() {
  if (visible.value && !allowDiscard()) return
  visible.value = !visible.value
  if (visible.value) void load()
}

async function apply() {
  if (!fields.value || stale.value) return
  const before = source.value
  const nextTags = tags.value === fields.value.tags.join('\n') ? fields.value.tags : tags.value.split('\n').map(tag => tag.trim()).filter(Boolean)
  busy.value = true
  error.value = ''
  try {
    const result = await request<{ raw_content: string }>('/api/v1/article-form/patch', 'POST', {
      raw_content: before,
      values: { ...fields.value, tags: nextTags },
    })
    if (props.text !== before) return
    emit('apply', before, result.raw_content)
    source.value = result.raw_content
    fields.value.tags = nextTags
    tags.value = nextTags.join('\n')
    initial.value = valuesKey()
  } catch (cause) { error.value = cause instanceof Error ? cause.message : '无法更新表单字段' }
  finally { busy.value = false }
}
</script>

<template>
  <section class="card article-form" aria-label="文章信息">
    <div class="article-form-header">
      <button type="button" class="article-form-toggle" :aria-expanded="visible" :disabled="busy" @click="toggle">
        <svg aria-hidden="true" viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m6 4 4 4-4 4" /></svg>
        文章信息
      </button>
      <slot name="purpose" />
    </div>
    <template v-if="visible">
      <div class="article-form-body">
        <p v-if="busy" role="status">正在读取或应用表单…</p>
        <p v-if="error" role="alert">{{ error }}</p>
        <p v-if="stale" role="status">源码已有新修改。重新读取后再应用表单。</p>
        <button v-if="stale || (!fields && !busy)" type="button" class="btn btn-secondary btn-sm" :disabled="busy" @click="load">从源码重新读取</button>
        <form v-if="fields" class="article-form-fields" @submit.prevent="apply">
          <label class="article-title">标题<input v-model="fields.title" class="input" :disabled="busy" /></label>
          <div class="article-field">
            <label>摘要<textarea v-model="fields.description" class="input" rows="4" :disabled="busy" /></label>
          </div>
          <div class="article-field">
            <label><span class="article-label">标签 <small>每行一个</small></span><textarea v-model="tags" class="input" rows="3" :disabled="busy" /></label>
          </div>
          <div class="article-form-footer">
            <label class="article-pin"><input v-model="fields.sticky" type="checkbox" :disabled="busy" /> 置顶</label>
            <div class="article-form-actions">
              <span class="article-form-note">应用后请使用编辑器的「保存」。</span>
              <button class="btn btn-primary btn-sm" type="submit" :disabled="stale || busy">应用到源码</button>
            </div>
          </div>
        </form>
      </div>
    </template>
  </section>
</template>

<style scoped>
.article-form { margin-bottom: 12px; padding: 0; container-type: inline-size; }
.article-form-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px 16px; min-height: 48px; padding: 8px 16px; }
.article-form-toggle { display: inline-flex; align-items: center; gap: 6px; padding: 4px 6px; border: 0; border-radius: 6px; background: transparent; color: var(--text-primary); font: inherit; font-weight: 600; cursor: pointer; }
.article-form-toggle:hover:not(:disabled) { background: var(--bg-element-hover); }
.article-form-toggle[aria-expanded='true'] svg { transform: rotate(90deg); }
.article-form-body { padding: 14px 16px 0; border-top: 1px solid var(--border-subtle); }
.article-form-body > p { margin: 0 0 10px; }
.article-form-fields { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 14px 16px; }
.article-form-fields label { display: grid; align-content: start; gap: 6px; font-size: 13px; }
.article-title, .article-form-footer { grid-column: 1 / -1; }
.article-field { min-width: 0; }
.article-field textarea { resize: vertical; line-height: 1.5; }
.article-label small { margin-inline-start: 4px; color: var(--text-secondary); font-size: 12px; }
.article-form-footer { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px 16px; padding: 10px 0 12px; border-top: 1px solid var(--border-subtle); }
.article-form-fields .article-pin, .article-form-actions { display: flex; align-items: center; }
.article-form-actions { flex-wrap: wrap; justify-content: flex-end; gap: 8px 12px; margin-inline-start: auto; }
.article-form-note { color: var(--text-secondary); font-size: 12px; }
@container (max-width: 540px) {
  .article-form-fields { grid-template-columns: minmax(0, 1fr); }
}
</style>
