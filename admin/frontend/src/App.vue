<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NConfigProvider,
  NMessageProvider,
  NDialogProvider,
  NLayout,
  NMenu,
  NButton,
  type GlobalThemeOverrides,
  type MenuOption
} from 'naive-ui'

const router = useRouter()
const isAppSiderCollapsed = ref(false)

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#256b52',
    primaryColorHover: '#318463',
    primaryColorPressed: '#1d563f',
    primaryColorSuppl: '#256b52',
    infoColor: '#486b86',
    successColor: '#2f7a55',
    warningColor: '#ad6a27',
    errorColor: '#b94b4b',
    borderRadius: '8px',
    fontFamily: '"PingFang SC", "Microsoft YaHei UI", "Noto Sans CJK SC", "Source Han Sans SC", "Aptos", sans-serif',
    textColorBase: '#15231d'
  },
  Card: {
    borderRadius: '12px',
    color: 'rgba(255, 255, 255, 0.86)',
    boxShadow: '0 1px 2px rgba(21, 35, 29, 0.05)'
  },
  Button: {
    borderRadiusMedium: '8px',
    borderRadiusLarge: '10px',
    fontWeight: '600'
  },
  Menu: {
    itemHeight: '44px',
    itemBorderRadius: '10px',
    itemTextColor: '#40514a',
    itemTextColorHover: '#1d563f',
    itemTextColorActive: '#1d563f',
    itemTextColorActiveHover: '#1d563f',
    itemColorActive: 'rgba(37, 107, 82, 0.12)',
    itemColorActiveHover: 'rgba(37, 107, 82, 0.16)',
    itemIconColor: '#6f8178',
    itemIconColorActive: '#1d563f'
  },
  DataTable: {
    thColor: '#f4f7f1',
    thTextColor: '#40514a',
    borderColor: 'rgba(41, 63, 52, 0.08)'
  }
}

// 当前选中菜单
const currentKey = computed(() => router.currentRoute.value.path)

function renderMenuIcon(path: string) {
  return () =>
    h('span', { class: 'menu-icon' }, [
      h(
        'svg',
        {
          viewBox: '0 0 24 24',
          width: '18',
          height: '18',
          fill: 'none',
          stroke: 'currentColor',
          'stroke-width': '2',
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          'aria-hidden': 'true'
        },
        [h('path', { d: path })]
      )
    ])
}

// 菜单选项
const menuOptions: MenuOption[] = [
  {
    label: '仪表盘',
    key: '/',
    icon: renderMenuIcon('M3 13h8V3H3v10Zm10 8h8V3h-8v18ZM3 21h8v-6H3v6Z'),
  },
  {
    label: '文章管理',
    key: '/posts',
    icon: renderMenuIcon('M4 5h16M4 12h16M4 19h10'),
  },
  {
    label: '内容注册表',
    key: '/registry',
    icon: renderMenuIcon('M4 6h16M4 12h16M4 18h16M7 4v4M7 10v4M7 16v4M17 4v4M17 10v4M17 16v4'),
  },
  {
    label: 'AI 辅助写作',
    key: '/ai-writing',
    icon: renderMenuIcon('M12 3v3M12 18v3M4.9 4.9 7 7M17 17l2.1 2.1M3 12h3M18 12h3M4.9 19.1 7 17M17 7l2.1-2.1M9 12a3 3 0 1 0 6 0 3 3 0 0 0-6 0Z'),
  },
  {
    label: '编辑器',
    key: '/editor',
    icon: renderMenuIcon('M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z'),
  },
  {
    label: '图片管理',
    key: '/media',
    icon: renderMenuIcon('M4 5h16v14H4zM8 13l2.5-2.5L14 14l2-2 4 4M8.5 8.5h.01'),
  },
  {
    label: '设置',
    key: '/settings',
    icon: renderMenuIcon('M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5ZM19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1 1.56V21a2 2 0 1 1-4 0v-.08a1.7 1.7 0 0 0-1-1.56 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.56-1H3a2 2 0 1 1 0-4h.08a1.7 1.7 0 0 0 1.56-1 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.56V3a2 2 0 1 1 4 0v.08a1.7 1.7 0 0 0 1 1.56 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9c.1.32.4 1 1.56 1H21a2 2 0 1 1 0 4h-.08a1.7 1.7 0 0 0-1.52 1Z'),
  },
]

function handleMenuClick(key: string) {
  router.push(key)
}

