<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'
import { formatDate } from '@/utils/postDisplay'
import type { PostInfo, ArticleType } from '@/types/api'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

const loading = ref(true)
const posts = ref<PostInfo[]>([])
const searchQuery = ref('')
const filterType = ref<ArticleType | ''>('')

const filteredPosts = computed(() => {
  let result = posts.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(p =>
      p.title.toLowerCase().includes(q) ||
      p.filename.toLowerCase().includes(q) ||
      p.tags.some(t => t.toLowerCase().includes(q))
    )
  }
  if (filterType.value) {
    result = result.filter(p => p.type === filterType.value)
  }
  return result.sort((a, b) => new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime())
})

async function loadPosts() {
  loading.value = true
  try {
    posts.value = await api.getPosts()
  } catch {
    appStore.showToast('加载文章列表失败', 'error')
  } finally {
    loading.value = false
  }
}

function openEditor(post?: PostInfo) {
  if (post) {
    router.push(`/editor?id=${encodeURIComponent(post.id)}`)
  } else {
    router.push('/editor')
  }
}

async function handleDelete(post: PostInfo) {
  if (!confirm(`确定要删除「${post.title}」吗？`)) return
  try {
    await api.deletePost(post.id, post.sha, { confirm: true })
    appStore.showToast('文章已删除', 'success')
    await loadPosts()
  } catch {
    appStore.showToast('删除失败', 'error')
  }
}

onMounted(() => {
  loadPosts()
  // 如果 URL 带 type 参数
  const type = route.query.type as string
  if (type === 'docs' || type === 'blog') filterType.value = type
})
</script>

<template>
  <div>
    <div class="main-header">
      <div class="main-header-title">文章管理</div>
      <div class="main-header-actions">
        <button class="btn btn-primary btn-sm" @click="openEditor()">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          新建文章
        </button>
      </div>
    </div>

    <div class="main-content">
      <!-- 搜索 + 过滤 -->
      <div style="display: flex; gap: 12px; margin-bottom: 16px;">
        <div class="search-input" style="flex: 1;">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M11 11l3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <input class="input" v-model="searchQuery" placeholder="搜索文章标题、文件名或标签..." />
        </div>
        <select class="select" v-model="filterType" style="width: 140px;">
          <option value="">全部类型</option>
          <option value="docs">知识库</option>
          <option value="blog">博客</option>
        </select>
      </div>

      <!-- 文章列表 -->
      <div v-if="!loading">
        <div v-if="filteredPosts.length === 0" class="empty-state">
          <div class="empty-state-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <path d="M4 4h16v3H4V4zm0 6h16v3H4v-3zm0 6h10v3H4v-3z" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </div>
          <div class="empty-state-title">{{ searchQuery || filterType ? '没有匹配的文章' : '暂无文章' }}</div>
          <div class="empty-state-description">点击「新建文章」开始创建</div>
        </div>

        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>标题</th>
                <th style="width: 80px;">类型</th>
                <th style="width: 120px;">分类</th>
                <th style="width: 100px;">状态</th>
                <th style="width: 120px;">更新时间</th>
                <th style="width: 100px;">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="post in filteredPosts" :key="post.id">
                <td>
                  <div style="font-weight: 500;">{{ post.title }}</div>
                  <div style="font-size: 12px; color: var(--text-tertiary);">{{ post.relativePath }}</div>
                </td>
                <td><span class="badge" :class="post.type === 'blog' ? 'badge-info' : 'badge-success'">{{ post.typeLabel }}</span></td>
                <td>{{ post.categoryLabel }}</td>
                <td><span class="badge" :class="post.displayStatus === 'error' ? 'badge-danger' : post.displayStatus === 'warning' ? 'badge-warning' : 'badge-success'">{{ post.displayStatusLabel }}</span></td>
                <td style="color: var(--text-secondary);">{{ formatDate(post.lastModified) }}</td>
                <td>
                  <div style="display: flex; gap: 4px;">
                    <button class="btn btn-ghost btn-sm" @click="openEditor(post)">编辑</button>
                    <button class="btn btn-ghost btn-sm" style="color: var(--status-error);" @click="handleDelete(post)">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-else style="display: flex; align-items: center; justify-content: center; height: 300px;">
        <div class="spinner" style="width: 24px; height: 24px;"></div>
      </div>
    </div>
  </div>
</template>
