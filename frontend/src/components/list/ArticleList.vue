<template>
  <div v-if="articles.length" class="article-list">
    <article v-for="art in articles" :key="art.path" class="article-item">
      <header>
        <h2><router-link :to="contentHref(art.path)">{{ art.frontmatter.title }}</router-link></h2>
        <time v-if="art.frontmatter.date" :datetime="art.frontmatter.date">{{ formatDate(art.frontmatter.date) }}</time>
      </header>
      <p v-if="art.excerpt">{{ art.excerpt }}</p>
      <div v-if="art.frontmatter.tags?.length" class="tags">
        <router-link v-for="tag in art.frontmatter.tags" :key="tag" :to="`/tags/${encodeURIComponent(tag)}`">{{ tag }}</router-link>
      </div>
    </article>
  </div>
  <p v-else class="empty">这个分类下还没有文章。</p>
</template>

<script setup lang="ts">
import type { ArticleMeta } from '@/types/content';
import { contentHref } from '@/composables/contentPaths';

defineProps<{ articles: ArticleMeta[] }>();

function formatDate(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Shanghai' })
    .format(d)
    .replace(/\//g, '.');
}
</script>

<style scoped>
.article-list { display: grid; gap: 18px; }
.article-item { padding-bottom: 18px; border-bottom: 1px solid var(--site-border); }
.article-item header { display: flex; align-items: baseline; justify-content: space-between; gap: 20px; }
.article-item h2 { margin: 0; font-size: 22px; line-height: 1.45; text-wrap: pretty; }
.article-item h2 a { color: var(--site-text); text-decoration: none; }
.article-item h2 a:hover { color: var(--ifm-color-primary); }
.article-item time { flex: none; color: var(--site-text-secondary); font-size: 14px; }
.article-item p { margin: 10px 0 0; color: var(--site-text-secondary); font-size: 16px; line-height: 1.68; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.tags a {
  border-radius: 5px;
  padding: 3px 9px;
  background: var(--site-accent-soft);
  color: var(--ifm-color-primary-dark);
  font-size: 13px;
  font-weight: 600;
  line-height: 20px;
}
.tags a:hover { background: var(--site-border); }
.empty { color: var(--site-text-muted); font-size: 16px; }

@media (max-width: 700px) {
  .article-item header { display: block; }
  .article-item h2 { font-size: 21px; }
  .article-item time { display: block; margin-top: 6px; }
}
</style>
