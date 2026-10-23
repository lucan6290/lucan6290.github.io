<template>
  <div class="category-layout">
    <aside class="sidebar-container">
      <TreeSidebar :nodes="treeNodes" :active-path="path" :root="root" />
    </aside>
    <main class="category-main">
      <Breadcrumb :path="path" :root="root" />
      <header class="category-header">
        <h1>{{ title }}</h1>
        <SortToggle v-if="articles.length" :mode="sortMode" @toggle="toggleSort" />
      </header>
      <MarkdownRenderer
        v-if="currentNode?.introduction"
        :key="currentNode.introduction.relativePath"
        :content="currentNode.introduction.rawContent"
        :relative-path="currentNode.introduction.relativePath"
      />
      <nav v-if="subcategories.length" class="subcategory-list" aria-label="子分类">
        <h2>子分类</h2>
        <ul>
          <li v-for="category in subcategories" :key="category.path">
            <router-link :to="contentHref(category.path)">{{ category.label }}</router-link>
          </li>
        </ul>
      </nav>
      <ArticleList v-if="articles.length || (!subcategories.length && !currentNode?.introduction)" :articles="articles" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, watchEffect } from 'vue';
import { useContent } from '@/composables/useContent';
import TreeSidebar from '@/components/sidebar/TreeSidebar.vue';
import Breadcrumb from '@/components/list/Breadcrumb.vue';
import SortToggle from '@/components/list/SortToggle.vue';
import ArticleList from '@/components/list/ArticleList.vue';
import MarkdownRenderer from '@/components/article/MarkdownRenderer.vue';
import { sectionLabel } from '@/config/nav';
import { contentHref } from '@/composables/contentPaths';

const props = defineProps<{ root: string; path: string }>();

const { ready, findNodeByPath, getArticlesUnder, sortMode, toggleSort, manifest } = useContent();

const treeNodes = computed(() => {
  if (!manifest.value) return [];
  // 取 root 对应的子树
  const seg = props.root.replace(/^\/+/, '');
  const top = manifest.value.tree.find((n) => n.name === seg || n.path === props.root);
  return top ? top.children : [];
});

const currentNode = computed(() => findNodeByPath(props.path));
const subcategories = computed(() => props.root === '/knowledge'
  ? currentNode.value?.children.filter((node) => !node.article) || []
  : []);

const articles = computed(() => {
  if (!ready.value) return [];
  const list = getArticlesUnder(currentNode.value);
  return props.root === '/knowledge'
    ? list.filter((article) => article.path.slice(0, article.path.lastIndexOf('/')) === props.path)
    : list;
});

const title = computed(() => {
  if (props.path === props.root) return sectionLabel(props.root.slice(1));
  return currentNode.value?.label || props.path.split('/').pop() || '';
});

watchEffect(() => {
  document.title = `${title.value} - 箓川码笺`;
});
</script>

<style scoped>
.category-layout {
  display: grid;
  grid-template-columns: var(--doc-sidebar-width) minmax(0, 1fr);
  min-height: calc(100vh - var(--ifm-navbar-height));
}
.sidebar-container {
  position: sticky;
  top: var(--ifm-navbar-height);
  height: calc(100vh - var(--ifm-navbar-height));
  overflow-y: auto;
  border-right: 1px solid var(--site-border);
  background: var(--site-surface);
  padding: 20px 16px 96px 12px;
}
.category-main {
  padding: 32px 56px 96px;
  max-width: 920px;
  margin: 0 auto;
}
.category-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--site-border);
}
.category-header h1 { font-size: 32px; line-height: 1.25; }
.subcategory-list { margin-bottom: 28px; }
.subcategory-list h2 { font-size: 18px; margin-bottom: 12px; }
.subcategory-list ul { list-style: none; padding: 0; display: grid; gap: 10px; }
.subcategory-list a {
  display: block;
  padding: 14px 18px;
  border: 1px solid var(--site-border);
  border-radius: 8px;
  color: var(--site-text);
  background: var(--site-surface);
  text-decoration: none;
}
.subcategory-list a:hover { border-color: var(--ifm-color-primary); color: var(--ifm-color-primary); }

@media (max-width: 996px) {
  .category-layout { display: block; }
  .sidebar-container {
    position: static;
    height: auto;
    border-right: 0;
    border-bottom: 1px solid var(--site-border);
    padding: 24px 20px;
  }
  .category-main { padding: 24px 20px 72px; }
}
</style>
