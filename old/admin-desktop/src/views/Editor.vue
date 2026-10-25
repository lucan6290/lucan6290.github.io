<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'
import { parseFrontMatter, stringifyFrontMatter } from '@/utils/frontmatter'
import type { PostDetail, ArticleType, CategoryDTO, TagDTO } from '@/types/api'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const loading = ref(false)
const saving = ref(false)
const post = ref<PostDetail | null>(null)
const content = ref('')
const isEditMode = ref(false)

// 新建文章表单
const newPost = ref({
  type: 'docs' as ArticleType,
  title: '',
  slug: '',
  description: '',
  categoryPath: '',
  tags: '',
  authors: 'lucan'
})

const categories = ref<CategoryDTO[]>([])
const tags = ref<TagDTO[]>([])

async function loadPost() {
  const id = route.query.id as string
  if (!id) {
    isEditMode.value = false
    post.value = null
    content.value = '---\ntitle: \ndescription: \n---\n\n'
    return
  }
  isEditMode.value = true
  loading.value = true
  try {
    post.value = await api.getPost(id)
    content.value = post.value.content
  } catch {
    appStore.showToast('加载文章失败', 'error')
  } finally {
    loading.value = false
  }
}

async function loadMeta() {
  try {
    const [cats, tagList] = await Promise.allSettled([
      api.getCategories({ includeEmpty: true }),
      api.getTags()
    ])
    if (cats.status === 'fulfilled') categories.value = cats.value
    if (tagList.status === 'fulfilled') tags.value = tagList.value
  } catch {
    // 非关键，静默忽略
  }
}

async function handleSave() {
  if (!content.value.trim()) {
    appStore.showToast('内容不能为空', 'warning')
    return
  }
  saving.value = true
  try {
    if (isEditMode.value && post.value) {
      const updated = await api.updatePost(post.value.id, content.value, post.value.version)
      post.value = updated
      content.value = updated.content
      appStore.showToast('文章已保存', 'success')
    } else {
      // 新建文章
      const { frontMatter } = parseFrontMatter(content.value)
      const title = (frontMatter.title as string) || newPost.value.title
      if (!title) {
        appStore.showToast('请输入文章标题', 'warning')
        saving.value = false
        return
      }
      const created = await api.createPost(
        newPost.value.slug || title,
        content.value,
        {
          type: newPost.value.type,
          title,
          slug: newPost.value.slug || undefined,
          description: newPost.value.description || undefined,
          categoryPath: newPost.value.categoryPath
            ? newPost.value.categoryPath.split('/').filter(Boolean)
            : undefined,
          tags: newPost.value.tags
            ? newPost.value.tags.split(',').map(t => t.trim()).filter(Boolean)
            : undefined,
          authors: newPost.value.type === 'blog'
            ? newPost.value.authors.split(',').map(a => a.trim()).filter(Boolean)
            : undefined
        }
      )
      appStore.showToast('文章已创建', 'success')
      router.replace(`/editor?id=${encodeURIComponent(created.id)}`)
    }
  } catch {
    appStore.showToast('保存失败', 'error')
  } finally {
    saving.value = false
  }
}

function handleInsertFrontMatter() {
  const { body } = parseFrontMatter(content.value)
  const fm: Record<string, unknown> = {
    title: newPost.value.title || '未命名文章',
    description: newPost.value.description || '',
  }
  if (newPost.value.type === 'blog') {
    fm.tags = newPost.value.tags ? newPost.value.tags.split(',').map(t => t.trim()) : []
    fm.authors = newPost.value.authors ? newPost.value.authors.split(',').map(a => a.trim()) : ['lucan']
  }
  content.value = stringifyFrontMatter(fm) + (body || '')
}

onMounted(() => {
  loadPost()
  loadMeta()
})

watch(() => route.query.id, () => loadPost())
</script>

<template>
  <div>
    <div class="main-header">
      <div class="main-header-title">{{ isEditMode ? '编辑文章' : '新建文章' }}</div>
      <div class="main-header-actions">
        <button class="btn btn-secondary btn-sm" @click="router.back()">返回</button>
        <button class="btn btn-primary btn-sm" :disabled="saving" @click="handleSave">
          <span v-if="saving" class="spinner" style="width: 12px; height: 12px;"></span>
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>

    <div class="main-content" v-if="!loading">
      <!-- 新建模式：显示表单 -->
      <div v-if="!isEditMode" class="card" style="margin-bottom: 16px;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <div>
            <label style="display: block; font-size: 13px; font-weight: 500; margin-bottom: 4px;">类型</label>
            <select class="select" v-model="newPost.type">
              <option value="docs">知识库</option>
              <option value="blog">博客</option>
            </select>
          </div>
          <div>
            <label style="display: block; font-size: 13px; font-weight: 500; margin-bottom: 4px;">标题</label>
            <input class="input" v-model="newPost.title" placeholder="文章标题" />
          </div>
          <div>
            <label style="display: block; font-size: 13px; font-weight: 500; margin-bottom: 4px;">Slug</label>
            <input class="input" v-model="newPost.slug" placeholder="url-slug（留空自动生成）" />
          </div>
          <div>
            <label style="display: block; font-size: 13px; font-weight: 500; margin-bottom: 4px;">分类路径</label>
            <input class="input" v-model="newPost.categoryPath" placeholder="如：前端/Vue（用/分隔）" />
          </div>
          <div v-if="newPost.type === 'blog'">
            <label style="display: block; font-size: 13px; font-weight: 500; margin-bottom: 4px;">标签</label>
            <input class="input" v-model="newPost.tags" placeholder="逗号分隔" />
          </div>
          <div v-if="newPost.type === 'blog'">
            <label style="display: block; font-size: 13px; font-weight: 500; margin-bottom: 4px;">作者</label>
            <input class="input" v-model="newPost.authors" placeholder="作者" />
          </div>
        </div>
        <div style="margin-top: 12px;">
          <button class="btn btn-secondary btn-sm" @click="handleInsertFrontMatter">生成 FrontMatter</button>
        </div>
      </div>

      <!-- 编辑器 -->
      <div class="card" style="padding: 0; overflow: hidden;">
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid var(--border-subtle);">
          <span style="font-size: 12px; color: var(--text-secondary);">Markdown 源码编辑</span>
          <span v-if="post" style="font-size: 12px; color: var(--text-tertiary);">{{ post.relativePath }}</span>
        </div>
        <textarea
          v-model="content"
          class="editor-content"
          style="width: 100%; min-height: 500px; padding: 16px; font-family: var(--font-mono); font-size: 13px; line-height: 1.7; border: none; outline: none; resize: vertical; background: var(--bg-panel); color: var(--text-primary);"
          spellcheck="false"
        />
      </div>
    </div>

    <div v-else style="display: flex; align-items: center; justify-content: center; height: 400px;">
      <div class="spinner" style="width: 24px; height: 24px;"></div>
    </div>
  </div>
</template>
