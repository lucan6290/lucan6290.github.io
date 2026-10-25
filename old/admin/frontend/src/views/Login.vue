<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { localAPI } from '@/api/local'
import { setAuthSession } from '@/utils/auth'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const loading = ref(false)

const form = reactive({
  username: 'admin',
  password: ''
})

const canSubmit = computed(() => form.username.trim().length > 0 && form.password.length > 0 && !loading.value)

async function handleLogin() {
  if (!canSubmit.value) return
  loading.value = true
  try {
    const result = await localAPI.loginAdmin(form.username.trim(), form.password)
    setAuthSession({
      accessToken: result.access_token,
      username: result.username,
      expiresAt: result.expires_at
    })
    message.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.replace(redirect)
  } catch (error) {
    const loginError = error as { message?: string }
    message.error(loginError.message || '登录失败，请检查账号密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-panel">
      <div class="login-brand">
        <span class="brand-mark">箓</span>
        <div>
          <h1>箓川码笺</h1>
          <p>Writing Console</p>
        </div>
      </div>

      <n-form class="login-form" @submit.prevent="handleLogin">
        <n-form-item label="账号">
          <n-input
            v-model:value="form.username"
            autocomplete="username"
            placeholder="管理员账号"
            size="large"
          />
        </n-form-item>

        <n-form-item label="密码">
          <n-input
            v-model:value="form.password"
            autocomplete="current-password"
            placeholder="管理员密码"
            show-password-on="click"
            size="large"
            type="password"
            @keydown.enter.prevent="handleLogin"
          />
        </n-form-item>

        <n-button
          attr-type="submit"
          block
          class="login-button"
          :disabled="!canSubmit"
          :loading="loading"
          size="large"
          type="primary"
        >
          登录
        </n-button>
      </n-form>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  padding: 24px;
  display: grid;
  place-items: center;
}

.login-panel {
  width: min(100%, 390px);
  padding: 30px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.84));
  border: 1px solid var(--admin-line);
  border-radius: 12px;
  box-shadow: var(--admin-shadow-lg);
  backdrop-filter: blur(18px);
}

.login-brand {
  margin-bottom: 26px;
  display: flex;
  align-items: center;
  gap: 13px;
}

.brand-mark {
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.2), transparent 45%),
    linear-gradient(145deg, #1f6c50, #a45e24);
  border-radius: 12px;
  box-shadow: 0 14px 28px rgba(47, 112, 85, 0.25);
  font-size: 22px;
  font-weight: 800;
}

.login-brand h1 {
  margin: 0;
  color: var(--admin-text);
  font-size: 24px;
  line-height: 1.2;
}

.login-brand p {
  margin: 4px 0 0;
  color: var(--admin-muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.login-form {
  display: grid;
  gap: 4px;
}

.login-button {
  margin-top: 6px;
}

@media (max-width: 520px) {
  .login-page {
    padding: 16px;
  }

  .login-panel {
    padding: 24px;
  }
}
</style>
