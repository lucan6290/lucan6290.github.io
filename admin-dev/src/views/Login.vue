<template>
  <div class="login-container">
    <NCard class="login-card" title="博客管理后台">
      <div class="login-content">
        <!-- 模式选择 -->
        <div class="mode-section">
          <NText depth="3">选择工作模式</NText>
          <NSpace vertical :size="16" style="width: 100%">
            <NButton type="primary" size="large" block @click="handleLocalMode">
              本地模式（免登录）
            </NButton>
            <NDivider style="margin: 0">或</NDivider>
            <NButton size="large" block @click="showGitHubLogin = true">
              GitHub 在线模式
            </NButton>
          </NSpace>
        </div>

        <!-- GitHub 登录流程 -->
        <template v-if="showGitHubLogin">
          <!-- 未开始登录 -->
          <div v-if="!authStore.userCode && !authStore.isLoading" class="login-init">
            <NText depth="3" class="login-desc">
              点击下方按钮开始 GitHub 授权登录。
            </NText>
            <NButton type="primary" size="large" @click="handleLogin">
              开始授权
            </NButton>
          </div>

          <!-- 登录中 -->
          <div v-else-if="authStore.isLoading && authStore.userCode" class="login-polling">
            <NSpin size="large" />
            <div class="polling-status">
              <NText>等待授权中...</NText>
            </div>
            <div class="device-code-section">
              <NText depth="3">请前往 GitHub 输入以下授权码：</NText>
              <div class="user-code">{{ authStore.userCode }}</div>
            </div>
            <NButton
              type="primary"
              tag="a"
              :href="authStore.verificationUri"
              target="_blank"
              size="large"
            >
              打开 GitHub 授权页面
            </NButton>
            <NButton text @click="handleCancel" class="cancel-btn">
              取消登录
            </NButton>
          </div>

          <!-- 错误 -->
          <div v-else-if="authStore.loginError" class="login-error">
            <NText type="error">{{ authStore.loginError }}</NText>
            <NButton type="primary" @click="handleRetry">
              重试
            </NButton>
          </div>
        </template>
      </div>
    </NCard>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useModeStore } from '@/stores/mode'
import { NCard, NButton, NText, NSpin, NSpace, NDivider, useMessage } from 'naive-ui'

const router = useRouter()
const authStore = useAuthStore()
const modeStore = useModeStore()
const message = useMessage()

const showGitHubLogin = ref(false)

function handleLocalMode() {
  modeStore.setMode('local')
  router.push('/')
}

async function handleLogin() {
  try {
    await authStore.login()
    message.success('登录成功')
    router.push('/')
  } catch (error) {
    console.error('登录失败:', error)
    if (!authStore.loginError) {
      message.error('登录失败，请重试')
    }
  }
}

function handleCancel() {
  authStore.resetLoginState()
  showGitHubLogin.value = false
}

function handleRetry() {
  authStore.resetLoginState()
  handleLogin()
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 420px;
  max-width: 90vw;
}

.login-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 16px 0;
}

.mode-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  width: 100%;
}

.login-init {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.login-desc {
  text-align: center;
  line-height: 1.6;
}

.login-polling {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.polling-status {
  text-align: center;
}

.device-code-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.user-code {
  font-size: 32px;
  font-weight: bold;
  letter-spacing: 8px;
  font-family: 'Courier New', monospace;
  padding: 12px 24px;
  background: #f5f5f5;
  border-radius: 8px;
  color: #333;
}

.cancel-btn {
  margin-top: 8px;
}

.login-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
</style>