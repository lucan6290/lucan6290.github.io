<template>
  <main class="page-shell">
    <section class="simple-page">
      <p class="eyebrow">Tags</p>
      <h1>标签索引</h1>
      <div v-if="entries.length" class="tag-cloud">
        <router-link v-for="e in entries" :key="e.tag" :to="`/tags/${encodeURIComponent(e.tag)}`" class="tag-pill">
          {{ e.tag }} <span class="count">{{ e.count }}</span>
        </router-link>
      </div>
      <p v-else class="empty">暂无标签。</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useContent } from '@/composables/useContent';

const { getAllTags } = useContent();
const entries = computed(() =>
  Object.entries(getAllTags())
    .map(([tag, paths]) => ({ tag, count: paths.length }))
    .sort((a, b) => b.count - a.count),
);
</script>

<style scoped>
.page-shell { min-height: calc(100vh - var(--ifm-navbar-height)); padding: 64px 24px 96px; background: var(--site-background); }
.simple-page { width: min(880px, 100%); margin: 0 auto; }
.eyebrow { margin: 0 0 12px; color: var(--ifm-color-primary); font-size: 0.82rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.simple-page h1 { margin: 0 0 32px; color: var(--site-text); font-size: clamp(2rem, 4vw, 3.2rem); line-height: 1.12; }
.tag-cloud { display: flex; flex-wrap: wrap; gap: 12px; }
.tag-pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 16px; border: 1px solid var(--site-border); border-radius: 999px;
  background: var(--site-surface); color: var(--site-text); font-size: 0.92rem; font-weight: 500;
  text-decoration: none; transition: border-color 180ms, background 180ms;
}
.tag-pill:hover { border-color: var(--ifm-color-primary); background: var(--site-accent-soft); }
.count { color: var(--site-text-muted); font-size: 0.78rem; font-weight: 700; }
.empty { color: var(--site-text-muted); }
</style>
