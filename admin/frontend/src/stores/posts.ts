/**
 * 文章索引缓存 Store
 * 管理文章列表的缓存和刷新
 */
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { PostInfo } from '@/types/api'
import { getAPI } from '@/api/index'
import { getPostCategoryLabel, getPostDisplayStatus } from '@/utils/postDisplay'

/**
 * 缓存有效期（5分钟）
 */
const CACHE_DURATION = 5 * 60 * 1000 // 5 分钟

export const usePostsStore = defineStore('posts', () => {
  // State
  const posts = ref<PostInfo[]>([])
  const isLoading = ref(false)
  const lastUpdate = ref<number>(0)
  const error = ref<string | null>(null)

  // Getters

  /**
   * 缓存是否过期
   */
  const isCacheExpired = computed(() => {
    if (lastUpdate.value === 0) return true
    return Date.now() - lastUpdate.value > CACHE_DURATION
  })

  /**
   * 是否有缓存
   */
  const hasCache = computed(() => posts.value.length > 0)

  /**
   * 按分类分组的文章
   */
  const postsByCategory = computed(() => {
    const grouped: Record<string, PostInfo[]> = {}
    for (const post of posts.value) {
      const category = getPostCategoryLabel(post)
      if (!grouped[category]) {
        grouped[category] = []
      }
      grouped[category].push(post)
    }
    return grouped
  })

  /**
   * 按标签分组的文章
   */
  const postsByTag = computed(() => {
    const grouped: Record<string, PostInfo[]> = {}
    for (const post of posts.value) {
      if (post.tags && post.tags.length > 0) {
        for (const tag of post.tags) {
          if (!grouped[tag]) {
            grouped[tag] = []
          }
          grouped[tag].push(post)
        }
      }
    }
    return grouped
  })

  /**
   * 草稿文章
   */
  const drafts = computed(() =>
    posts.value.filter((post) => getPostDisplayStatus(post).value !== 'ok')
  )

  /**
   * 已发布文章
   */
  const published = computed(() =>
    posts.value.filter((post) => getPostDisplayStatus(post).value === 'ok')
  )

  // Actions

  /**
   * 获取文章列表并缓存
   * 如果缓存未过期且存在缓存，则直接返回缓存
   * @param force 是否强制刷新
   */
  async function fetchPosts(force = false): Promise<PostInfo[]> {
    // 如果有缓存且未过期，且不强制刷新，则返回缓存
    if (!force && hasCache.value && !isCacheExpired.value) {
      return posts.value
    }

    // 如果正在加载，等待加载完成
    if (isLoading.value) {
      // 等待加载完成
      return new Promise((resolve) => {
        const unwatch = watch(isLoading, (loading) => {
          if (!loading) {
            unwatch()
            resolve(posts.value)
          }
        })
      })
    }

    isLoading.value = true
    error.value = null

    try {
      const api = getAPI()
      const result = await api.getPosts()
      posts.value = result
      lastUpdate.value = Date.now()
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '获取文章列表失败'
      error.value = errorMessage
      console.error('获取文章列表失败:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 强制刷新缓存
   */
  async function refreshPosts(): Promise<PostInfo[]> {
    return fetchPosts(true)
  }

  /**
   * 从缓存中获取单个文章
   * @param path 文章路径
   */
  function getPostByPath(path: string): PostInfo | undefined {
    return posts.value.find((post) => post.path === path)
  }

  /**
   * 从缓存中获取文章（按标题）
   * @param title 文章标题
   */
  function getPostByTitle(title: string): PostInfo | undefined {
    return posts.value.find((post) => post.title === title)
  }

  /**
   * 从缓存中获取文章（按分类）
   * @param category 分类名称
   */
  function getPostsByCategory(category: string): PostInfo[] {
    return posts.value.filter((post) => getPostCategoryLabel(post) === category)
  }

  /**
   * 从缓存中获取文章（按标签）
   * @param tag 标签名称
   */
  function getPostsByTag(tag: string): PostInfo[] {
    return posts.value.filter((post) => post.tags?.includes(tag))
  }

  /**
   * 从缓存中获取文章（按状态）
   * @param status 文章状态
   */
  function getPostsByStatus(status: 'ok' | 'warning' | 'error'): PostInfo[] {
    return posts.value.filter((post) => getPostDisplayStatus(post).value === status)
  }

  /**
   * 更新缓存中的文章
   * @param path 文章路径
   * @param updates 更新内容
   */
  function updatePostInCache(path: string, updates: Partial<PostInfo>): void {
    const index = posts.value.findIndex((post) => post.path === path)
    if (index !== -1) {
      posts.value[index] = { ...posts.value[index], ...updates }
    }
  }

  /**
   * 从缓存中移除文章
   * @param path 文章路径
   */
  function removePostFromCache(path: string): void {
    const index = posts.value.findIndex((post) => post.path === path)
    if (index !== -1) {
      posts.value.splice(index, 1)
    }
  }

  /**
   * 添加文章到缓存
   * @param post 文章信息
   */
  function addPostToCache(post: PostInfo): void {
    // 检查是否已存在
    const index = posts.value.findIndex((p) => p.path === post.path)
    if (index !== -1) {
      // 已存在，更新
      posts.value[index] = post
    } else {
      // 不存在，添加到开头
      posts.value.unshift(post)
    }
  }

  /**
   * 清空缓存
   */
  function clearCache(): void {
    posts.value = []
    lastUpdate.value = 0
    error.value = null
  }

  /**
   * 搜索文章
   * @param keyword 搜索关键词
   */
  function searchPosts(keyword: string): PostInfo[] {
    if (!keyword.trim()) {
      return posts.value
    }

    const lowerKeyword = keyword.toLowerCase()
    return posts.value.filter((post) => {
      return (
        post.title.toLowerCase().includes(lowerKeyword) ||
        post.description?.toLowerCase().includes(lowerKeyword) ||
        post.tags?.some((tag) => tag.toLowerCase().includes(lowerKeyword)) ||
        getPostCategoryLabel(post).toLowerCase().includes(lowerKeyword)
      )
    })
  }

  return {
    // State
    posts,
    isLoading,
    lastUpdate,
    error,

    // Getters
    isCacheExpired,
    hasCache,
    postsByCategory,
    postsByTag,
    drafts,
    published,

    // Actions
    fetchPosts,
    refreshPosts,
    getPostByPath,
    getPostByTitle,
    getPostsByCategory,
    getPostsByTag,
    getPostsByStatus,
    updatePostInCache,
    removePostFromCache,
    addPostToCache,
    clearCache,
    searchPosts
  }
})
