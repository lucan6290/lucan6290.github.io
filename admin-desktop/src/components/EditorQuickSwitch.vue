<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { contentApi } from '@/api/content'
import type { DocumentSummary } from '@/types/content'
import { favorites, toggleFavorite } from '@/utils/editorFavorites'

const props = defineProps<{ path: string | null }>()
const emit = defineEmits<{ navigate: [path: string] }>()
const visible = ref(false)
const query = ref('')
const input = ref<HTMLInputElement | null>(null)
const results = ref<DocumentSummary[]>([])
const loading = ref(false)
const error = ref('')
const pinned = computed(() => !!props.path && favorites.value.includes(props.path))

async function open() {
  visible.value = true
  await nextTick()
  input.value?.focus()
}
defineExpose({ open })

watch([visible, query], ([show, search], _previous, cleanup) => {
  results.value = []
  loading.value = false
  error.value = ''
  if (!show || !search.trim()) return
  let current = true
  loading.value = true
  const timer = setTimeout(async () => {
    try {
      const index = await contentApi.list(search.trim())
      if (current) results.value = index.documents.slice(0, 20)
    } catch (cause) {
      if (current) error.value = cause instanceof Error ? cause.message : '无法搜索文档'
    } finally { if (current) loading.value = false }
  }, 160)
  cleanup(() => { current = false; clearTimeout(timer) })
})

function go(path: string) {
  visible.value = false
  query.value = ''
  emit('navigate', path)
}
</script>

<template>
  <div class="quick-switch">
    <div class="quick-actions">
      <button class="btn btn-secondary btn-sm" type="button" title="Ctrl+P" :aria-expanded="visible" @click="visible ? visible = false : open()">快速切换</button>
      <button v-if="path" class="btn btn-secondary btn-sm" type="button" :aria-pressed="pinned" @click="toggleFavorite(path)">
        {{ pinned ? '取消收藏' : '收藏此文档' }}
      </button>
    </div>
    <section v-if="visible" class="card quick-results" aria-label="快速切换文档" @keydown.esc.stop="visible = false">
      <form @submit.prevent="results[0] && go(results[0].relative_path)">
        <label>搜索文档
          <input ref="input" v-model="query" class="input" maxlength="200" placeholder="输入标题、路径或正文关键词" />
        </label>
      </form>
      <p v-if="loading" role="status">搜索中…</p>
      <p v-else-if="error" role="alert">{{ error }}</p>
      <p v-else-if="query.trim() && !results.length">没有匹配的文档。</p>
      <ul v-else-if="query.trim()">
        <li v-for="document in results" :key="document.relative_path">
          <button class="btn btn-ghost btn-sm" @click="go(document.relative_path)">{{ document.title }} · {{ document.relative_path }}</button>
        </li>
      </ul>
      <template v-else>
        <h3>收藏</h3>
        <ul v-if="favorites.length">
          <li v-for="item in favorites" :key="item">
            <button class="btn btn-ghost btn-sm" @click="go(item)">{{ item }}</button>
            <button class="btn btn-ghost btn-sm" :aria-label="'取消收藏 ' + item" @click="toggleFavorite(item)">×</button>
          </li>
        </ul>
        <p v-else>还没有收藏。</p>
      </template>
    </section>
  </div>
</template>

<style scoped>
.quick-switch { margin-bottom: 12px; }
.quick-actions { display: flex; gap: 8px; }
.quick-results { margin-top: 8px; overflow-wrap: anywhere; }
.quick-results form { max-width: 36rem; }
.quick-results li button { text-align: start; white-space: normal; }
</style>
