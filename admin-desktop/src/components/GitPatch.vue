<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ patch: string }>()
const lines = computed(() => props.patch.replace(/\n$/, '').split('\n').map(line => {
  const style = line.startsWith('@@') ? 'range' :
    line.startsWith('+') && !line.startsWith('+++ ') ? 'add' :
    line.startsWith('-') && !line.startsWith('--- ') ? 'remove' : undefined
  return { line, style }
}))
</script>

<template>
  <pre v-if="patch" class="git-patch" tabindex="0" aria-label="Git 差异内容"><code><span v-for="({ line, style }, index) in lines" :key="index" :class="style">{{ line || ' ' }}</span></code></pre>
</template>

<style scoped>
.git-patch {
  max-height: 22rem;
  overflow: auto;
  padding: 0.5rem 0;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--bg-app);
  font: 0.82rem/1.5 var(--font-mono);
}
.git-patch code { display: block; min-width: max-content; }
.git-patch span { display: block; padding-inline: 0.75rem; }
.add { background: var(--success-soft-bg); }
.remove { background: var(--danger-soft-bg); }
.range { color: var(--text-secondary); }
</style>
