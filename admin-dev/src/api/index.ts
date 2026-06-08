/**
 * 统一数据接口
 * 根据 mode 自动选择 GitHub API 或本地 API
 */
import type { BlogAPI, PostInfo, PostDetail, ImageInfo, DirectoryItem, GitOperationResult } from '@/types/api'
import { useModeStore } from '@/stores/mode'
import * as githubAPI from './github'
import { localAPI } from './local'

/**
 * 仓库配置（与 github.ts 保持一致）
 */
const REPO_CONFIG = {
  postsPath: 'source/_posts'
} as const

/**
 * GitHub API 适配器
 * 将 GitHub API 转换为统一的 BlogAPI 接口
 */
const githubAPIAdapter: BlogAPI = {
  // 文章管理
  async getPosts(): Promise<PostInfo[]> {
    return githubAPI.getPosts()
  },

  async getPost(path: string): Promise<PostInfo | null> {
    return githubAPI.getPost(path)
  },

  async getPostContent(path: string): Promise<string> {
    return githubAPI.getPostContent(path)
  },

  async createPost(path: string, content: string): Promise<PostDetail> {
    await githubAPI.createPost(path, content)
    // 创建后重新获取文章信息
    const post = await githubAPI.getPost(`${REPO_CONFIG.postsPath}/${path}`)
    if (!post) {
      throw new Error('创建文章后无法获取文章信息')
    }
    return {
      ...post,
      content,
      body: content.split('---\n')[2] || ''
    }
  },

  async updatePost(path: string, content: string, sha?: string): Promise<PostDetail> {
    if (!sha) {
      throw new Error('GitHub API 更新文章需要提供 SHA 值')
    }
    await githubAPI.updatePost(path, content, sha)
    // 更新后重新获取文章信息
    const post = await githubAPI.getPost(`${REPO_CONFIG.postsPath}/${path}`)
    if (!post) {
      throw new Error('更新文章后无法获取文章信息')
    }
    return {
      ...post,
      content,
      body: content.split('---\n')[2] || ''
    }
  },

  async deletePost(path: string, sha?: string): Promise<void> {
    if (!sha) {
      throw new Error('GitHub API 删除文章需要提供 SHA 值')
    }
    await githubAPI.deletePost(path, sha)
  },

  async getCategories(): Promise<DirectoryItem[]> {
    return githubAPI.getCategories()
  },

  async getPostsByCategory(category: string): Promise<PostInfo[]> {
    return githubAPI.getPostsByCategory(category)
  },

  // 图片管理
  async uploadImage(path: string, content: Uint8Array | ArrayBuffer, _filename?: string): Promise<GitOperationResult> {
    const result = await githubAPI.uploadImage(path, content)
    return {
      success: true,
      message: '上传成功',
      commitHash: result.sha,
      htmlUrl: result.html_url
    }
  },

  async deleteImage(path: string, sha?: string): Promise<void> {
    if (!sha) {
      throw new Error('GitHub API 删除图片需要提供 SHA 值')
    }
    await githubAPI.deleteImage(path, sha)
  },

  // Git 操作
  async deploy(message: string, _filePath?: string): Promise<GitOperationResult> {
    // GitHub 模式下 filePath 不适用，整体仓库提交
    const result = await githubAPI.triggerDeploy(message)
    return {
      success: true,
      message: '部署成功',
      commitHash: result.sha,
      htmlUrl: result.html_url
    }
  },

  // 工具方法
  async fileExists(path: string): Promise<boolean> {
    return githubAPI.fileExists(path)
  },

  async getDirectoryContents(path: string): Promise<DirectoryItem[]> {
    return githubAPI.getDirectoryContents(path)
  }
}

/**
 * 本地 API 适配器
 * 将本地 API 转换为统一的 BlogAPI 接口
 */
