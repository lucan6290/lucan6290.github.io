<template>
  <nav class="prev-next" aria-label="上一篇/下一篇">
    <router-link v-if="prev" class="pn-link pn-prev" :to="contentHref(prev.path)">
      <span class="sublabel">← 上一篇</span>
      <span class="label">{{ prev.title }}</span>
    </router-link>
    <span v-else />
    <router-link v-if="next" class="pn-link pn-next" :to="contentHref(next.path)">
      <span class="sublabel">下一篇 →</span>
      <span class="label">{{ next.title }}</span>
    </router-link>
  </nav>
</template>

<script setup lang="ts">
import { contentHref } from '@/composables/contentPaths';
defineProps<{
  prev: { path: string; title: string } | null;
  next: { path: string; title: string } | null;
}>();
</script>

<style scoped>
.prev-next {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 48px;
  padding-top: 24px;
  border-top: 1px solid var(--site-border);
}
.pn-link {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 20px;
  border: 1px solid var(--site-border);
  border-radius: 8px;
  text-decoration: none;
  min-width: 0;
  flex: 1;
  transition: border-color 180ms, background 180ms;
}
.pn-link:hover { border-color: var(--ifm-color-primary); background: var(--site-accent-soft); }
.pn-next { align-items: flex-end; text-align: right; }
.sublabel { color: var(--site-text-muted); font-size: 0.85rem; }
.label { color: var(--ifm-color-primary); font-size: 1rem; font-weight: 600; word-break: break-word; }
</style>
