<template>
  <nav class="breadcrumbs" aria-label="面包屑">
    <ol>
      <li><router-link :to="root">{{ rootLabel }}</router-link></li>
      <li v-for="(seg, i) in segments" :key="i">
        <span class="sep" aria-hidden="true">/</span>
        <router-link v-if="i < segments.length - 1" :to="seg.to">{{ seg.label }}</router-link>
        <span v-else aria-current="page">{{ seg.label }}</span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ path: string; root: string }>();

const rootLabel = computed(() => props.root === '/blog' ? '博客' : '知识库');

const segments = computed(() => {
  const rel = props.path.replace(props.root, '').replace(/^\/+|\/+$/g, '');
  if (!rel) return [];
  const parts = rel.split('/').filter(Boolean);
  return parts.map((p, i) => ({
    label: decodeURIComponent(p),
    to: props.root + '/' + parts.slice(0, i + 1).join('/'),
  }));
});
</script>

<style scoped>
.breadcrumbs { margin-bottom: 16px; color: var(--site-text-muted); font-size: 0.88rem; }
.breadcrumbs ol { list-style: none; display: flex; flex-wrap: wrap; gap: 4px; padding: 0; margin: 0; }
.breadcrumbs a { color: var(--site-text-muted); }
.breadcrumbs a:hover { color: var(--ifm-color-primary); }
.sep { margin: 0 2px; opacity: 0.6; }
</style>
