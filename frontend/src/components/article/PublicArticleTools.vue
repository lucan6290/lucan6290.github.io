<template>
  <section class="article-interactions" :aria-labelledby="headingId">
    <header>
      <h2 :id="headingId">评论</h2>
      <p v-if="views !== null" class="view-count">累计阅读 {{ views.toLocaleString('zh-CN') }} 次</p>
    </header>
    <p v-if="loading" role="status">正在加载阅读量…</p>
    <div v-else-if="loadError">
      <p role="status">{{ loadError }}</p>
      <button type="button" @click="loadViews">重新加载</button>
    </div>
    <Giscus
      v-if="giscusCategoryId"
      id="article-comments"
      repo="lucan6290/lucan6290.github.io"
      repo-id="R_kgDOSk2r-g"
      category="文章评论"
      :category-id="giscusCategoryId"
      mapping="specific"
      :term="articlePath"
      strict="1"
      :theme="siteTheme"
      lang="zh-CN"
      loading="lazy"
    />
    <p v-else>本站尚未启用文章评论。</p>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, useId, watch } from 'vue';
import Giscus from '@giscus/vue';
import { siteTheme } from '@/composables/useTheme';
import {
  articleService, PublicServiceError, publicServiceConfigured, visitorSession,
} from '@/api/publicService';

const props = defineProps<{ articlePath: string }>();
const headingId = useId();
const loading = ref(false);
const loadError = ref('');
const views = ref<number | null>(null);
const giscusCategoryId = import.meta.env.VITE_GISCUS_CATEGORY_ID?.trim();
let current: AbortController | undefined;

async function loadViews() {
  current?.abort();
  const controller = new AbortController();
  current = controller;
  const { signal } = controller;
  const path = props.articlePath;
  views.value = null;
  loadError.value = '';
  if (!publicServiceConfigured) return;

  loading.value = true;
  try {
    const result = await articleService.get(path, signal);
    if (signal.aborted) return;
    views.value = result.views;
  } catch (error) {
    if (!signal.aborted) loadError.value = error instanceof PublicServiceError ? error.message : '阅读量暂不可用，请稍后再试。';
    return;
  } finally {
    if (!signal.aborted) loading.value = false;
  }

  const session = visitorSession();
  if (session) {
    // 保留已查询的累计阅读量，下一次浏览可安全重试计数。
    const result = await articleService.view(path, session, signal).catch(() => null);
    if (result && !signal.aborted) views.value = result.views;
  }
}

watch(() => props.articlePath, loadViews, { immediate: true });
onBeforeUnmount(() => current?.abort());

</script>

<style scoped>
.article-interactions { margin-top: 32px; padding: 20px 0 0; border-top: 1px solid var(--site-border); }
header { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 8px 16px; }
h2 { margin: 0 0 8px; }
.view-count { color: var(--site-text-secondary); font-size: .88rem; }
button { padding: 4px 12px; border: 1px solid var(--site-border); border-radius: var(--ifm-global-radius); font: inherit; background: var(--site-accent-soft); color: var(--site-accent-ink); cursor: pointer; }
button:focus-visible { outline: 2px solid var(--ifm-color-primary); outline-offset: 2px; }
</style>