const localAPIAdapter: BlogAPI = {
  // 文章管理
  async getPosts(): Promise<PostInfo[]> {
    const posts = await localAPI.getPosts()
    // 转换为统一的 PostInfo 格式
    return posts.map((post: any) => ({
      filename: post.filename || post.path?.split('/').pop()?.replace('.md', '') || '',
      path: post.path,
      title: post.title || post.filename || '',
      category: post.category || post.categories?.[0] || '未分类',
      subCategory: post.subCategory || post.categories?.[1] || '',
      categories: post.categories || [],
      tags: post.tags || [],
      date: post.date || post.lastModified || new Date().toISOString(),
      status: post.status || 'draft',
      sha: post.sha,
      size: post.size,
      lastModified: post.lastModified
    }))
  },

  async getPost(path: string): Promise<PostDetail> {
    const detail = await localAPI.getPost(path)
    return {
      filename: detail.filename,
      path: detail.path,
      title: detail.title || detail.filename,
      category: detail.categories?.[0] || '未分类',
      subCategory: detail.categories?.[1],
      tags: detail.tags || [],
      date: detail.lastModified || new Date().toISOString(),
      status: detail.status || 'draft',
      content: detail.content,
      frontMatter: detail.frontMatter as any,
      body: detail.body,
      size: detail.size,
      lastModified: detail.lastModified
    }
  },

  async createPost(path: string, content: string, options?: { prefix1?: string; prefix2?: string; title?: string }): Promise<PostDetail> {
    const detail = await localAPI.createPost(path, content, options)
    return {
      filename: detail.filename,
      path: detail.path,
      title: detail.title || detail.filename,
      category: detail.categories?.[0] || '未分类',
      subCategory: detail.categories?.[1],
      tags: detail.tags || [],
      date: detail.lastModified || new Date().toISOString(),
      status: detail.status || 'draft',
      content: detail.content,
      frontMatter: detail.frontMatter as any,
      body: detail.body,
      size: detail.size,
      lastModified: detail.lastModified
    }
  },

  async updatePost(path: string, content: string): Promise<PostDetail> {
    const detail = await localAPI.updatePost(path, content)
    return {
      filename: detail.filename,
      path: detail.path,
      title: detail.title || detail.filename,
      category: detail.categories?.[0] || '未分类',
      subCategory: detail.categories?.[1],
      tags: detail.tags || [],
      date: detail.lastModified || new Date().toISOString(),
      status: detail.status || 'draft',
      content: detail.content,
      frontMatter: detail.frontMatter as any,
      body: detail.body,
      size: detail.size,
      lastModified: detail.lastModified
    }
  },

  async deletePost(path: string): Promise<void> {
    await localAPI.deletePost(path)
  },

  // 图片管理
  async uploadImage(articlePath: string, imageData: Uint8Array | ArrayBuffer, filename?: string): Promise<ImageInfo> {
    const name = filename || 'image.png'
    // 将 ArrayBuffer 转换为 Uint8Array
    const data = imageData instanceof ArrayBuffer ? new Uint8Array(imageData) : imageData
    return localAPI.uploadImage(articlePath, data, name)
  },

  async deleteImage(path: string): Promise<void> {
    await localAPI.deleteImage(path)
  },

  async getImages(articlePath: string): Promise<ImageInfo[]> {
    return localAPI.getImages(articlePath)
  },

  // Git 操作
  async commit(message: string): Promise<GitOperationResult> {
    return localAPI.commit(message)
  },

  async push(): Promise<GitOperationResult> {
    return localAPI.push()
  },

  async deploy(message: string, filePath?: string): Promise<GitOperationResult> {
    return localAPI.deploy(message, filePath)
  },

  // 工具方法
  async checkHealth(): Promise<boolean> {
    return localAPI.checkHealth()
  }
}

/**
 * 获取当前模式的 API 实例
 * 根据模式自动选择 GitHub API 或本地 API
 * @returns 统一的 BlogAPI 接口
 */
export function getAPI(): BlogAPI {
  const modeStore = useModeStore()

  if (modeStore.isLocal) {
    return localAPIAdapter
  }

  return githubAPIAdapter
}

/**
 * 获取 GitHub API 实例
 * 直接访问 GitHub API，忽略模式设置
 */
export function getGitHubAPI(): BlogAPI {
  return githubAPIAdapter
}

/**
 * 获取本地 API 实例
 * 直接访问本地 API，忽略模式设置
 */
export function getLocalAPI(): BlogAPI {
  return localAPIAdapter
}

/**
 * 检查本地 API 是否可用
 */
export async function checkLocalAPIAvailable(): Promise<boolean> {
  try {
    return await localAPI.checkHealth()
  } catch {
    return false
  }
}

// 导出类型
export type { BlogAPI, PostInfo, PostDetail, ImageInfo, DirectoryItem, GitOperationResult }