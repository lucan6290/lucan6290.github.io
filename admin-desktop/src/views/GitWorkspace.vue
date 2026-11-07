<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { gitWorkspaceApi, type GitAction, type GitChange, type GitDiff, type GitPreview,
  type GitPreviewInput, type GitResult, type GitStatus } from '@/api/gitWorkspace'
import GitPatch from '@/components/GitPatch.vue'

const labels: Record<GitAction, string> = { commit: '提交所选文件', update: '更新工作区', push: '推送提交', publish: '发布站点' }
const state = ref<GitStatus | null>(null)
const selected = ref<string[]>([])
const message = ref('')
const activePath = ref('')
const diff = ref<GitDiff | null>(null)
const diffLoading = ref(false)
const diffError = ref('')
const error = ref('')
const result = ref<GitResult | null>(null)
const preview = ref<GitPreview | null>(null)
const confirmation = ref<HTMLElement | null>(null)
const busy = ref(false)
let diffRequest = 0

const changes = computed(() => state.value?.changes ?? [])
const activeChange = computed(() => changes.value.find(item => item.path === activePath.value))
const usableBranch = computed(() => !!state.value?.branch && !state.value.operation && !changes.value.some(item => item.conflicted))
const canChangeScope = computed(() => usableBranch.value && !busy.value && !preview.value)

function messageFor(cause: unknown) {
  return cause instanceof Error ? cause.message : '无法完成 Git 操作'
}

function unavailable(action: GitAction) {
  if (!usableBranch.value) return '需要可操作的本地分支'
  if (action === 'commit') {
    if (!selected.value.length) return '请勾选文件'
    if (!message.value.trim()) return '请填写提交描述'
    return ''
  }
  if (action === 'publish' && !state.value?.publish_configured) return '后端尚未配置 GitHub Pages 发布'
  if (!state.value?.head || !state.value.upstream) return '需要已提交的分支和远程上游'
  if ((action === 'update' || action === 'publish') && changes.value.length) return '需要干净的工作区'
  return ''
}

function select(item: GitChange, event: Event) {
  const checked = (event.target as HTMLInputElement).checked
  selected.value = checked ? [...selected.value, item.path] : selected.value.filter(path => path !== item.path)
}

async function loadDiff(path: string) {
  const request = ++diffRequest
  diff.value = null
  diffError.value = ''
  diffLoading.value = Boolean(path)
  if (!path) return
  try {
    const next = await gitWorkspaceApi.diff(path)
    if (request === diffRequest) diff.value = next
  } catch (cause) {
    if (request === diffRequest) diffError.value = messageFor(cause)
  } finally {
    if (request === diffRequest) diffLoading.value = false
  }
}

watch(activePath, loadDiff)

async function loadStatus() {
  state.value = await gitWorkspaceApi.status()
  selected.value = selected.value.filter(path => changes.value.some(item => item.selectable && item.path === path))
  if (activeChange.value) {
    void loadDiff(activePath.value)
  } else {
    activePath.value = changes.value.find(item => item.selectable || item.conflicted)?.path || ''
  }
}

async function refresh() {
  if (busy.value || preview.value) return
  busy.value = true
  error.value = ''
  try {
    await loadStatus()
  } catch (cause) {
    state.value = null
    activePath.value = ''
    error.value = messageFor(cause)
  } finally {
    busy.value = false
  }
}

async function prepare(action: GitAction) {
  if (busy.value || preview.value || unavailable(action)) return
  busy.value = true
  result.value = null
  error.value = ''
  const input: GitPreviewInput = action === 'commit' ? { action, paths: selected.value, message: message.value.trim() } : { action }
  try {
    preview.value = await gitWorkspaceApi.preview(input)
    await nextTick()
    confirmation.value?.focus()
  } catch (cause) {
    error.value = messageFor(cause)
  } finally {
    busy.value = false
  }
}

