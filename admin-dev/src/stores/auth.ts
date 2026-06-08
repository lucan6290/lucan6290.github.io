import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { GitHubUser } from '@/types/auth'
import {
  initDeviceFlow,
  pollForToken,
  verifyToken,
  saveToken,
  getStoredToken,
  logout as logoutApi
} from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(null)
  const user = ref<GitHubUser | null>(null)
  const isLoading = ref(false)

  // 当前登录流程状态
  const deviceCode = ref<string | null>(null)
  const userCode = ref<string | null>(null)
  const verificationUri = ref<string | null>(null)
  const pollingInterval = ref<number | null>(null)
  const loginError = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // Actions

  /**
   * 启动 Device Flow 登录
   */
  async function login(): Promise<void> {
    isLoading.value = true
    loginError.value = null

    try {
      // 1. 初始化 Device Flow
      const response = await initDeviceFlow()
      deviceCode.value = response.device_code
      userCode.value = response.user_code
      verificationUri.value = response.verification_uri

      // 2. 开始轮询
      await startPolling(response.device_code, response.interval)
    } catch (error) {
      console.error('登录失败:', error)
      loginError.value = '初始化登录失败，请重试'
      isLoading.value = false
    }
  }

  /**
   * 开始轮询等待授权
   */
  async function startPolling(code: string, interval: number): Promise<void> {
    // 清除之前的轮询
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
    }

    return new Promise((resolve, reject) => {
      pollingInterval.value = window.setInterval(async () => {
        try {
          const response = await pollForToken(code)

          if (response.access_token) {
            // 授权成功
            clearInterval(pollingInterval.value!)
            pollingInterval.value = null

            // 验证用户身份
            const verifiedUser = await verifyToken(response.access_token)
            if (verifiedUser) {
              token.value = response.access_token
              user.value = verifiedUser
              saveToken(response.access_token)
              isLoading.value = false
              resolve()
            } else {
              loginError.value = '身份验证失败，您不是授权用户'
              isLoading.value = false
              reject(new Error('Unauthorized user'))
            }
          } else if (response.error) {
            // 授权被拒绝或过期
            if (response.error === 'authorization_pending') {
              // 等待用户授权，继续轮询
              return
            } else if (response.error === 'slow_down') {
              // 需要减慢轮询速度
              console.log('需要减慢轮询速度')
            } else if (response.error === 'expired_token') {
              clearInterval(pollingInterval.value!)
              pollingInterval.value = null
              loginError.value = '授权码已过期，请重新登录'
              isLoading.value = false
              reject(new Error('Token expired'))
            } else {
              clearInterval(pollingInterval.value!)
              pollingInterval.value = null
              loginError.value = response.error_description || '授权失败'
              isLoading.value = false
              reject(new Error(response.error))
            }
          }
        } catch (error) {
          console.error('轮询出错:', error)
        }
      }, interval * 1000)
    })
  }

  /**
   * 检查现有 token 是否有效
   */
  async function checkAuth(): Promise<boolean> {
    const storedToken = getStoredToken()
    if (!storedToken) {
      return false
    }

    isLoading.value = true
    try {
      const verifiedUser = await verifyToken(storedToken)
      if (verifiedUser) {
        token.value = storedToken
        user.value = verifiedUser
        return true
      } else {
        // token 无效或用户不匹配，清除
        await logout()
        return false
      }
    } catch (error) {
      console.error('检查认证状态失败:', error)
      await logout()
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 清除认证状态
   */
  async function logout(): Promise<void> {
    // 停止轮询
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }

    token.value = null
    user.value = null
    deviceCode.value = null
    userCode.value = null
    verificationUri.value = null
    loginError.value = null
    isLoading.value = false

    logoutApi()
  }

  /**
   * 重置登录状态
   */
  function resetLoginState(): void {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
    deviceCode.value = null
    userCode.value = null
    verificationUri.value = null
    loginError.value = null
    isLoading.value = false
  }

  return {
    // State
    token,
    user,
    isLoading,
    deviceCode,
    userCode,
    verificationUri,
    loginError,

    // Getters
    isAuthenticated,

    // Actions
    login,
    checkAuth,
    logout,
    resetLoginState
  }
})