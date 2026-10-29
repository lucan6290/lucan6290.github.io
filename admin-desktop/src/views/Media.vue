<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'
import { formatFileSize, formatDate } from '@/utils/postDisplay'
import type { ImageFolderInfo, ImageInfo } from '@/types/api'

const appStore = useAppStore()

const loading = ref(true)
const folders = ref<ImageFolderInfo[]>([])
const selectedFolder = ref<ImageFolderInfo | null>(null)
const images = ref<ImageInfo[]>([])
const uploading = ref(false)

async function loadFolders() {
  loading.value = true
  try {
    folders.value = await api.getImageFolders()
    if (folders.value.length > 0 && !selectedFolder.value) {
      selectFolder(folders.value[0])
    }
  } catch {
    appStore.showToast('加载图片列表失败', 'error')
  } finally {
    loading.value = false
  }
}

function selectFolder(folder: ImageFolderInfo) {
  selectedFolder.value = folder
  images.value = folder.images
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files.length || !selectedFolder.value) return
  uploading.value = true
  try {
    for (const file of Array.from(input.files)) {
      const buffer = await file.arrayBuffer()
      await api.uploadImage(selectedFolder.value.articlePath, buffer, file.name)
    }
    appStore.showToast('图片上传成功', 'success')
    await loadFolders()
    // 重新选中当前文件夹
    if (selectedFolder.value) {
      const updated = folders.value.find(f => f.articlePath === selectedFolder.value?.articlePath)
      if (updated) selectFolder(updated)
    }
  } catch {
    appStore.showToast('图片上传失败', 'error')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function handleDeleteImage(img: ImageInfo) {
  if (!confirm(`确定要删除图片「${img.name}」吗？`)) return
  try {
    await api.deleteImage(img.path)
    appStore.showToast('图片已删除', 'success')
    await loadFolders()
    if (selectedFolder.value) {
      const updated = folders.value.find(f => f.articlePath === selectedFolder.value?.articlePath)
      if (updated) selectFolder(updated)
    }
  } catch {
    appStore.showToast('删除失败', 'error')
  }
}

function copyMarkdown(img: ImageInfo) {
  if (img.markdown) {
    navigator.clipboard.writeText(img.markdown)
    appStore.showToast('Markdown 已复制', 'success')
  }
}

onMounted(loadFolders)
</script>

<template>
  <div>
    <div class="main-header">
      <div class="main-header-title">媒体库</div>
      <div class="main-header-actions">
        <button class="btn btn-secondary btn-sm" @click="loadFolders">刷新</button>
        <label class="btn btn-primary btn-sm" style="cursor: pointer;" v-if="selectedFolder">
          <span v-if="uploading" class="spinner" style="width: 12px; height: 12px;"></span>
          {{ uploading ? '上传中...' : '上传图片' }}
          <input type="file" accept="image/*" multiple style="display: none;" @change="handleUpload" />
        </label>
      </div>
    </div>

    <div class="main-content" v-if="!loading">
      <div style="display: grid; grid-template-columns: 280px 1fr; gap: 16px; height: 100%;">
        <!-- 文件夹列表 -->
        <div>
          <div style="font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">文章文件夹</div>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <div
              v-for="folder in folders"
              :key="folder.articlePath"
              class="list-item"
              :style="{ background: selectedFolder?.articlePath === folder.articlePath ? 'var(--bg-element)' : 'var(--bg-panel)', border: selectedFolder?.articlePath === folder.articlePath ? '1px solid var(--border-strong)' : '1px solid var(--border-subtle)' }"
              @click="selectFolder(folder)"
            >
              <div class="list-item-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" stroke="currentColor" stroke-width="1.5"/>
                </svg>
              </div>
              <div class="list-item-content">
                <div class="list-item-title" style="font-size: 13px;">{{ folder.articlePath }}</div>
                <div class="list-item-meta">{{ folder.imageCount }} 张图片</div>
              </div>
            </div>
          </div>
          <div v-if="folders.length === 0" class="empty-state" style="padding: 24px;">
            <div class="empty-state-description">暂无图片文件夹</div>
          </div>
        </div>

        <!-- 图片网格 -->
        <div>
          <div v-if="images.length === 0" class="empty-state">
            <div class="empty-state-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M3 5h18v14H3V5zm2 2v10h14V7H5zm2 7l3-4 3 3 2-2 3 3H7z" stroke="currentColor" stroke-width="1.5"/>
              </svg>
            </div>
            <div class="empty-state-title">暂无图片</div>
            <div class="empty-state-description">选择文件夹后可上传图片</div>
          </div>
          <div v-else style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px;">
            <div v-for="img in images" :key="img.path" class="card card-hover" style="padding: 8px; text-align: center;">
              <div style="aspect-ratio: 1; display: flex; align-items: center; justify-content: center; background: var(--bg-element); border-radius: var(--radius-md); margin-bottom: 8px; overflow: hidden;">
                <img :src="img.url" :alt="img.name" style="max-width: 100%; max-height: 100%; object-fit: contain;" />
              </div>
              <div style="font-size: 12px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ img.name }}</div>
              <div style="font-size: 11px; color: var(--text-tertiary); margin-bottom: 4px;">{{ formatFileSize(img.size) }}</div>
              <div style="display: flex; gap: 4px; justify-content: center;">
                <button class="btn btn-ghost btn-sm" style="padding: 2px 6px;" @click="copyMarkdown(img)" title="复制 Markdown">复制</button>
                <button class="btn btn-ghost btn-sm" style="padding: 2px 6px; color: var(--status-error);" @click="handleDeleteImage(img)" title="删除">删除</button>
              </div>
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
