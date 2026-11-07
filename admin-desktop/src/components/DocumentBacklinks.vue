<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { contentMoves, type ContentGraph } from '@/api/contentMoves'

const props = defineProps<{ path: string }>()
const graph = ref<ContentGraph | null>(null)
const expanded = ref(false)
const error = ref('')
const incoming = computed(() => graph.value?.edges.filter(edge => edge.target === props.path) ?? [])

watch([() => props.path, expanded], ([path, open], _previous, cleanup) => {
  graph.value = null
  error.value = ''
  if (!open || !path) return
  let current = true
  cleanup(() => { current = false })
  void contentMoves.links().then(result => { if (current) graph.value = result }).catch(cause => {
    if (current) error.value = cause instanceof Error ? cause.message : '无法读取链接'
  })
})
</script>

<template>
  <details class="card backlinks" @toggle="expanded = ($event.target as HTMLDetailsElement).open">
    <summary>反向链接{{ graph ? '（' + incoming.length + '）' : '' }}</summary>
    <p v-if="error" role="alert">{{ error }}</p>
    <p v-else-if="!graph" role="status">正在读取链接…</p>
    <p v-else-if="!incoming.length">暂无其他文档链接到此处。</p>
    <ul v-else>
      <li v-for="edge in incoming" :key="edge.source">
        <RouterLink :to="{ name: 'Editor', query: { id: edge.source } }">{{ edge.source }}</RouterLink>
      </li>
    </ul>
    <RouterLink class="btn btn-secondary btn-sm" :to="{ name: 'KnowledgeGraph', query: { document: path } }">在知识图谱查看</RouterLink>
  </details>
</template>

<style scoped>
.backlinks { margin-top: 12px; overflow-wrap: anywhere; }
.backlinks a { color: var(--text-primary); }
.backlinks .btn { margin-top: 8px; }
</style>
