<template>
  <div class="author-page">
    <header class="page-heading">
      <div>
        <h1>站点管理</h1>
        <p>写作 Markdown，审核文章留言。</p>
      </div>
      <button v-if="token" type="button" @click="signOut">退出管理</button>
    </header>

    <p v-if="!publicServiceConfigured" role="status">本站尚未配置在线管理服务。</p>
    <form v-else-if="!token" class="login" autocomplete="off" @submit.prevent="signIn">
      <label for="admin-token">管理员访问令牌</label>
      <input id="admin-token" v-model="credential" type="password" autocomplete="off" required maxlength="512"
        :disabled="checking" />
      <p class="hint">令牌仅在当前页面保留，刷新后需要重新输入。</p>
      <button type="submit" class="primary" :disabled="checking || !credential.trim()">
        {{ checking ? '正在验证…' : '进入管理' }}
      </button>
      <p v-if="loginError" class="error" role="alert">{{ loginError }}</p>
    </form>

    <template v-else>
      <section class="work-area" aria-labelledby="writing-title">
        <h2 id="writing-title">Markdown 写作</h2>
        <p v-if="!writingEnabled">本站尚未启用在线写作。</p>
        <template v-else>
          <p class="hint">保存会更新作者工作区。公开站点在下次静态发布时更新。</p>
          <div class="document-tools">
            <div class="field">
              <label for="article-selection">现有文档</label>
              <select id="article-selection" v-model="chosenPath" :disabled="writingBusy || listingBusy">
                <option value="">{{ listingBusy ? '正在读取列表…' : '选择 Markdown 文档' }}</option>
                <option v-for="entry in documents" :key="entry.relative_path" :value="entry.relative_path">
                  {{ entry.title }}（{{ entry.relative_path }}）
                </option>
              </select>
            </div>
            <button type="button" :disabled="writingBusy || !chosenPath" @click="openDocument">打开文档</button>
            <button type="button" :disabled="writingBusy" @click="newDocument">新建文章</button>
          </div>
          <p v-if="listError" class="error" role="alert">{{ listError }}
            <button type="button" :disabled="listingBusy" @click="loadDocuments()">重试列表</button>
          </p>
          <form v-if="editor" class="editor" @submit.prevent="saveDocument">
            <div class="editor-path">
              <label for="document-path">文档路径</label>
              <input id="document-path" v-model="editor.path" :readonly="editor.version !== null"
                :disabled="writingBusy" required maxlength="1024" placeholder="blog/随笔.md"
                aria-describedby="document-path-hint" />
              <p id="document-path-hint" class="hint">相对于内容库，父目录须已存在。</p>
            </div>
            <label for="markdown-source">Markdown 原文</label>
            <textarea id="markdown-source" v-model="editor.raw" :disabled="writingBusy" rows="19" spellcheck="false"
              aria-describedby="markdown-hint" />
            <p id="markdown-hint" class="hint">普通文章保留 YAML 六字段，标题与正文一级标题一致。</p>
            <div class="row">
              <button class="primary" type="submit" :disabled="writingBusy || !editor.path.trim() || !dirty">
                {{ writingBusy ? '处理中…' : editor.version ? '保存修改' : '创建文章' }}
              </button>
              <button v-if="editor.version" type="button" :disabled="writingBusy"
                @click="openPath(editor.path)">重新读取</button>
              <span v-if="saveMessage" role="status">{{ saveMessage }}</span>
            </div>
          </form>
          <p v-if="writingError" class="error" role="alert">{{ writingError }}</p>
        </template>
      </section>

      <section class="work-area" aria-labelledby="moderation-title">
        <h2 id="moderation-title">留言审核</h2>
        <div class="row">
          <label for="queue-filter">审核状态</label>
          <select id="queue-filter" v-model="queueStatus" :disabled="queueBusy || moderating !== null"
            @change="loadQueue()">
            <option value="pending">待审核</option>
            <option value="published">已公开</option>
            <option value="rejected">已撤下</option>
          </select>
          <button type="button" :disabled="queueBusy || moderating !== null" @click="loadQueue()">刷新队列</button>
        </div>
        <p v-if="queueBusy" role="status">正在读取留言…</p>
        <p v-if="moderationError" class="error" role="alert">{{ moderationError }}</p>
        <p v-if="moderationMessage" role="status">{{ moderationMessage }}</p>
        <ol v-if="queue.length" class="queue">
          <li v-for="comment in queue" :key="comment.id">
            <div class="row hint">
              <strong>{{ comment.article_path }}</strong>
              <time :datetime="comment.created_at">{{ formatDate.format(new Date(comment.created_at)) }}</time>
            </div>
            <p>{{ comment.body }}</p>
            <div class="row">
              <button v-if="comment.status !== 'published'" type="button" :disabled="moderating !== null || queueBusy"
                @click="moderate(comment.id, 'published')">公开留言</button>
              <button v-if="comment.status !== 'rejected'" type="button" :disabled="moderating !== null || queueBusy"
                @click="moderate(comment.id, 'rejected')">{{ comment.status === 'pending' ? '拒绝留言' : '撤下留言' }}</button>
            </div>
          </li>
        </ol>
        <p v-else-if="!queueBusy && !moderationError">此状态没有留言。</p>
        <button v-if="nextBefore !== null" type="button" :disabled="queueBusy || moderating !== null"
          @click="loadQueue(nextBefore ?? undefined)">加载更多留言</button>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import {
  authorService, PublicServiceError, publicServiceConfigured,
  type AdminComment, type CommentStatus, type AuthorDocument, type DocumentSummary,
} from '@/api/publicService';

