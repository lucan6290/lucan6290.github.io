<template>
  <main class="series-page">
    <router-link v-if="id" :to="SERIES_ROOT">全部系列</router-link>
    <h1>{{ title }}</h1>
    <ol v-if="group">
      <li v-for="path in group.articlePaths" :key="path">
        <router-link :to="contentHref(path)">{{ manifest.articles[path].frontmatter.title }}</router-link>
      </li>
    </ol>
    <p v-else-if="id">这个系列可能已移动或删除。</p>
    <ul v-else-if="groups.length">
      <li v-for="series in groups" :key="series.id">
        <router-link :to="seriesHref(series.id)">{{ series.title }}</router-link>
        <span> · {{ series.articlePaths.length }} 篇</span>
      </li>
    </ul>
    <p v-else>暂无系列专题。</p>
  </main>
</template>

<script setup lang="ts">
import { computed, watchEffect } from 'vue';
import { useRoute } from 'vue-router';
import { contentHref } from '@/composables/contentPaths';
import { useContent } from '@/composables/useContent';
import { SERIES_ROOT, seriesHref } from '@/utils/seriesPaths';

const route = useRoute();
const { manifest } = useContent();
const id = computed(() => String(route.params.id || ''));
const groups = computed(() => Object.values(manifest.value.series));
const group = computed(() => Object.hasOwn(manifest.value.series, id.value) ? manifest.value.series[id.value] : undefined);
const title = computed(() => group.value?.title || (id.value ? '系列不存在' : '系列专题'));

watchEffect(() => {
  document.title = `${title.value} - 箓川码笺`;
});
</script>

<style scoped>
.series-page { width: min(100% - 40px, 860px); margin: 48px auto 80px; }
.series-page li + li { margin-top: 8px; }
.series-page li span { color: var(--site-text-secondary); }
</style>
