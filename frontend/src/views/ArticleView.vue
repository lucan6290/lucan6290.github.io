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
          </div>
          <div class="meta">
            <span class="meta-item" tabindex="0" aria-describedby="reading-time-tip">
              <svg class="meta-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M5 2h14M5 22h14M6 2v4a6 6 0 0 0 3 5.2L12 13l3-1.8A6 6 0 0 0 18 6V2M6 22v-4a6 6 0 0 1 3-5.2L12 11l3 1.8a6 6 0 0 1 3 5.2v4" /></svg>
              <span class="meta-label">预计阅读时长</span>{{ article.readingMinutes }} 分钟
              <span id="reading-time-tip" class="meta-tooltip" role="tooltip">预计阅读时长 ⏳</span>
            </span>
            <span class="meta-item" tabindex="0" aria-describedby="word-count-tip">
              <svg class="meta-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6M8 13h8M8 17h6" /></svg>
              <span class="meta-label">全文</span>{{ article.wordCount }} 字
              <span id="word-count-tip" class="meta-tooltip" role="tooltip">文章字数 📝</span>
            </span>
            <span class="meta-item" tabindex="0" aria-describedby="created-time-tip">
              <svg class="meta-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 11h18" /></svg>
              <span class="meta-label">创建于</span><time v-if="article.frontmatter.date" :datetime="article.frontmatter.date">{{ formatDate(article.frontmatter.date) }}</time><template v-else>未记录</template>
              <span id="created-time-tip" class="meta-tooltip" role="tooltip">写作日期 📅</span>
            </span>
            <span class="meta-item" tabindex="0" aria-describedby="updated-time-tip">
              <svg class="meta-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M3 11a9 9 0 1 1 2.6 7M3 4v7h7M12 7v5l3 2" /></svg>
              <span class="meta-label">更新于</span><time v-if="article.frontmatter.updated" :datetime="article.frontmatter.updated">{{ formatDate(article.frontmatter.updated) }}</time><template v-else>未记录</template>
              <span id="updated-time-tip" class="meta-tooltip" role="tooltip">最新更新时间 🕒</span>
            </span>
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
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Shanghai' })
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
.meta { display: flex; flex-wrap: wrap; gap: 6px 16px; color: var(--site-text-secondary); font-size: 0.82rem; margin-bottom: 12px; line-height: 1.6; font-variant-numeric: tabular-nums; }
.meta-item { position: relative; white-space: nowrap; cursor: help; }
.meta-icon { width: 1em; height: 1em; margin-right: 5px; vertical-align: -.15em; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.meta-label { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.meta-item:focus-visible { outline: 2px solid var(--ifm-color-primary); outline-offset: 3px; border-radius: 3px; }
.meta-tooltip {
  position: absolute;
  z-index: 10;
  bottom: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 12px;
  border-radius: 3px;
  background: var(--site-accent-soft);
  color: var(--site-text);
  border: 1px solid var(--site-border);
  box-shadow: 0 4px 12px var(--site-shadow);
  font-size: .88rem;
  font-weight: 600;
  line-height: 1.5;
  visibility: hidden;
  opacity: 0;
  pointer-events: none;
  transition: opacity 150ms;
}
.meta-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  width: 10px;
  height: 10px;
  transform: translate(-50%, -50%) rotate(45deg);
  background: var(--site-accent-soft);
  border-right: 1px solid var(--site-border);
  border-bottom: 1px solid var(--site-border);
}
.meta-item:hover > .meta-tooltip,
.meta-item:focus-visible > .meta-tooltip { visibility: visible; opacity: 1; }
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
  .meta-tooltip { left: 0; transform: none; }
  .meta-tooltip::after { left: 24px; }
}
</style>
