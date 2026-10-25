<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { useAppStore, type ThemeMode } from '@/stores/app'
import type { GitSyncStatusDTO, GitCommandResultDTO, DocusaurusConfigStatusDTO, SidebarStatusDTO } from '@/types/api'

const appStore = useAppStore()

const loading = ref(true)
const activeTab = ref<'git' | 'site' | 'theme' | 'about'>('git')

// Git 同步
const gitSyncStatus = ref<GitSyncStatusDTO | null>(null)
const gitRemoteUrl = ref('')
const gitSshEmail = ref('')
const gitBranch = ref('develop')
const gitBusy = ref(false)
const gitOutput = ref('')

// 站点配置
const docusaurusStatus = ref<DocusaurusConfigStatusDTO | null>(null)
const sidebarStatus = ref<SidebarStatusDTO | null>(null)
const siteBusy = ref(false)
const siteOutput = ref('')

async function loadSettings() {
  loading.value = true
  try {
    const [gitRes, docRes, sidebarRes] = await Promise.allSettled([
      api.getGitSyncStatus(),
      api.getDocusaurusConfigStatus(),
      api.getSidebarStatus()
    ])
    if (gitRes.status === 'fulfilled') {
      gitSyncStatus.value = gitRes.value
      gitRemoteUrl.value = gitRes.value.remote_url || ''
      gitBranch.value = gitRes.value.current_branch || 'develop'
    }
    if (docRes.status === 'fulfilled') docusaurusStatus.value = docRes.value
    if (sidebarRes.status === 'fulfilled') sidebarStatus.value = sidebarRes.value
  } catch {
    appStore.showToast('加载设置失败', 'error')
  } finally {
    loading.value = false
  }
}

async function handleUpdateRemote() {
  if (!gitRemoteUrl.value.trim()) {
    appStore.showToast('请输入远程仓库地址', 'warning')
    return
  }
  gitBusy.value = true
  gitOutput.value = ''
  try {
    const result: GitCommandResultDTO = await api.updateGitRemote(gitRemoteUrl.value)
    gitOutput.value = result.logs + (result.error ? '\n' + JSON.stringify(result.error) : '')
    appStore.showToast(result.status === 'success' ? '远程仓库已更新' : '更新失败', result.status === 'success' ? 'success' : 'error')
    await loadSettings()
  } catch {
    appStore.showToast('操作失败', 'error')
  } finally {
    gitBusy.value = false
  }
}

async function handleCreateSshKey() {
  gitBusy.value = true
  gitOutput.value = ''
  try {
    const result: GitCommandResultDTO = await api.createGitSshKey({
      email: gitSshEmail.value || undefined
    })
    gitOutput.value = result.logs + (result.error ? '\n' + JSON.stringify(result.error) : '')
    appStore.showToast(result.status === 'success' ? 'SSH 密钥已生成' : '生成失败', result.status === 'success' ? 'success' : 'error')
    await loadSettings()
  } catch {
    appStore.showToast('操作失败', 'error')
  } finally {
    gitBusy.value = false
  }
}

async function handleTestSsh() {
  gitBusy.value = true
  gitOutput.value = ''
  try {
    const result: GitCommandResultDTO = await api.testGitSsh()
    gitOutput.value = result.logs + (result.error ? '\n' + JSON.stringify(result.error) : '')
    appStore.showToast(result.status === 'success' ? 'SSH 连接正常' : '连接失败', result.status === 'success' ? 'success' : 'error')
  } catch {
    appStore.showToast('测试失败', 'error')
  } finally {
    gitBusy.value = false
  }
}

async function handlePull() {
  gitBusy.value = true
  gitOutput.value = ''
  try {
    const result: GitCommandResultDTO = await api.pullFromGitHub({ branch: gitBranch.value })
    gitOutput.value = result.logs + (result.error ? '\n' + JSON.stringify(result.error) : '')
    appStore.showToast(result.status === 'success' ? '拉取成功' : '拉取失败', result.status === 'success' ? 'success' : 'error')
  } catch {
    appStore.showToast('操作失败', 'error')
  } finally {
    gitBusy.value = false
  }
}

async function handleSyncSidebars() {
  siteBusy.value = true
  siteOutput.value = ''
  try {
    await api.syncSidebars({ confirm: true, mode: 'append_missing' })
    siteOutput.value = '侧边栏同步完成'
    appStore.showToast('侧边栏同步完成', 'success')
    await loadSettings()
  } catch {
    siteOutput.value = '同步失败'
    appStore.showToast('同步失败', 'error')
  } finally {
    siteBusy.value = false
  }
}

