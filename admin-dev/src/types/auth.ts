/**
 * GitHub OAuth Device Flow 相关类型定义
 */

/**
 * Device Flow 初始化响应
 */
export interface DeviceFlowResponse {
  device_code: string
  user_code: string
  verification_uri: string
  expires_in: number
  interval: number
}

/**
 * Token 轮询响应
 */
export interface TokenResponse {
  access_token?: string
  token_type?: string
  scope?: string
  error?: string
  error_description?: string
  error_uri?: string
}

/**
 * GitHub 用户信息
 */
export interface GitHubUser {
  id: number
  login: string
  name: string | null
  email: string | null
  avatar_url: string
  html_url: string
  bio: string | null
  company: string | null
  location: string | null
  blog: string | null
  public_repos: number
  public_gists: number
  followers: number
  following: number
  created_at: string
  updated_at: string
}

/**
 * 认证状态
 */
export interface AuthState {
  token: string | null
  user: GitHubUser | null
  isAuthenticated: boolean
  isLoading: boolean
}