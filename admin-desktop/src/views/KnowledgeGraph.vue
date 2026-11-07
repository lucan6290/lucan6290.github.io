<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { contentMoves, type ContentGraph } from '@/api/contentMoves'

const route = useRoute()
const graph = ref<ContentGraph | null>(null)
const focus = ref('')
const error = ref('')
const loading = ref(false)
const center = { x: 360, y: 210 }
const edges = computed(() => graph.value?.edges.filter(edge => edge.source === focus.value || edge.target === focus.value) ?? [])
const neighborPaths = computed(() => [...new Set(edges.value.map(edge => edge.source === focus.value ? edge.target : edge.source))])
const nodes = computed(() => neighborPaths.value.map((path, index) => {
  const angle = index * 2 * Math.PI / neighborPaths.value.length - Math.PI / 2
  return { path, x: center.x + 260 * Math.cos(angle), y: center.y + 155 * Math.sin(angle) }
}))

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    graph.value = await contentMoves.links()
    const requested = typeof route.query.document === 'string' ? route.query.document : ''
    if (!graph.value.documents.includes(focus.value)) {
      focus.value = graph.value.documents.includes(requested) ? requested : graph.value.documents[0] || ''
    }
  } catch (cause) { error.value = cause instanceof Error ? cause.message : '无法读取知识图谱' }
  finally { loading.value = false }
}
onMounted(refresh)
</script>

<template>
  <div>
    <header class="main-header">
      <h1 class="main-header-title">知识图谱</h1>
      <div class="main-header-actions"><button class="btn btn-secondary btn-sm" :disabled="loading" @click="refresh">刷新</button></div>
    </header>
    <div class="main-content">
      <p v-if="error" role="alert">{{ error }}</p>
      <p v-if="loading" role="status">正在读取 Markdown 链接…</p>
      <template v-if="graph">
        <p>{{ graph.documents.length }} 篇文档，{{ graph.edges.length }} 条链接。选择文档查看直接连接。</p>
        <label class="graph-select">中心文档
          <select v-model="focus" class="select">
            <option v-for="path in graph.documents" :key="path" :value="path">{{ path }}</option>
          </select>
        </label>
        <div v-if="focus" class="card graph-body">
          <svg viewBox="0 0 720 420" role="img" aria-label="中心文档及直接链接节点">
            <line v-for="node in nodes" :key="node.path" :x1="center.x" :y1="center.y" :x2="node.x" :y2="node.y" />
            <g v-for="(node, index) in nodes" :key="node.path" :transform="'translate(' + node.x + ' ' + node.y + ')'">
              <title>{{ node.path }}</title>
              <circle r="15" />
              <text text-anchor="middle" y="5">{{ index + 1 }}</text>
            </g>
            <circle class="graph-center" :cx="center.x" :cy="center.y" r="22" />
            <text :x="center.x" :y="center.y + 4" text-anchor="middle">中心</text>
          </svg>
          <RouterLink :to="{ name: 'Editor', query: { id: focus } }">{{ focus }}</RouterLink>
          <p v-if="!nodes.length">此文档暂无直接连接。</p>
          <ol v-else class="graph-neighbors">
            <li v-for="node in nodes" :key="node.path">
              <button class="btn btn-ghost btn-sm" type="button" @click="focus = node.path">{{ node.path }}</button>
              <span v-if="edges.some(edge => edge.source === node.path)">链接到中心</span>
              <span v-if="edges.some(edge => edge.target === node.path)">由中心链接</span>
            </li>
          </ol>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.graph-select { display: grid; gap: 8px; max-width: 36rem; }
.graph-body { margin-top: 12px; overflow-wrap: anywhere; }
.graph-body svg { display: block; width: 100%; max-height: 48vh; }
.graph-body line { stroke: var(--border-subtle); stroke-width: 2; }
.graph-body circle { fill: var(--bg-panel); stroke: var(--text-secondary); }
.graph-body .graph-center { stroke: var(--text-primary); stroke-width: 2; }
.graph-body text { fill: var(--text-primary); font-size: 11px; }
.graph-neighbors span { margin-inline-start: 8px; font-size: 12px; color: var(--text-secondary); }
</style>
