/**
 * 管理端 API 入口。
 *
 * 当前前端只对接 admin/backend 文档声明的 `/api/v1` 接口。
 */
import type {
  BlogAPI,
  DirectoryItem,
  GitOperationResult,
  ImageInfo,
  PostDetail,
  PostInfo
} from '@/types/api'
import { localAPI } from './local'

const api = localAPI as unknown as BlogAPI

export function getAPI(): BlogAPI {
  return api
}

export function getLocalAPI(): BlogAPI {
  return api
}

export async function checkLocalAPIAvailable(): Promise<boolean> {
  try {
    return await localAPI.checkHealth()
  } catch {
    return false
  }
}

export type { BlogAPI, PostInfo, PostDetail, ImageInfo, DirectoryItem, GitOperationResult }
