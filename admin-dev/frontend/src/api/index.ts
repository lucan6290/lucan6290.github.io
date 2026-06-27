/**
 * 统一数据接口
 * 管理后台仅使用本地 API
 */
import type { BlogAPI, PostInfo, PostDetail, ImageInfo, ImageFolderInfo, AssetCleanupResult, DirectoryItem, GitOperationResult } from '@/types/api'
import type {
  AIChatRequest,
  AIChatResponse,
  AgentCommitRequest,
  AgentCommitResponse,
  AgentPlanRequest,
  AgentPlanResponse,
  ArticleIndexScanResult,
  ArticleIndexSummary,
  CategoryRegistryItem,
  EditApplyRequest,
  EditPlanRequest,
  EditPlanResponse,
  KnowledgeQARequest,
  KnowledgeQAResponse,
  WritingMaterialExtractResponse
} from '@/types/ai-writing'
import { localAPI } from './local'

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
      unusedImages: detail.unusedImages as any,
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
      unusedImages: detail.unusedImages as any,
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
      unusedImages: detail.unusedImages as any,
      size: detail.size,
      lastModified: detail.lastModified
    }
  },

  async deletePost(path: string): Promise<void> {
    await localAPI.deletePost(path)
  },

  async getCategoryRegistry(): Promise<CategoryRegistryItem[]> {
    return localAPI.getCategoryRegistry()
  },

  async updateCategoryRegistry(registry: CategoryRegistryItem[]): Promise<CategoryRegistryItem[]> {
    return localAPI.updateCategoryRegistry(registry)
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

  async getImageFolders(): Promise<ImageFolderInfo[]> {
    return localAPI.getImageFolders()
  },

  async scanUnusedImages(articlePath: string, content: string): Promise<AssetCleanupResult> {
    return localAPI.scanUnusedImages(articlePath, content)
  },

  async cleanupUnusedImages(articlePath: string, content: string): Promise<AssetCleanupResult> {
    return localAPI.cleanupUnusedImages(articlePath, content)
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

  async aiChat(payload: AIChatRequest): Promise<AIChatResponse> {
    return localAPI.aiChat(payload)
  },

  async generateAgentPlan(payload: AgentPlanRequest): Promise<AgentPlanResponse> {
    return localAPI.generateAgentPlan(payload)
  },

  async commitAgentPlan(payload: AgentCommitRequest): Promise<AgentCommitResponse> {
    return localAPI.commitAgentPlan(payload)
  },

  async extractWritingMaterial(file: File): Promise<WritingMaterialExtractResponse> {
    return localAPI.extractWritingMaterial(file)
  },

  async generateEditPlan(payload: EditPlanRequest): Promise<EditPlanResponse> {
    return localAPI.generateEditPlan(payload)
  },

  async applyEditPlan(payload: EditApplyRequest): Promise<unknown> {
    return localAPI.applyEditPlan(payload)
  },

  async scanArticleIndex(): Promise<ArticleIndexScanResult> {
    return localAPI.scanArticleIndex()
  },

  async getArticleIndex(): Promise<ArticleIndexSummary> {
    return localAPI.getArticleIndex()
  },

  async knowledgeQA(payload: KnowledgeQARequest): Promise<KnowledgeQAResponse> {
    return localAPI.knowledgeQA(payload)
  },

  // 工具方法
  async checkHealth(): Promise<boolean> {
    return localAPI.checkHealth()
  }
}

/**
 * 获取当前模式的 API 实例
 * 始终返回本地 API
 * @returns 统一的 BlogAPI 接口
 */
export function getAPI(): BlogAPI {
  return localAPIAdapter
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
