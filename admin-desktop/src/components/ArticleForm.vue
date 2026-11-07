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
  <section class="card article-form">
    <button type="button" class="btn btn-secondary btn-sm" :aria-expanded="visible" :disabled="busy" @click="toggle">
      {{ visible ? '收起文章信息' : '编辑文章信息' }}
    </button>
    <template v-if="visible">
      <p v-if="busy" role="status">正在读取或应用表单…</p>
      <p v-if="error" role="alert">{{ error }}</p>
      <p v-if="stale" role="status">源码已有新修改。重新读取后再应用表单。</p>
      <button v-if="stale || (!fields && !busy)" type="button" class="btn btn-secondary btn-sm" :disabled="busy" @click="load">从源码重新读取</button>
      <form v-if="fields" class="article-form-fields" @submit.prevent="apply">
        <label>标题<input v-model="fields.title" class="input" :disabled="busy" /></label>
        <label>摘要<textarea v-model="fields.description" class="input" rows="2" :disabled="busy" /></label>
        <label>标签（每行一个）<textarea v-model="tags" class="input" rows="3" :disabled="busy" /></label>
        <label class="article-pin"><input v-model="fields.sticky" type="checkbox" :disabled="busy" /> 置顶</label>
        <div>
          <button class="btn btn-primary btn-sm" type="submit" :disabled="stale || busy">应用到源码</button>
          <span class="article-form-note">应用后请使用编辑器的「保存」。</span>
        </div>
      </form>
    </template>
  </section>
</template>

<style scoped>
.article-form { margin-bottom: 12px; }
.article-form-fields { margin-top: 12px; display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); }
.article-form-fields label { display: grid; align-content: start; gap: 5px; }
.article-form-fields .article-pin { display: flex; align-items: center; }
.article-form-note { margin-inline-start: 8px; color: var(--text-secondary); }
</style>