function backToBlog() {
  window.location.href = '/'
}
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-layout has-sider class="admin-layout">
          <n-layout-sider
            v-model:collapsed="isAppSiderCollapsed"
            bordered
            collapse-mode="width"
            :collapsed-width="64"
            :width="184"
            class="app-sider"
            :class="{ collapsed: isAppSiderCollapsed }"
          >
            <div class="sider-header">
              <button class="brand-button" type="button" @click="router.push('/')">
                <span class="brand-mark">箓</span>
                <span>
                  <span class="brand-title">箓川码笺</span>
                  <span class="brand-subtitle">Writing Console</span>
                </span>
              </button>
            </div>

            <button
              class="app-sider-toggle"
              type="button"
              :title="isAppSiderCollapsed ? '展开导航栏' : '收起导航栏'"
              @click="isAppSiderCollapsed = !isAppSiderCollapsed"
            >
              {{ isAppSiderCollapsed ? '›' : '‹' }}
            </button>

            <n-menu
              :value="currentKey"
              :options="menuOptions"
              :collapsed="isAppSiderCollapsed"
              :collapsed-width="64"
              :collapsed-icon-size="20"
              @update:value="handleMenuClick"
            />

            <div class="sider-footer">
              <div class="sider-status">
                <span class="status-dot"></span>
                <span>本地管理模式</span>
              </div>
              <n-button
                size="small"
                type="primary"
                block
                @click="backToBlog"
              >
                返回博客
              </n-button>
            </div>
          </n-layout-sider>

          <n-layout content-class="app-content">
            <router-view />
          </n-layout>
        </n-layout>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
#app {
  font-family: "PingFang SC", "Microsoft YaHei UI", "Noto Sans CJK SC", "Source Han Sans SC", "Aptos", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>

<style scoped>
.admin-layout {
  height: 100vh;
  min-width: 1024px;
}

.app-sider {
  position: relative;
  border-right: 1px solid rgba(31, 52, 43, 0.12);
  box-shadow: 18px 0 44px rgba(31, 45, 38, 0.08);
  overflow: visible;
}

.sider-header {
  padding: 18px 12px 16px;
  border-bottom: 1px solid rgba(31, 52, 43, 0.1);
}

.brand-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  color: #18241f;
  background: transparent;
  border: 0;
  cursor: pointer;
  text-align: left;
}

.brand-mark {
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.2), transparent 45%),
    linear-gradient(145deg, #1f6c50, #a45e24);
  border-radius: 12px;
  box-shadow: 0 14px 28px rgba(47, 112, 85, 0.25);
  font-size: 19px;
  font-weight: 800;
}

.brand-title,
.brand-subtitle {
  display: block;
}

.brand-title {
  font-size: 17px;
  font-weight: 800;
  line-height: 1.2;
}

.brand-subtitle {
  margin-top: 2px;
  color: #7a897f;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.app-sider-toggle {
  position: absolute;
  top: 50%;
  right: -13px;
  z-index: 20;
  width: 28px;
  height: 34px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: rgba(41, 63, 52, 0.46);
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  transform: translateY(-50%);
  transition: background-color 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
  box-shadow: 0 8px 20px rgba(21, 35, 29, 0.08);
}

.app-sider-toggle:hover {
  color: rgba(37, 107, 82, 0.92);
  background: rgba(255, 255, 255, 0.96);
  border-color: rgba(37, 107, 82, 0.2);
  box-shadow: var(--admin-shadow-sm);
}

.app-sider.collapsed .sider-header {
  padding: 18px 8px 16px;
}

.app-sider.collapsed .brand-button {
  justify-content: center;
}

.app-sider.collapsed .brand-button > span:not(.brand-mark),
.app-sider.collapsed .sider-footer {
  display: none;
}

.app-sider.collapsed .brand-mark {
  width: 38px;
  height: 38px;
}

.sider-footer {
  position: absolute;
  bottom: 16px;
  left: 0;
  right: 0;
  padding: 0 12px;
  text-align: center;
}

.sider-status {
  margin-bottom: 10px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #53665c;
  background: rgba(37, 107, 82, 0.08);
  border: 1px solid rgba(37, 107, 82, 0.12);
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #2f7a55;
  box-shadow: 0 0 0 4px rgba(47, 122, 85, 0.12);
}

:deep(.app-content) {
  height: 100vh;
  overflow: auto;
}

:deep(.n-menu) {
  padding: 10px;
}

:deep(.menu-icon) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

:deep(.n-menu-item-content) {
  font-weight: 750;
}

.app-sider:not(.collapsed) :deep(.n-menu-item-content) {
  padding-left: 16px !important;
  padding-right: 12px !important;
}

:deep(.n-menu-item-content.n-menu-item-content--selected) {
  background: rgba(47, 112, 85, 0.12);
}

.app-sider.collapsed :deep(.n-menu) {
  padding: 10px 8px;
}

.app-sider.collapsed :deep(.n-menu-item-content) {
  justify-content: center;
}

@media (max-width: 760px) {
  .admin-layout {
    min-width: 0;
  }

  .app-sider {
    width: 72px !important;
    min-width: 72px !important;
    max-width: 72px !important;
    flex: 0 0 72px !important;
  }

  .sider-header {
    padding: 14px 8px;
  }

  .brand-button {
    justify-content: center;
  }

  .brand-button > span:not(.brand-mark),
  .sider-footer {
    display: none;
  }

  .brand-mark {
    width: 40px;
    height: 40px;
  }

  :deep(.n-menu) {
    padding: 10px 8px;
  }

  :deep(.n-menu-item-content) {
    justify-content: center;
    padding: 0 !important;
  }

  :deep(.n-menu-item-content-header) {
    display: none;
  }
}
</style>
