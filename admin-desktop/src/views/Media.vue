<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { contentApi } from '@/api/content'
import { mediaApi, type ArticleImage, type MediaDeletePlan } from '@/api/media'
import MediaThumbnail from '@/components/MediaThumbnail.vue'
import type { DocumentSummary } from '@/types/content'

const route = useRoute()
const articles = ref<DocumentSummary[]>([])
const article = ref('')
const images = ref<ArticleImage[]>([])
const selected = ref<ArticleImage | null>(null)
const plan = ref<MediaDeletePlan | null>(null)
const error = ref('')
const notice = ref('')
const loading = ref(false)
const changing = ref(false)

function failure(cause: unknown) {
  return cause instanceof Error ? cause.message : '媒体库请求失败'
}

async function refresh(path = article.value) {
  selected.value = null
  plan.value = null
  images.value = []
  error.value = ''
  if (!path) return
  loading.value = true
  try {
    const result = await mediaApi.list(path)
    if (article.value === path) images.value = result.images
  } catch (cause) {
    if (article.value === path) error.value = failure(cause)
  } finally {
    if (article.value === path) loading.value = false
  }
}

watch(article, path => { void refresh(path) })
onMounted(async () => {
  try {
    articles.value = (await contentApi.list()).documents
    const current = route.query.document
    if (typeof current === 'string' && articles.value.some(item => item.relative_path === current)) article.value = current
  } catch (cause) { error.value = failure(cause) }
})

async function copy(image: ArticleImage) {
  try {
    await navigator.clipboard.writeText(image.markdown)
    notice.value = '已复制 Markdown 引用，可粘贴到该文档。'
  } catch { error.value = '复制失败，请手动选中并复制引用。' }
}

async function previewDelete(image: ArticleImage) {
  changing.value = true
  error.value = ''
  notice.value = ''
  try { plan.value = await mediaApi.deletePlan(image.relative_path) }
  catch (cause) { error.value = failure(cause) }
  finally { changing.value = false }
}

async function remove() {
  if (!plan.value) return
  changing.value = true
  error.value = ''
  try {
    await mediaApi.remove(plan.value)
    await refresh()
    notice.value = '图片已删除。'
  } catch (cause) {
    plan.value = null
    error.value = failure(cause)
  } finally { changing.value = false }
}
</script>

<template>
  <div>
    <header class="main-header">
      <h1 class="main-header-title">媒体库</h1>
      <div class="main-header-actions">
        <RouterLink v-if="article" class="btn btn-secondary btn-sm" :to="{ name: 'Editor', query: { id: article } }">打开文档</RouterLink>
        <button v-if="article" class="btn btn-secondary btn-sm" :disabled="loading || changing" @click="refresh()">刷新</button>
      </div>
    </header>
    <div class="main-content">
      <label class="media-selector">按文档浏览
        <select v-model="article" class="select" :disabled="changing">
          <option value="">选择文档</option>
          <option v-for="item in articles" :key="item.relative_path" :value="item.relative_path">{{ item.title }} · {{ item.relative_path }}</option>
        </select>
      </label>
      <p v-if="error" role="alert">{{ error }}</p>
      <p v-if="notice" role="status">{{ notice }}</p>
      <p v-if="!article">请选择文档查看其配图。可从编辑器导入图片。</p>
      <p v-else-if="loading" role="status">正在读取配图…</p>
      <p v-else-if="!images.length && !error">该文档暂无配图。</p>
      <ul v-else class="media-grid">
        <li v-for="image in images" :key="image.relative_path" class="card media-card">
          <strong>{{ image.name }}</strong>
          <code>{{ image.markdown }}</code>
          <div class="media-actions">
            <button class="btn btn-secondary btn-sm" :disabled="changing" @click="selected = image">预览</button>
            <button class="btn btn-secondary btn-sm" :disabled="changing" @click="copy(image)">复制引用</button>
            <button class="btn btn-secondary btn-sm" :disabled="changing" @click="previewDelete(image)">查看删除影响</button>
          </div>
        </li>
      </ul>
      <section v-if="selected" class="card media-preview" aria-label="图片预览">
        <div class="media-actions">
          <strong>{{ selected.name }}</strong>
          <button class="btn btn-secondary btn-sm" @click="selected = null">关闭预览</button>
        </div>
        <MediaThumbnail :path="selected.relative_path" :name="selected.name" />
      </section>
      <section v-if="plan" class="card media-preview" aria-labelledby="delete-image-title">
        <h2 id="delete-image-title">删除图片</h2>
        <p>{{ plan.relative_path }}</p>
        <template v-if="plan.references.length">
          <p>以下文档引用此图片。删除后原引用保留，读者将无法加载图片。</p>
          <ul><li v-for="reference in plan.references" :key="reference.relative_path">{{ reference.relative_path }}（{{ reference.count }} 处）</li></ul>
        </template>
        <p v-else>未在内容库 Markdown 中发现引用。</p>
        <div class="media-actions">
          <button class="btn btn-secondary btn-sm" :disabled="changing" @click="plan = null">取消</button>
          <button class="btn btn-primary btn-sm" :disabled="changing" @click="remove">确认删除</button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.media-selector { display: grid; gap: 8px; max-width: 36rem; }
.media-grid { padding: 0; list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; }
.media-card { display: grid; gap: 12px; overflow-wrap: anywhere; }
.media-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.media-preview { margin-top: 12px; overflow-wrap: anywhere; }
.media-preview img { display: block; max-width: 100%; max-height: 50vh; margin-top: 12px; }
</style>
