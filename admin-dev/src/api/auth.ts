import axios from 'axios'
import { githubConfig } from '@/config/github'
import type { DeviceFlowResponse, TokenResponse, GitHubUser } from '@/types/auth'

// Token 存储 key
const TOKEN_KEY = 'github_token'

/**
 * 初始化 Device Flow
 * 调用 GitHub API 获取 device_code 和 user_code
 */
export async function initDeviceFlow(): Promise<DeviceFlowResponse> {
  const response = await axios.post<DeviceFlowResponse>(
    githubConfig.endpoints.deviceCode,
    {
      client_id: githubConfig.clientId,
      scope: githubConfig.scope
    },
    {
      headers: {
        'Accept': 'application/json'
      }
    }
  )

  return response.data
}

/**
 * 轮询验证授权状态
 * 用户在浏览器授权后，轮询获取 access_token
 */
export async function pollForToken(deviceCode: string): Promise<TokenResponse> {
  const response = await axios.post<TokenResponse>(
    githubConfig.endpoints.accessToken,
    {
      client_id: githubConfig.clientId,
      device_code: deviceCode,
      grant_type: 'urn:ietf:params:oauth:grant-type:device_code'
    },
    {
      headers: {
        'Accept': 'application/json'
      }
    }
  )

  return response.data
}

/**
 * 验证 token 有效性和用户身份
 * 获取用户信息并校验是否为授权用户
 */
export async function verifyToken(token: string): Promise<GitHubUser | null> {
  try {
    const response = await axios.get<GitHubUser>(githubConfig.endpoints.user, {
      headers: {
        'Authorization': `token ${token}`,
        'Accept': 'application/vnd.github.v3+json'
      }
    })

    const user = response.data

    // 校验用户是否为授权的 owner
    if (user.login !== githubConfig.owner) {
      console.error(`用户 ${user.login} 不是授权用户，期望: ${githubConfig.owner}`)
      return null
    }

    return user
  } catch (error) {
    console.error('验证 token 失败:', error)
    return null
  }
}

/**
 * 保存 token 到 localStorage
 */
export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * 从 localStorage 获取 token
 */
export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 清除 token
 */
export function logout(): void {
  localStorage.removeItem(TOKEN_KEY)
}