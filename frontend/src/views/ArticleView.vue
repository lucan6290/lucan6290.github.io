<template>
  <div class="article-layout">
    <aside class="sidebar-container">
      <TreeSidebar :nodes="treeNodes" :active-path="article.path" :root="root" />
    </aside>
    <main class="article-main">
      <ReadingProgress />
      <article class="markdown-body">
        <header>
          <h1>{{ article.frontmatter.title }}</h1>
          <div class="meta">
            <time v-if="article.frontmatter.date" :datetime="article.frontmatter.date">发布于 {{ formatDate(article.frontmatter.date) }}</time>
            <time v-if="article.frontmatter.updated && article.frontmatter.updated !== article.frontmatter.date" :datetime="article.frontmatter.updated">· 更新于 {{ formatDate(article.frontmatter.updated) }}</time>
          </div>
          <div v-if="article.frontmatter.tags?.length" class="tags">
            <router-link v-for="tag in article.frontmatter.tags" :key="tag" :to="`/tags/${encodeURIComponent(tag)}`">{{ tag }}</router-link>
          </div>
        </header>
        <MarkdownRenderer :content="rawContent" :relative-path="article.relativePath" :title="article.frontmatter.title" />
      </article>
      <PrevNext :prev="pn.prev" :next="pn.next" />
    </main>
    <FloatToc />
  </div>
</template>

<script setup lang="ts">
import { computed, watchEffect } from 'vue';
import type { ArticleMeta } from '@/types/content';
import { useContent } from '@/composables/useContent';
import { sidebarNodes } from '@/composables/contentPaths';
import TreeSidebar from '@/components/sidebar/TreeSidebar.vue';
import MarkdownRenderer from '@/components/article/MarkdownRenderer.vue';
import ReadingProgress from '@/components/article/ReadingProgress.vue';
import PrevNext from '@/components/article/PrevNext.vue';
import FloatToc from '@/components/toc/FloatToc.vue';

const props = defineProps<{ article: ArticleMeta }>();

const { manifest, getPrevNext } = useContent();
const pn = computed(() => getPrevNext(props.article.path));

// 原文直接从 manifest 读取（构建期已写入），无需运行时 IO
const rawContent = computed(() => props.article.rawContent ?? '');

const root = computed(() => '/' + props.article.path.split('/')[1]);
const treeNodes = computed(() => {
  if (!manifest.value) return [];
  const seg = root.value.replace(/^\/+/, '');
  const top = manifest.value.tree.find((n) => n.name === seg || n.path === root.value);
  return top ? sidebarNodes(top.children, root.value, props.article.path) : [];
});

watchEffect(() => {
  document.title = `${props.article.frontmatter.title} - 箓川码笺`;
});

function formatDate(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Shanghai' })
    .format(d)
    .replace(/\//g, '.');
}
</script>

<style scoped>
.article-layout {
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
.article-main {
  padding: 32px 56px 96px;
  max-width: 860px;
  margin: 0 auto;
  width: 100%;
}
.markdown-body header { margin-bottom: 32px; }
.markdown-body h1 { font-size: 46px; line-height: 1.16; margin-bottom: 14px; }
.meta { color: var(--site-text-muted); font-size: 0.92rem; margin-bottom: 12px; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tags a {
  border: 1px solid var(--site-border);
  border-radius: 999px;
  padding: 2px 9px;
  color: var(--ifm-color-primary-dark);
  font-size: 12px;
  font-weight: 700;
}

@media (max-width: 996px) {
  .article-layout { display: block; }
  .sidebar-container { position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--site-border); padding: 24px 20px; }
  .article-main { padding: 24px 20px 72px; }
  .markdown-body h1 { font-size: 30px; }
}
</style>
