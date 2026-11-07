<script setup lang="ts">
import { ref, watch } from 'vue'
import type { DirectoryNode } from '@/types/content'

const props = defineProps<{ nodes: DirectoryNode[]; selected: string }>()
const emit = defineEmits<{ select: [path: string] }>()
const expanded = ref(new Set<string>())
watch(() => props.selected, (path) => {
  const parts = path.split('/')
  while (parts.length > 1) {
    parts.pop()
    expanded.value.add(parts.join('/'))
  }
}, { immediate: true })

function toggle(path: string) {
  if (expanded.value.has(path)) expanded.value.delete(path)
  else expanded.value.add(path)
}
</script>

<template>
  <ul class="directory-branches">
    <li v-for="node in nodes" :key="node.relative_path">
      <div class="directory-branch">
        <button v-if="node.children.length" type="button" class="btn btn-ghost btn-sm branch-toggle"
          :aria-expanded="expanded.has(node.relative_path)" :aria-label="`${expanded.has(node.relative_path) ? '收起' : '展开'} ${node.label}`"
          @click="toggle(node.relative_path)">{{ expanded.has(node.relative_path) ? '▾' : '▸' }}</button>
        <button type="button" class="btn btn-ghost btn-sm branch-label" :class="{ 'branch-leaf': !node.children.length }"
          :aria-current="selected === node.relative_path ? 'true' : undefined" @click="emit('select', node.relative_path)">{{ node.label }}</button>
      </div>
      <DirectoryBranch v-if="node.children.length && expanded.has(node.relative_path)" :nodes="node.children" :selected="selected"
        @select="emit('select', $event)" />
    </li>
  </ul>
</template>

<style scoped>
.directory-branches { list-style: none; padding: 0; margin: 0; }
li > .directory-branches { padding-inline-start: 16px; }
.directory-branch { display: flex; min-width: 0; align-items: baseline; }
.branch-toggle { width: 26px; flex: 0 0 26px; padding-inline: 0; }
.branch-label { text-align: start; white-space: normal; overflow-wrap: anywhere; min-width: 0; }
.branch-leaf { margin-inline-start: 26px; }
.branch-label[aria-current='true'] { font-weight: 700; background: var(--bg-hover); }
</style>
