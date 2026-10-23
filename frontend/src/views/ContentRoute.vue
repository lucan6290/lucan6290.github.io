<template>
  <div v-if="!ready" class="loading">加载中…</div>
  <ArticleView v-else-if="article" :key="article.path" :article="article" />
  <CategoryView v-else :root="root" :path="currentPath" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useContent } from '@/composables/useContent';
import { contentPath } from '@/composables/contentPaths';
import CategoryView from './CategoryView.vue';
import ArticleView from './ArticleView.vue';

const route = useRoute();
const { ready, getArticle } = useContent();

const root = computed(() => route.name === 'blog' ? '/blog' : '/knowledge');
const currentPath = computed(() => contentPath(root.value, route.params.pathMatch));

const article = computed(() => {
  const p = currentPath.value;
  if (!p || p === root.value) return undefined;
  return getArticle(p);
});
</script>

<style scoped>
.loading { padding: 96px 24px; text-align: center; color: var(--site-text-muted); }
</style>