type Editor = { path: string; raw: string; original: string; version: string | null };

const credential = ref('');
const token = ref('');
const checking = ref(false);
const loginError = ref('');
const writingEnabled = ref(false);
const documents = ref<DocumentSummary[]>([]);
const listingBusy = ref(false);
const listError = ref('');
const chosenPath = ref('');
const editor = ref<Editor | null>(null);
const writingBusy = ref(false);
const writingError = ref('');
const saveMessage = ref('');
const queueStatus = ref<CommentStatus>('pending');
const queue = ref<AdminComment[]>([]);
const nextBefore = ref<number | null>(null);
const queueBusy = ref(false);
const moderating = ref<number | null>(null);
const moderationError = ref('');
const moderationMessage = ref('');
const formatDate = new Intl.DateTimeFormat('zh-CN', {
  dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Shanghai',
});
const dirty = computed(() => Boolean(editor.value && (
  editor.value.raw !== editor.value.original || (!editor.value.version && editor.value.path.trim())
)));
let session: AbortController | undefined;

function explain(error: unknown, fallback: string) {
  return error instanceof PublicServiceError ? error.message : fallback;
}

function discardChanges() {
  return !dirty.value || window.confirm('当前修改尚未保存，确认放弃？');
}

function warnBeforeReload(event: BeforeUnloadEvent) {
  if (dirty.value) {
    event.preventDefault();
    event.returnValue = '';
  }
}

onMounted(() => {
  document.title = '站点管理 - 箓川码笺';
  window.addEventListener('beforeunload', warnBeforeReload);
});
onBeforeRouteLeave(discardChanges);
onBeforeUnmount(() => {
  clearSession();
  window.removeEventListener('beforeunload', warnBeforeReload);
});

async function signIn() {
  const candidate = credential.value.trim();
  if (!candidate || checking.value) return;
  credential.value = '';
  session?.abort();
  session = new AbortController();
  const { signal } = session;
  checking.value = true;
  loginError.value = '';
  try {
    const access = await authorService.session(candidate, signal);
    if (signal.aborted) return;
    writingEnabled.value = access.writing_enabled;
    token.value = candidate;
    if (writingEnabled.value) void loadDocuments();
    void loadQueue();
  } catch (error) {
    if (!signal.aborted) loginError.value = explain(error, '管理服务暂不可用，请稍后重试。');
  } finally {
    if (!signal.aborted) checking.value = false;
  }
}

function clearSession() {
  session?.abort();
  session = undefined;
  token.value = '';
  credential.value = '';
  checking.value = false;
  writingEnabled.value = false;
  documents.value = [];
  chosenPath.value = '';
  editor.value = null;
  writingBusy.value = false;
  listingBusy.value = false;
  listError.value = '';
  writingError.value = '';
  saveMessage.value = '';
  queueStatus.value = 'pending';
  queue.value = [];
  nextBefore.value = null;
  queueBusy.value = false;
  moderating.value = null;
  moderationError.value = '';
  moderationMessage.value = '';
}

function signOut() {
  if (discardChanges()) clearSession();
}

async function loadDocuments() {
  const signal = session?.signal;
  if (!signal || listingBusy.value) return;
  listingBusy.value = true;
  listError.value = '';
  try {
    const result = await authorService.documents(token.value, signal);
    if (!signal.aborted) documents.value = result.documents;
  } catch (error) {
    if (!signal.aborted) listError.value = explain(error, '文档列表读取失败。');
  } finally {
    if (!signal.aborted) listingBusy.value = false;
  }
}

function selectDocument(document: AuthorDocument) {
  editor.value = {
    path: document.relative_path, raw: document.raw_content,
    original: document.raw_content, version: document.version,
  };
  chosenPath.value = document.relative_path;
}

function openDocument() {
  return openPath(chosenPath.value);
}

async function openPath(path: string) {
  const signal = session?.signal;
  if (!signal || !path || writingBusy.value || !discardChanges()) return;
  writingBusy.value = true;
  writingError.value = '';
  saveMessage.value = '';
  try {
    const result = await authorService.open(token.value, path, signal);
    if (!signal.aborted) selectDocument(result);
  } catch (error) {
    if (!signal.aborted) writingError.value = explain(error, '读取文档失败。');
  } finally {
    if (!signal.aborted) writingBusy.value = false;
  }
}

