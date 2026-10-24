<template>
  <div class="article-layout">
    <ResizableSidebar>
      <TreeSidebar :nodes="treeNodes" :active-path="article.path" :root="root" />
    </ResizableSidebar>
    <main class="article-main">
      <ReadingProgress />
      <article class="markdown-body">
        <header class="article-header">
          <h1>{{ article.frontmatter.title }}</h1>
          <div class="byline">
            <span class="author-mark" aria-hidden="true">箓</span>
            <div class="author-details">
              <strong>小灿同学啊</strong>
              <span>作者</span>
            </div>
            <span class="word-count">全文 {{ article.wordCount }} 字</span>
          </div>
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
import ResizableSidebar from '@/components/sidebar/ResizableSidebar.vue';
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
  grid-template-columns: auto minmax(0, 1fr);
  min-height: calc(100vh - var(--ifm-navbar-height));
}
.article-main {
  padding: 40px clamp(28px, 4vw, 64px) 96px;
  max-width: 940px;
  margin: 0 auto;
  width: 100%;
  min-width: 0;
}
.article-header { margin-bottom: 24px; padding-bottom: 18px; border-bottom: 1px solid var(--site-border); }
.article-header h1 { max-width: 100%; margin-bottom: 18px; color: var(--site-reading-heading); font-size: clamp(1.95rem, 3.2vw, 2.5rem); line-height: 1.32; letter-spacing: -.025em; }
.byline { display: flex; align-items: center; gap: 11px; margin-bottom: 12px; }
.author-mark { display: grid; place-items: center; flex: none; width: 38px; height: 38px; border-radius: 50%; background: var(--site-accent-soft); color: var(--site-accent-ink); font-family: var(--site-font-literary); font-size: 1.1rem; font-weight: 700; }
.author-details { display: flex; flex-direction: column; gap: 1px; }
.author-details strong { color: var(--site-text); font-size: .88rem; font-weight: 700; line-height: 1.4; }
.author-details > span { color: var(--site-text-secondary); font-size: .82rem; line-height: 1.3; }
.word-count { margin-left: auto; color: var(--site-text-secondary); font-size: .82rem; white-space: nowrap; }
.meta { display: flex; flex-wrap: wrap; gap: 4px 10px; color: var(--site-text-secondary); font-size: 0.82rem; margin-bottom: 12px; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tags a {
  border: 1px solid transparent;
  border-radius: 5px;
  padding: 3px 9px;
  background: var(--site-accent-soft);
  color: var(--ifm-color-primary-dark);
  font-size: 0.82rem;
  font-weight: 600;
}
.tags a:hover { border-color: var(--site-accent); }

@media (max-width: 996px) {
  .article-layout { display: block; }
  .article-main { padding: 28px 20px 72px; }
  .article-header h1 { font-size: clamp(1.65rem, 7vw, 1.95rem); }
  .word-count { font-size: .82rem; }
}
</style>
