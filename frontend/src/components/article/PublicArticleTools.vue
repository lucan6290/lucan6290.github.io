<template>
  <section class="article-interactions" :aria-labelledby="headingId">
    <header>
      <h2 :id="headingId">文章互动</h2>
      <p v-if="views !== null" class="view-count">累计阅读 {{ views.toLocaleString('zh-CN') }} 次</p>
    </header>
    <p v-if="!publicServiceConfigured">本站尚未启用评论与阅读统计。</p>
    <p v-else-if="loading" role="status">正在加载评论与阅读量…</p>
    <div v-else-if="loadError">
      <p role="status">{{ loadError }}</p>
      <button type="button" @click="loadArticle">重新加载</button>
    </div>
    <template v-else>
      <h3>评论</h3>
      <ol v-if="comments.length" class="comment-list">
        <li v-for="comment in comments" :key="comment.id">
          <div class="comment-meta">
            <strong>匿名读者</strong>
            <time :datetime="comment.created_at">{{ formatDate.format(new Date(comment.created_at)) }}</time>
          </div>
          <p>{{ comment.body }}</p>
        </li>
      </ol>
      <p v-else>还没有公开评论。</p>
      <button v-if="nextBefore !== null" type="button" :disabled="paging" @click="loadMore">
        {{ paging ? '正在加载…' : '查看更多评论' }}
      </button>
      <p v-if="pagingError" role="alert">{{ pagingError }}</p>
      <form class="comment-form" @submit.prevent="submit">
        <label :for="bodyId">匿名留言</label>
        <textarea
          :id="bodyId" v-model="draft" :aria-describedby="hintId"
          required rows="4" maxlength="4000" :disabled="submitting"
        />
        <p :id="hintId">请输入 1–2000 个字符。留言经审核后公开。</p>
        <div class="form-actions">
          <button type="submit" :disabled="submitting || !draft.trim()">
            {{ submitting ? '正在提交…' : '提交评论' }}
          </button>
          <span v-if="submitMessage" :role="submitError ? 'alert' : 'status'">{{ submitMessage }}</span>
        </div>
      </form>
    </template>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, useId, watch } from 'vue';
import {
  articleService, PublicServiceError, publicServiceConfigured, visitorSession, type PublicComment,
} from '@/api/publicService';

const props = defineProps<{ articlePath: string }>();
const headingId = useId();
const bodyId = useId();
const hintId = useId();
const formatDate = new Intl.DateTimeFormat('zh-CN', {
  dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Shanghai',
});

const loading = ref(false);
const loadError = ref('');
const views = ref<number | null>(null);
const comments = ref<PublicComment[]>([]);
const nextBefore = ref<number | null>(null);
const draft = ref('');
const paging = ref(false);
const pagingError = ref('');
const submitting = ref(false);
const submitMessage = ref('');
const submitError = ref(false);
let current: AbortController | undefined;
let lastSubmission: { body: string; id: string } | undefined;

function message(error: unknown, fallback: string) {
  return error instanceof PublicServiceError ? error.message : fallback;
}

async function loadArticle() {
  current?.abort();
  const controller = new AbortController();
  current = controller;
  const { signal } = controller;
  const path = props.articlePath;
  views.value = null;
  comments.value = [];
  nextBefore.value = null;
  draft.value = '';
  lastSubmission = undefined;
  paging.value = false;
  pagingError.value = '';
  submitting.value = false;
  submitMessage.value = '';
  submitError.value = false;
  loadError.value = '';
  if (!publicServiceConfigured) return;

  loading.value = true;
  try {
    const result = await articleService.get(path, signal);
    if (signal.aborted) return;
    comments.value = result.comments;
    nextBefore.value = result.next_before;
    views.value = result.views;
  } catch (error) {
    if (!signal.aborted) loadError.value = message(error, '互动服务暂不可用，请稍后再试。');
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

async function loadMore() {
  const signal = current?.signal;
  if (!signal || nextBefore.value === null || paging.value) return;
  paging.value = true;
  pagingError.value = '';
  try {
    const result = await articleService.get(props.articlePath, signal, nextBefore.value);
    if (signal.aborted) return;
    comments.value.push(...result.comments);
    nextBefore.value = result.next_before;
  } catch (error) {
    if (!signal.aborted) pagingError.value = message(error, '评论加载失败，请重试。');
  } finally {
    if (!signal.aborted) paging.value = false;
  }
}

async function submit() {
  const signal = current?.signal;
  const body = draft.value.trim();
  if (!signal || !body || submitting.value) return;
  if ([...body].length > 2000) {
    submitError.value = true;
    submitMessage.value = '留言不能超过 2000 个字符。';
    return;
  }
  submitting.value = true;
  submitMessage.value = '';
  submitError.value = false;
  try {
    if (lastSubmission?.body !== body) lastSubmission = { body, id: crypto.randomUUID() };
    await articleService.comment(props.articlePath, body, lastSubmission.id, signal);
    if (signal.aborted) return;
    draft.value = '';
    lastSubmission = undefined;
    submitMessage.value = '留言已提交。审核通过后会显示在评论区。';
  } catch (error) {
    if (signal.aborted) return;
    submitError.value = true;
    submitMessage.value = message(error, '留言提交失败，请稍后再试。');
  } finally {
    if (!signal.aborted) submitting.value = false;
  }
}

watch(() => props.articlePath, loadArticle, { immediate: true });
onBeforeUnmount(() => current?.abort());
</script>

<style scoped>
.article-interactions { margin-top: 32px; padding: 20px 0 0; border-top: 1px solid var(--site-border); }
header { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 8px 16px; }
h2, h3 { margin: 0 0 8px; }
h3 { margin-top: 16px; font-size: 1rem; }
.view-count, .comment-meta, .comment-form p { color: var(--site-text-secondary); font-size: .88rem; }
.comment-list { list-style: none; margin: 0 0 12px; padding: 0; }
.comment-list li { border-bottom: 1px solid var(--site-border); padding: 12px 0; }
.comment-list li p { margin: 4px 0 0; white-space: pre-wrap; overflow-wrap: anywhere; }
.comment-meta, .form-actions { display: flex; flex-wrap: wrap; gap: 4px 12px; align-items: baseline; }
.comment-form { margin-top: 20px; display: grid; gap: 6px; }
label { font-weight: 700; }
textarea, button { border: 1px solid var(--site-border); border-radius: var(--ifm-global-radius); font: inherit; }
textarea { padding: 8px 12px; color: var(--site-text); background: var(--site-surface); resize: vertical; }
button { padding: 4px 12px; background: var(--site-accent-soft); color: var(--site-accent-ink); cursor: pointer; }
button:disabled { opacity: .65; cursor: default; }
:is(button, textarea):focus-visible { outline: 2px solid var(--ifm-color-primary); outline-offset: 2px; }
[role="alert"] { color: var(--site-danger); }
</style>
