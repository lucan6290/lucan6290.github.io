<template>
  <div v-if="!ready" class="loading">加载中…</div>
  <ArticleView v-else-if="article" :key="article.path" :article="article" />
  <CategoryView v-else-if="node" :key="currentPath" :root="root" :path="currentPath" />
  <main v-else class="loading"><h1>内容不存在</h1><p>这个栏目或文档已被移动或删除。</p><router-link to="/">返回首页</router-link></main>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useContent } from '@/composables/useContent';
import { contentPath } from '@/composables/contentPaths';
import CategoryView from './CategoryView.vue';
import ArticleView from './ArticleView.vue';

const route = useRoute();
const { ready, getArticle, findNodeByPath } = useContent();

const root = computed(() => '/' + String(route.params.section));
const currentPath = computed(() => contentPath(root.value, route.params.pathMatch));
const node = computed(() => findNodeByPath(currentPath.value));

const article = computed(() => {
  const p = currentPath.value;
  if (!p || p === root.value) return undefined;
  return getArticle(p);
});
</script>

<style scoped>
.loading { padding: 96px 24px; text-align: center; color: var(--site-text-muted); }
</style>