async function handleSyncDocusaurusConfig() {
  siteBusy.value = true
  siteOutput.value = ''
  try {
    await api.syncDocusaurusConfig({ confirm: true, mode: 'all' })
    siteOutput.value = '站点配置已同步'
    appStore.showToast('配置同步完成', 'success')
    await loadSettings()
  } catch {
    siteOutput.value = '同步失败'
    appStore.showToast('同步失败', 'error')
  } finally {
    siteBusy.value = false
  }
}

function setTheme(mode: ThemeMode) {
  appStore.setTheme(mode)
}

onMounted(loadSettings)
</script>

<template>
  <div>
    <div class="main-header">
      <div class="main-header-title">设置</div>
      <div class="main-header-actions">
        <button class="btn btn-secondary btn-sm" @click="loadSettings">刷新</button>
      </div>
    </div>

    <div class="main-content" v-if="!loading">
      <!-- 标签页 -->
      <div class="tabs" style="margin-bottom: 16px;">
        <button class="tab" :class="{ active: activeTab === 'git' }" @click="activeTab = 'git'">Git 同步</button>
        <button class="tab" :class="{ active: activeTab === 'site' }" @click="activeTab = 'site'">站点配置</button>
        <button class="tab" :class="{ active: activeTab === 'theme' }" @click="activeTab = 'theme'">主题</button>
        <button class="tab" :class="{ active: activeTab === 'about' }" @click="activeTab = 'about'">关于</button>
      </div>

      <!-- Git 同步 -->
      <div v-if="activeTab === 'git'" style="display: flex; flex-direction: column; gap: 16px;">
        <div class="card">
          <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px;">Git 同步状态</h3>
          <div v-if="gitSyncStatus" style="display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">已配置</span>
              <span class="badge" :class="gitSyncStatus.remote_url ? 'badge-success' : 'badge-warning'">{{ gitSyncStatus.remote_url ? '是' : '否' }}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">远程仓库</span>
              <span style="font-family: var(--font-mono); font-size: 12px;">{{ gitSyncStatus.remote_url || '-' }}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">分支</span>
              <span>{{ gitSyncStatus.current_branch || '-' }}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">SSH 密钥</span>
              <span class="badge" :class="gitSyncStatus.has_private_key ? 'badge-success' : 'badge-warning'">{{ gitSyncStatus.has_private_key ? '已配置' : '未配置' }}</span>
            </div>
          </div>
          <div v-else class="empty-state" style="padding: 16px;">
            <div class="empty-state-description">无法获取 Git 状态</div>
          </div>
        </div>

        <div class="card">
          <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px;">远程仓库配置</h3>
          <div style="display: flex; gap: 8px; margin-bottom: 12px;">
            <input class="input" v-model="gitRemoteUrl" placeholder="https://github.com/user/repo.git 或 git@github.com:user/repo.git" />
            <button class="btn btn-primary btn-sm" :disabled="gitBusy" @click="handleUpdateRemote">更新</button>
          </div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px;">
              <input class="input" v-model="gitBranch" placeholder="分支名称" />
            </div>
            <button class="btn btn-secondary btn-sm" :disabled="gitBusy" @click="handlePull">
              <span v-if="gitBusy" class="spinner" style="width: 12px; height: 12px;"></span>
              拉取代码
            </button>
          </div>
        </div>

        <div class="card">
          <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px;">SSH 密钥</h3>
          <div style="display: flex; gap: 8px; margin-bottom: 12px;">
            <input class="input" v-model="gitSshEmail" placeholder="邮箱（用于生成密钥）" />
            <button class="btn btn-secondary btn-sm" :disabled="gitBusy" @click="handleCreateSshKey">生成密钥</button>
            <button class="btn btn-secondary btn-sm" :disabled="gitBusy" @click="handleTestSsh">测试连接</button>
          </div>
        </div>

        <div v-if="gitOutput" class="card">
          <div style="font-size: 13px; font-weight: 600; margin-bottom: 8px;">命令输出</div>
          <div class="code-block" style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{{ gitOutput }}</div>
        </div>
      </div>

      <!-- 站点配置 -->
      <div v-if="activeTab === 'site'" style="display: flex; flex-direction: column; gap: 16px;">
        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3 style="font-size: 15px; font-weight: 600;">Docusaurus 配置</h3>
            <button class="btn btn-primary btn-sm" :disabled="siteBusy" @click="handleSyncDocusaurusConfig">
              <span v-if="siteBusy" class="spinner" style="width: 12px; height: 12px;"></span>
              同步配置
            </button>
          </div>
          <div v-if="docusaurusStatus" style="display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">配置文件</span>
              <span class="badge" :class="docusaurusStatus.config_exists ? 'badge-success' : 'badge-warning'">{{ docusaurusStatus.config_exists ? '存在' : '不存在' }}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">导航项</span>
              <span>{{ docusaurusStatus.nav_item_total }}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">断链</span>
              <span class="badge" :class="docusaurusStatus.broken_to_links.length === 0 ? 'badge-success' : 'badge-danger'">{{ docusaurusStatus.broken_to_links.length === 0 ? '无' : docusaurusStatus.broken_to_links.length + ' 个' }}</span>
            </div>
            <div v-if="docusaurusStatus.broken_to_links.length > 0">
              <div style="font-size: 12px; color: var(--status-error); margin-top: 4px;" v-for="(err, i) in docusaurusStatus.broken_to_links" :key="i">· {{ err.to }}</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3 style="font-size: 15px; font-weight: 600;">侧边栏注册状态</h3>
            <button class="btn btn-primary btn-sm" :disabled="siteBusy" @click="handleSyncSidebars">
              <span v-if="siteBusy" class="spinner" style="width: 12px; height: 12px;"></span>
              同步侧边栏
            </button>
          </div>
          <div v-if="sidebarStatus" style="display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">知识库注册</span>
              <span>{{ sidebarStatus.registered_count }} / {{ sidebarStatus.docs_count }}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">未登记</span>
              <span>{{ sidebarStatus.missing_count }}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">孤儿注册</span>
              <span>{{ sidebarStatus.orphan_count }}</span>
            </div>
            <div v-if="sidebarStatus.missing_in_sidebars.length > 0">
              <div style="font-size: 12px; color: var(--status-warning); margin-top: 4px;">未注册: {{ sidebarStatus.missing_in_sidebars.length }} 个</div>
            </div>
            <div v-if="sidebarStatus.orphan_sidebar_ids.length > 0">
              <div style="font-size: 12px; color: var(--status-error); margin-top: 4px;">孤立注册: {{ sidebarStatus.orphan_sidebar_ids.length }} 个</div>
            </div>
          </div>
        </div>

        <div v-if="siteOutput" class="card">
          <div style="font-size: 13px; font-weight: 600; margin-bottom: 8px;">操作结果</div>
          <div class="code-block" style="white-space: pre-wrap;">{{ siteOutput }}</div>
        </div>
      </div>

      <!-- 主题 -->
      <div v-if="activeTab === 'theme'">
        <div class="card" style="max-width: 500px;">
          <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 16px;">外观主题</h3>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <label
              v-for="mode in (['system', 'light', 'dark'] as ThemeMode[])"
              :key="mode"
              class="list-item"
              :style="{ border: appStore.themeMode === mode ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)' }"
            >
              <div class="list-item-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <template v-if="mode === 'system'">
                    <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M12 3v18" stroke="currentColor" stroke-width="1.5"/>
                  </template>
                  <template v-else-if="mode === 'light'">
                    <circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M12 1v2m0 18v2m11-11h-2M3 12H1m17.5-6.5l-2 2m-9 9l-2 2m13 0l-2-2m-9-9l-2-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </template>
                  <template v-else>
                    <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" stroke="currentColor" stroke-width="1.5"/>
                  </template>
                </svg>
              </div>
              <div class="list-item-content">
                <div class="list-item-title">{{ mode === 'system' ? '跟随系统' : mode === 'light' ? '亮色' : '暗色' }}</div>
                <div class="list-item-meta">{{ mode === 'system' ? '根据系统设置自动切换' : mode === 'light' ? '始终使用亮色主题' : '始终使用暗色主题' }}</div>
              </div>
              <div class="list-item-actions">
                <input type="radio" :checked="appStore.themeMode === mode" @change="setTheme(mode)" />
              </div>
            </label>
          </div>
        </div>
      </div>

      <!-- 关于 -->
      <div v-if="activeTab === 'about'">
        <div class="card" style="max-width: 500px;">
          <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px;">关于箓川码笺管理端</h3>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">版本</span>
              <span>0.1.0 (Desktop)</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">技术栈</span>
              <span>Tauri v2 + Vue 3 + FastAPI</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">后端端口</span>
              <span style="font-family: var(--font-mono);">{{ appStore.backendPort || '-' }}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-secondary);">后端状态</span>
              <span class="badge" :class="appStore.backendReady ? 'badge-success' : 'badge-danger'">{{ appStore.backendReady ? '已连接' : '未连接' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else style="display: flex; align-items: center; justify-content: center; height: 300px;">
      <div class="spinner" style="width: 24px; height: 24px;"></div>
    </div>
  </div>
</template>
