<script setup lang="ts">
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const icons = {
  success: 'M5 13l4 4L19 7',
  error: 'M6 18L18 6M6 6l12 12',
  warning: 'M12 9v4m0 4h.01M10.3 3.3l-7 13A2 2 0 0 0 5 20h14a2 2 0 0 0 1.7-3.7l-7-13a2 2 0 0 0-3.4 0z',
  info: 'M12 16v-4m0-4h.01M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20z'
}

const toastClass: Record<string, string> = {
  success: 'toast-success',
  error: 'toast-error',
  warning: 'toast-warning',
  info: 'toast-info'
}
</script>

<template>
  <div class="toast-container" v-if="appStore.toasts.length > 0">
    <div
      v-for="toast in appStore.toasts"
      :key="toast.id"
      class="toast"
      :class="toastClass[toast.type]"
      @click="appStore.dismissToast(toast.id)"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0;">
        <path :d="icons[toast.type]" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>{{ toast.message }}</span>
    </div>
  </div>
</template>
