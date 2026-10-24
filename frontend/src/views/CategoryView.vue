<template>
  <div class="category-layout" :class="{ 'knowledge-home': isKnowledgeHome }">
    <aside class="sidebar-container">
      <nav v-if="isKnowledgeHome" aria-label="知识库分类" class="home-categories">
        <router-link v-for="category in subcategories" :key="category.path" :to="contentHref(category.path)">{{ category.label }}</router-link>
      </nav>
      <TreeSidebar v-else :nodes="treeNodes" :active-path="path" :root="root" />
    </aside>
    <main class="category-main">
      <Breadcrumb v-if="!isKnowledgeHome" :path="path" :root="root" />
      <header v-if="!isKnowledgeHome" class="category-header">
        <h1>{{ title }}</h1>
        <SortToggle v-if="articles.length" :mode="sortMode" @toggle="toggleSort" />
      </header>
      <MarkdownRenderer
        v-if="currentNode?.introduction && (!isKnowledgeHome || currentNode.introduction.rawContent.trim())"
        :key="currentNode.introduction.relativePath"
        :content="currentNode.introduction.rawContent"
        :relative-path="currentNode.introduction.relativePath"
      />
      <p v-else-if="isKnowledgeHome" class="empty-home">暂无首页内容。</p>
      <nav v-if="!isKnowledgeHome && subcategories.length" class="subcategory-list" aria-label="子分类">
        <h2>子分类</h2>
        <ul>
          <li v-for="category in subcategories" :key="category.path">
            <router-link :to="contentHref(category.path)">{{ category.label }}</router-link>
          </li>
        </ul>
      </nav>
      <ArticleList v-if="!isKnowledgeHome && (articles.length || (!subcategories.length && !currentNode?.introduction))" :articles="articles" />
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
import { contentHref, sidebarNodes } from '@/composables/contentPaths';

const props = defineProps<{ root: string; path: string }>();
const isKnowledgeHome = computed(() => props.root === '/knowledge' && props.path === '/knowledge');

const { ready, findNodeByPath, getArticlesUnder, sortMode, toggleSort, manifest } = useContent();

const treeNodes = computed(() => {
  if (!manifest.value) return [];
  // 取 root 对应的子树
  const seg = props.root.replace(/^\/+/, '');
  const top = manifest.value.tree.find((n) => n.name === seg || n.path === props.root);
  return top ? sidebarNodes(top.children, props.root, props.path) : [];
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
.knowledge-home .category-main { width: 100%; }
.empty-home { color: var(--site-text-muted); }
.home-categories { display: grid; gap: 4px; }
.home-categories a { padding: 8px 10px; border-radius: 6px; color: var(--site-text-secondary); text-decoration: none; }
.home-categories a:hover { color: var(--ifm-color-primary); background: var(--site-accent-soft); }
.sidebar-container {
  position: sticky;
  top: var(--ifm-navbar-height);
  height: calc(100vh - var(--ifm-navbar-height));
  overflow-y: auto;
  border-right: 1px solid var(--site-border);
  background: var(--site-surface);
  padding: 24px 18px 96px 14px;
}
.category-main {
  padding: 42px clamp(28px, 5vw, 68px) 96px;
  max-width: 940px;
  margin: 0 auto;
}
.category-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 27px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--site-border);
}
.category-header h1 { font-size: clamp(1.8rem, 3.5vw, 2.1rem); line-height: 1.3; letter-spacing: -.025em; }
.subcategory-list { margin-bottom: 32px; }
.subcategory-list h2 { font-size: 18px; margin-bottom: 12px; }
.subcategory-list ul { list-style: none; padding: 0; display: grid; gap: 0; }
.subcategory-list a {
  display: block;
  padding: 13px 2px;
  border-bottom: 1px solid var(--site-border);
  color: var(--site-text);
  text-decoration: none;
}
.subcategory-list a:hover { color: var(--ifm-color-primary); }

@media (max-width: 996px) {
  .category-layout { display: block; }
  .sidebar-container {
    position: static;
    height: auto;
    border-right: 0;
    border-bottom: 1px solid var(--site-border);
    padding: 16px 20px;
  }
  .category-main { padding: 28px 20px 72px; }
}
</style>