function newDocument() {
  if (!discardChanges()) return;
  const time = new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString().slice(0, 19) + '+08:00';
  const raw = `---\ntitle: ""\ndate: "${time}"\nupdated: "${time}"\ndescription: ""\ntags: []\nsticky: false\n---\n\n# \n`;
  editor.value = { path: '', raw, original: raw, version: null };
  chosenPath.value = '';
  writingError.value = '';
  saveMessage.value = '';
}

async function saveDocument() {
  const signal = session?.signal;
  const current = editor.value;
  if (!signal || !current || !dirty.value || writingBusy.value) return;
  const path = current.path.trim();
  const isNew = current.version === null;
  writingBusy.value = true;
  writingError.value = '';
  saveMessage.value = '';
  try {
    const result = await authorService.save(token.value, path, current.raw, current.version, signal);
    if (signal.aborted) return;
    selectDocument(result);
    saveMessage.value = isNew ? '文章已创建。' : '修改已保存。';
    if (isNew || documents.value.some((item) => item.relative_path === path && item.title !== result.title)) {
      void loadDocuments();
    }
  } catch (error) {
    if (signal.aborted) return;
    writingError.value = error instanceof PublicServiceError && error.code === 'version_conflict'
      ? '文档已在其他位置更新。本页保留你的修改，可复制草稿后重新读取最新文档。'
      : explain(error, '保存请求失败，请重新读取文档确认磁盘内容。');
  } finally {
    if (!signal.aborted) writingBusy.value = false;
  }
}

async function loadQueue(before?: number) {
  const signal = session?.signal;
  if (!signal || queueBusy.value) return;
  queueBusy.value = true;
  moderationError.value = '';
  if (before === undefined) {
    queue.value = [];
    nextBefore.value = null;
  }
  try {
    const result = await authorService.comments(token.value, queueStatus.value, signal, before);
    if (signal.aborted) return;
    queue.value.push(...result.comments);
    nextBefore.value = result.next_before;
  } catch (error) {
    if (!signal.aborted) moderationError.value = explain(error, '留言队列读取失败。');
  } finally {
    if (!signal.aborted) queueBusy.value = false;
  }
}

async function moderate(id: number, status: 'published' | 'rejected') {
  const signal = session?.signal;
  if (!signal || moderating.value !== null || queueBusy.value) return;
  moderating.value = id;
  moderationError.value = '';
  moderationMessage.value = '';
  try {
    await authorService.moderate(token.value, id, status, signal);
    if (signal.aborted) return;
    queue.value = queue.value.filter((item) => item.id !== id);
    moderationMessage.value = status === 'published' ? '留言已公开。' : '留言已移出公开范围。';
    void loadQueue();
  } catch (error) {
    if (!signal.aborted) moderationError.value = explain(error, '审核失败，请重试。');
  } finally {
    if (!signal.aborted) moderating.value = null;
  }
}
</script>

<style scoped>
.author-page { width: min(100% - 36px, 880px); margin: 0 auto; padding: 40px 0 72px; }
.page-heading, .row, .document-tools { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; }
.page-heading { justify-content: space-between; border-bottom: 1px solid var(--site-border); padding-bottom: 16px; }
.page-heading h1 { margin: 0; color: var(--site-reading-heading); font-size: clamp(1.8rem, 4vw, 2.4rem); }
.page-heading p, .hint { margin: 0; color: var(--site-text-secondary); }
.work-area, .login { margin-top: 24px; }
.work-area + .work-area { border-top: 1px solid var(--site-border); padding-top: 24px; }
.work-area h2 { margin-bottom: 8px; color: var(--site-reading-heading); font-size: 1.25rem; }
.document-tools { align-items: flex-end; margin: 12px 0; }
.document-tools .field { flex: 1 1 260px; min-width: 0; }
.editor, .editor-path, .field, .login { display: grid; gap: 6px; }
.editor { margin-top: 18px; }
.login { max-width: 420px; justify-items: start; }
.login input { width: 100%; }
label { font-weight: 700; }
.hint { font-size: .88rem; }
input, textarea, select, button { border: 1px solid var(--site-border); border-radius: var(--ifm-global-radius); font: inherit; }
input, textarea, select { min-width: 0; padding: 6px 10px; color: var(--site-text); background: var(--site-surface); }
textarea { min-height: 16em; padding: 12px; resize: vertical; font: .93rem/1.7 var(--ifm-font-family-monospace); }
button { padding: 5px 10px; color: var(--site-accent-ink); background: var(--site-surface); cursor: pointer; }
button.primary { background: var(--site-accent-soft); }
button:disabled { opacity: .65; cursor: default; }
:is(input, textarea, select, button):focus-visible { outline: 2px solid var(--ifm-color-primary); outline-offset: 2px; }
.error { color: var(--site-danger); }
.queue { list-style: none; margin: 0 0 12px; padding: 0; }
.queue li { padding: 12px 0; border-bottom: 1px solid var(--site-border); overflow-wrap: anywhere; }
.queue li p { margin: 6px 0; white-space: pre-wrap; }
@media (max-width: 480px) { .author-page { padding-top: 24px; } }
</style>
