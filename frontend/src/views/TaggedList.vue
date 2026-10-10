<template>
  <main class="page-shell">
    <section class="simple-page">
      <p class="eyebrow">Tag</p>
      <h1>#{{ tag }}</h1>
      <ArticleList :articles="articles" />
      <p class="back"><router-link to="/tags">← 返回标签索引</router-link></p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, watchEffect } from 'vue';
import { useRoute } from 'vue-router';
import { useContent } from '@/composables/useContent';
import ArticleList from '@/components/list/ArticleList.vue';

const route = useRoute();
const { manifest } = useContent();

const tag = computed(() => decodeURIComponent(String(route.params.tag)));
const articles = computed(() => {
  const paths = manifest.value?.tags[tag.value] || [];
  return paths.map((p) => manifest.value!.articles[p]).filter(Boolean);
});

watchEffect(() => { document.title = `#${tag.value} - 箓川码笺`; });
</script>

<style scoped>
.page-shell { min-height: calc(100vh - var(--ifm-navbar-height)); padding: 64px 24px 96px; background: var(--site-background); }
.simple-page { width: min(880px, 100%); margin: 0 auto; }
.eyebrow { margin: 0 0 12px; color: var(--ifm-color-primary); font-size: 0.82rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.simple-page h1 { margin: 0 0 32px; color: var(--site-text); font-size: clamp(2rem, 4vw, 3.2rem); line-height: 1.12; }
.back { margin-top: 32px; }
.back a { color: var(--site-text-muted); font-size: 0.92rem; }
.back a:hover { color: var(--ifm-color-primary); }
</style>