async function confirm() {
  if (busy.value || !preview.value) return
  const scope = preview.value
  busy.value = true
  error.value = ''
  try {
    result.value = await gitWorkspaceApi.execute(scope.token)
    if (scope.action === 'commit') {
      selected.value = []
      message.value = ''
    }
  } catch (cause) {
    error.value = messageFor(cause)
  } finally {
    preview.value = null
    try {
      await loadStatus()
    } catch (cause) {
      state.value = null
      activePath.value = ''
      if (!error.value) error.value = messageFor(cause)
    }
    busy.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <div>
    <header class="main-header">
      <h1 class="main-header-title">Git 工作区</h1>
      <button class="btn btn-secondary btn-sm" :disabled="busy || !!preview" @click="refresh">刷新状态</button>
    </header>

    <div class="main-content git-workspace" :aria-busy="busy">
      <p v-if="error" class="git-error" role="alert">{{ error }}</p>
      <p v-if="result" class="git-result" role="status">
        {{ result.message }} <code v-if="result.commit">{{ result.commit }}</code>
      </p>
      <p v-if="busy && !state" role="status">正在读取 Git 状态…</p>

      <template v-if="state">
        <dl class="card git-branch">
          <div><dt>当前分支</dt><dd>{{ state.branch || '分离 HEAD' }}</dd></div>
          <div><dt>本地提交</dt><dd><code>{{ state.head?.slice(0, 12) || '尚无提交' }}</code></dd></div>
          <div><dt>上游分支</dt><dd>{{ state.upstream ? state.upstream.remote + '/' + state.upstream.branch : '未设置' }}</dd></div>
          <div v-if="state.upstream">
            <dt>相对本地跟踪引用</dt>
            <dd v-if="state.upstream.ahead !== null">领先 {{ state.upstream.ahead }} · 落后 {{ state.upstream.behind }}</dd>
            <dd v-else>尚无跟踪记录</dd>
          </div>
        </dl>
        <p v-if="state.operation" class="git-error" role="status">仓库正在进行 {{ state.operation }}，请在本机 Git 中处理。</p>

        <div class="git-layout">
          <section class="card git-files" aria-labelledby="git-files-title">
            <h2 id="git-files-title">工作区变更 <small>{{ changes.length }}</small></h2>
            <p v-if="!changes.length" class="git-secondary">工作区干净。</p>
            <ul v-else class="git-file-list">
              <li v-for="item in changes" :key="item.path" :class="{ active: activePath === item.path }">
                <input type="checkbox" :checked="selected.includes(item.path)" :disabled="!canChangeScope || !item.selectable"
                  :aria-label="'选择 ' + item.path" @change="select(item, $event)" />
                <button type="button" class="git-file" :aria-pressed="activePath === item.path" :disabled="busy" @click="activePath = item.path">
                  <span class="git-path">{{ item.path }}</span>
                  <span class="git-file-state">
                    <span v-if="item.conflicted" class="git-error">冲突</span>
                    <span v-else-if="!item.selectable">此路径不可提交</span>
                    <span v-if="item.staged !== '.'">暂存 {{ item.staged }}</span>
                    <span v-if="item.unstaged === '?'">未跟踪</span>
                    <span v-else-if="item.unstaged !== '.'">工作区 {{ item.unstaged }}</span>
                  </span>
                </button>
              </li>
            </ul>
          </section>

          <section class="card git-diff" aria-labelledby="git-diff-title">
            <h2 id="git-diff-title">文件差异</h2>
            <p v-if="!activeChange" class="git-secondary">选择文件查看差异。</p>
            <template v-else>
              <p class="git-path">{{ activeChange.path }}</p>
              <p v-if="diffLoading" role="status">正在读取差异…</p>
              <p v-if="diffError" class="git-error" role="alert">{{ diffError }}</p>
              <template v-if="diff">
                <h3>已暂存</h3>
                <GitPatch :patch="diff.staged" />
                <p v-if="!diff.staged" class="git-secondary">无已暂存差异。</p>
                <h3>工作区</h3>
                <GitPatch :patch="diff.unstaged" />
                <p v-if="!diff.unstaged" class="git-secondary">无工作区差异。</p>
                <p v-if="diff.truncated" class="git-secondary">差异过长，已截断显示。</p>
              </template>
            </template>
          </section>
        </div>

        <section class="card git-actions" aria-labelledby="git-actions-title">
          <h2 id="git-actions-title">Git 操作</h2>
          <form class="git-action" @submit.prevent="prepare('commit')">
            <label for="git-message">提交描述 · 已选 {{ selected.length }} 个文件</label>
            <p class="git-secondary">每个所选文件将提交完整的工作区版本，包括该文件尚未暂存的修改。</p>
            <input id="git-message" class="input" v-model="message" maxlength="40" placeholder="例如 feat: 更新文章"
              :disabled="!canChangeScope" />
            <button class="btn btn-primary" :disabled="!canChangeScope || !!unavailable('commit')">{{ labels.commit }} · 预览</button>
          </form>
          <div class="git-remote-actions">
            <div class="git-action" v-for="action in (['update', 'push', 'publish'] as const)" :key="action">
              <button class="btn btn-secondary" :disabled="busy || !!preview || !!unavailable(action)"
                @click="prepare(action)">{{ labels[action] }} · 预览</button>
              <small v-if="unavailable(action)" class="git-secondary">{{ unavailable(action) }}</small>
            </div>
          </div>
          <p v-if="busy && !preview" role="status" class="git-secondary">正在读取状态或准备操作…</p>
        </section>

        <section v-if="preview" ref="confirmation" class="card git-confirm" tabindex="-1" aria-labelledby="git-confirm-title">
          <h2 id="git-confirm-title">确认{{ labels[preview.action] }}</h2>
          <dl>
            <div><dt>操作目标</dt><dd>{{ preview.target }}</dd></div>
            <div v-if="preview.remote_address"><dt>远端地址</dt><dd>{{ preview.remote_address }}</dd></div>
            <div v-if="preview.head"><dt>本地当前提交</dt><dd><code>{{ preview.head }}</code></dd></div>
            <div v-if="preview.remote_head"><dt>预览时的远端提交</dt><dd><code>{{ preview.remote_head }}</code></dd></div>
            <div v-if="preview.target_commit"><dt>目标提交</dt><dd><code>{{ preview.target_commit }}</code></dd></div>
            <div v-if="preview.message"><dt>提交描述</dt><dd>{{ preview.message }}</dd></div>
          </dl>
          <template v-if="preview.action === 'commit'">
            <h3>将提交 {{ preview.paths.length }} 个文件</h3>
            <ul class="git-confirm-files"><li v-for="path in preview.paths" :key="path" class="git-path">{{ path }}</li></ul>
            <p>将使用所选文件完整的工作区版本。未选文件的暂存内容会保留。</p>
            <details><summary>查看本次提交的差异</summary><GitPatch :patch="preview.patch" /></details>
            <p v-if="preview.truncated" class="git-secondary">差异过长，已截断显示。</p>
          </template>
          <p v-if="preview.action === 'update'">从上游取回目标提交，仅在可快进时更新当前分支和文件。</p>
          <p v-if="preview.action === 'push'">只推送已提交的历史到上游分支。推送可能触发远端配置的自动部署等工作流。</p>
          <p v-if="preview.action === 'publish'">将向 GitHub 派发站点部署工作流。部署进度可在 Actions 查看。</p>
          <div class="git-confirm-actions">
            <button class="btn btn-secondary" :disabled="busy" @click="preview = null">取消</button>
            <button class="btn btn-primary" :disabled="busy" @click="confirm">{{ busy ? '正在执行…' : '确认' + labels[preview.action] }}</button>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
.git-workspace { display: grid; gap: 1rem; }
.git-workspace h2 { font-size: 1rem; margin: 0 0 0.75rem; }
.git-workspace h3 { font-size: 0.9rem; margin: 0.9rem 0 0.35rem; }
.git-workspace p { margin: 0.45rem 0; }
.git-workspace small, .git-secondary, dt { color: var(--text-secondary); }
.git-error { color: var(--status-error); }
.git-result { color: var(--status-success); }
.git-workspace code, .git-path { font-family: var(--font-mono); overflow-wrap: anywhere; }
.git-branch { display: flex; flex-wrap: wrap; gap: 0.8rem 2rem; margin: 0; }
.git-branch dt, .git-confirm dt { font-size: 0.82rem; }
dd { margin: 0; overflow-wrap: anywhere; }
.git-layout { display: grid; grid-template-columns: minmax(15rem, 1fr) minmax(0, 2fr); gap: 1rem; }
.git-diff, .git-files { min-width: 0; }
.git-file-list { list-style: none; margin: 0; padding: 0; max-height: 28rem; overflow: auto; }
.git-file-list li { display: flex; gap: 0.4rem; align-items: center; border-bottom: 1px solid var(--border-subtle); }
.git-file-list li.active { background: var(--accent-soft-bg); }
.git-file-list input { margin-inline-start: 0.45rem; }
.git-file { flex: 1; min-width: 0; display: grid; gap: 0.2rem; padding: 0.45rem 0.3rem; text-align: start; color: inherit; background: none; border: 0; cursor: pointer; }
.git-file:focus-visible { outline-offset: -2px; }
.git-file-state { display: flex; gap: 0.6rem; color: var(--text-secondary); font-size: 0.78rem; }
.git-action { display: grid; gap: 0.35rem; justify-items: start; }
.git-action .input { width: min(100%, 30rem); }
.git-remote-actions { display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1rem; }
.git-confirm { border-color: var(--accent-primary); scroll-margin-bottom: 1rem; }
.git-confirm dl { display: grid; gap: 0.45rem; }
.git-confirm-files { padding-inline-start: 1.25rem; }
.git-confirm-actions { display: flex; flex-wrap: wrap; gap: 0.65rem; margin-top: 1rem; }
@media (max-width: 860px) {
  .git-layout { grid-template-columns: minmax(0, 1fr); }
  .git-file-list { max-height: 16rem; }
}
</style>
