<template>
  <section class="article-interactions" :aria-labelledby="headingId">
    <header>
      <h2 :id="headingId">评论</h2>
      <p v-if="views !== null" class="view-count">累计阅读 {{ views.toLocaleString('zh-CN') }} 次</p>
    </header>
    <p v-if="!publicServiceConfigured">本站尚未启用阅读统计。</p>
    <p v-else-if="loading" role="status">正在加载阅读量…</p>
    <div v-else-if="loadError">
      <p role="status">{{ loadError }}</p>
      <button type="button" @click="loadViews">重新加载</button>
    </div>
    <p>使用 GitHub 账号登录后发表评论。</p>
    <div ref="commentsHost" />
    <p v-if="commentsFailed" role="status">GitHub 评论暂无法加载，请刷新页面重试。</p>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, useId, watch } from 'vue';
import {
  articleService, PublicServiceError, publicServiceConfigured, visitorSession,
} from '@/api/publicService';

const props = defineProps<{ articlePath: string }>();
const headingId = useId();
const loading = ref(false);
const loadError = ref('');
const views = ref<number | null>(null);
const commentsHost = ref<HTMLDivElement | null>(null);
const commentsFailed = ref(false);
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

// ArticleView 按源路径挂载此组件，换文章时 Vue 会移除整个评论容器。
onMounted(async () => {
  try {
    // 使用固定长度的检索词，避免中文及长路径受 GitHub Issue 搜索和标题长度限制。
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(props.articlePath));
    if (!commentsHost.value) return;
    const issueKey = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
    const script = document.createElement('script');
    script.src = 'https://utteranc.es/client.js';
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.setAttribute('repo', 'lucan6290/lucan6290.github.io');
    script.setAttribute('issue-term', `blog-comment ${issueKey}`);
    script.setAttribute('theme', 'preferred-color-scheme');
    script.onerror = () => { commentsFailed.value = true; };
    commentsHost.value.append(script);
  } catch {
    commentsFailed.value = true;
  }
});
</script>

<style scoped>
.article-interactions { margin-top: 32px; padding: 20px 0 0; border-top: 1px solid var(--site-border); }
header { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 8px 16px; }
h2 { margin: 0 0 8px; }
.view-count { color: var(--site-text-secondary); font-size: .88rem; }
button { padding: 4px 12px; border: 1px solid var(--site-border); border-radius: var(--ifm-global-radius); font: inherit; background: var(--site-accent-soft); color: var(--site-accent-ink); cursor: pointer; }
button:focus-visible { outline: 2px solid var(--ifm-color-primary); outline-offset: 2px; }
</style>
