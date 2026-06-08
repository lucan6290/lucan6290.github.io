<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NLayout,
  NLayoutSider,
  NUpload,
  NSelect,
  NButton,
  NGrid,
  NGi,
  NCard,
  NImage,
  NImageGroup,
  NModal,
  NPopconfirm,
  NSpace,
  NSpin,
  NEmpty,
  NTag,
  NIcon,
  useMessage,
  type UploadFileInfo,
  type SelectOption
} from 'naive-ui'
import { usePostsStore } from '@/stores/posts'
import { getAPI } from '@/api/index'
import type { PostInfo, ImageInfo } from '@/types/api'
import { useModeStore } from '@/stores/mode'

const message = useMessage()
const postsStore = usePostsStore()
const modeStore = useModeStore()

// 状态
const isLoading = ref(false)
const selectedPostPath = ref<string | null>(null)
const imageGroups = ref<Map<string, ImageInfo[]>>(new Map())
const previewVisible = ref(false)
const previewImageUrl = ref('')
const previewImageInfo = ref<ImageInfo | null>(null)

// 上传相关
const fileList = ref<UploadFileInfo[]>([])
const uploading = ref(false)

// 文章选项
const postOptions = computed<SelectOption[]>(() => {
  return postsStore.posts.map((post) => ({
    label: post.filename || post.title,
    value: post.path,
    disabled: false
  }))
})

// 选中的文章信息
const selectedPost = computed<PostInfo | undefined>(() => {
  if (!selectedPostPath.value) return undefined
  return postsStore.getPostByPath(selectedPostPath.value)
})

// 图片格式限制
const acceptFormats = '.png,.jpg,.gif,.svg'

/**
 * 加载所有文章的图片
 */
async function loadAllImages() {
  isLoading.value = true
  imageGroups.value.clear()

  try {
    const api = getAPI()
    
    // 遍历所有文章，获取图片
    for (const post of postsStore.posts) {
      try {
        // 只有本地模式支持 getImages
        if (modeStore.isLocal && api.getImages) {
          const images = await api.getImages(post.path)
          if (images && images.length > 0) {
            imageGroups.value.set(post.path, images)
          }
        }
      } catch (error) {
        // 忽略单个文章的图片加载错误
        console.warn(`加载文章 ${post.path} 的图片失败:`, error)
      }
    }
  } catch (error) {
    console.error('加载图片失败:', error)
    message.error('加载图片失败')
  } finally {
    isLoading.value = false
  }
}

/**
 * 获取文章的图片数量
 */
function getImageCount(postPath: string): number {
  return imageGroups.value.get(postPath)?.length || 0
}

/**
 * 获取文章的所有图片
 */
function getPostImages(postPath: string): ImageInfo[] {
  return imageGroups.value.get(postPath) || []
}

/**
 * 生成图片文件名
 * 格式：[文章名]-imgN.扩展名
 */
async function generateImageFilename(
  articlePath: string,
  originalFilename: string
): Promise<string> {
  const post = postsStore.getPostByPath(articlePath)
  if (!post) {
    throw new Error('文章不存在')
  }

  // 获取文件扩展名
  const ext = originalFilename.split('.').pop() || 'png'
  
  // 获取当前文章的图片数量，确定 N 值
  const images = imageGroups.value.get(articlePath) || []
  const nextNumber = images.length + 1

  // 生成文件名：文章名-imgN.扩展名
  // 文章名从文件名中提取（去掉.md扩展名）
  const articleName = post.filename
  
  return `${articleName}-img${nextNumber}.${ext}`
}

/**
 * 处理文件上传
 */
async function handleUpload({ file, onFinish, onError }: any) {
  if (!selectedPostPath.value) {
    message.error('请先选择关联文章')
    onError()
    return
  }

  try {
    uploading.value = true
    
    // 读取文件内容
    const fileData = await readFileAsArrayBuffer(file.file)
    
    // 生成文件名
    const filename = await generateImageFilename(selectedPostPath.value, file.name)
    
    // 调用 API 上传
    const api = getAPI()
    
    // 清理路径：移除可能的 source/_posts/ 前缀
    let cleanPath = selectedPostPath.value
    if (cleanPath.startsWith('source/_posts/')) {
      cleanPath = cleanPath.replace('source/_posts/', '')
    }
    
    if (modeStore.isLocal) {
      // 本地模式：uploadImage(articlePath, imageData, filename)
      await api.uploadImage(cleanPath, fileData, filename)
      message.success(`图片上传成功: ${filename}`)
    } else {
      // GitHub 模式：uploadImage(path, content)
      // 构建图片路径：source/_posts/[分类]/[文章名]/[图片名]
      const imagePath = `source/_posts/${cleanPath.replace('.md', '')}/${filename}`
      await api.uploadImage(imagePath, fileData)
      message.success(`图片上传成功: ${filename}`)
    }
    
    // 刷新图片列表
    await loadAllImages()
    onFinish()
  } catch (error) {
    console.error('上传图片失败:', error)
    message.error(error instanceof Error ? error.message : '上传失败')
    onError()
  } finally {
    uploading.value = false
  }
}

/**
 * 读取文件为 ArrayBuffer
 */
function readFileAsArrayBuffer(file: File): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as ArrayBuffer)
    reader.onerror = () => reject(new Error('读取文件失败'))
    reader.readAsArrayBuffer(file)
  })
}

/**
 * 复制 Markdown 引用路径
 */
async function copyMarkdownPath(image: ImageInfo) {
  // 格式：![描述](文章名-img1.png)
  const markdown = `![${image.name}](${image.name})`
  
  try {
    await navigator.clipboard.writeText(markdown)
    message.success('已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    message.error('复制失败')
  }
}

/**
 * 预览图片
 */
function handlePreview(image: ImageInfo) {
  previewImageInfo.value = image
  previewImageUrl.value = image.url || ''
  previewVisible.value = true
}

/**
 * 删除图片
 */
async function handleDeleteImage(image: ImageInfo) {
  try {
    isLoading.value = true
    const api = getAPI()
    
    if (modeStore.isLocal) {
      await api.deleteImage(image.path)
    } else {
      // GitHub 模式需要 SHA
      if (!image.sha) {
        throw new Error('缺少文件 SHA 值')
      }
      await api.deleteImage(image.path, image.sha)
    }
    
    message.success('删除成功')
    
    // 刷新图片列表
    await loadAllImages()
  } catch (error) {
    console.error('删除图片失败:', error)
    message.error(error instanceof Error ? error.message : '删除失败')
  } finally {
    isLoading.value = false
  }
}

/**
 * 处理上传前验证
 */
function beforeUpload({ file }: { file: UploadFileInfo }) {
  // 验证文件格式
  const allowedExtensions = ['png', 'jpg', 'gif', 'svg']
  const ext = file.name.split('.').pop()?.toLowerCase()
  
  if (!ext || !allowedExtensions.includes(ext)) {
    message.error('只支持 .png, .jpg, .gif, .svg 格式的图片')
    return false
  }
  
  // 验证是否选择了文章
  if (!selectedPostPath.value) {
    message.error('请先选择关联文章')
    return false
  }
  
  return true
}

// 初始化
onMounted(async () => {
  // 加载文章列表
  await postsStore.fetchPosts()
  
  // 加载图片
  await loadAllImages()
})
</script>

<template>
  <div class="media-page">
    <n-layout has-sider>
      <!-- 左侧：文章列表 -->
      <n-layout-sider
        bordered
        :width="280"
        :native-scrollbar="false"
        content-style="padding: 16px;"
      >
        <div class="sider-header">
          <h3>文章列表</h3>
          <p class="hint">选择文章后上传图片</p>
        </div>

        <!-- 文章选择器 -->
        <n-select
          v-model:value="selectedPostPath"
          :options="postOptions"
          placeholder="搜索并选择文章"
          filterable
          clearable
          style="margin-bottom: 16px"
        />

        <!-- 文章图片统计 -->
        <div v-if="postsStore.posts.length > 0" class="post-list">
          <div
            v-for="post in postsStore.posts"
            :key="post.path"
            class="post-item"
            :class="{ active: selectedPostPath === post.path }"
            @click="selectedPostPath = post.path"
          >
            <div class="post-title">{{ post.filename || post.title }}</div>
            <n-tag v-if="getImageCount(post.path) > 0" size="small" type="info">
              {{ getImageCount(post.path) }} 张图片
            </n-tag>
          </div>
        </div>
      </n-layout-sider>

      <!-- 右侧：图片管理 -->
      <n-layout content-style="padding: 16px;">
        <!-- 上传区域 -->
        <n-card title="上传图片" style="margin-bottom: 16px">
          <div v-if="!selectedPostPath" class="upload-hint">
            <n-empty description="请先在左侧选择要关联的文章" />
          </div>
          <div v-else>
            <div class="selected-post-info">
              <span>关联文章：</span>
              <n-tag type="primary">{{ selectedPost?.filename || selectedPost?.title }}</n-tag>
            </div>
            
            <n-upload
              v-model:file-list="fileList"
              :accept="acceptFormats"
              :custom-request="handleUpload"
              :before-upload="beforeUpload"
              multiple
              directory-dnd
              :max="10"
            >
              <n-button type="primary" :loading="uploading">
                选择图片上传
              </n-button>
              <template #tip>
                <div class="upload-tip">
                  支持 .png, .jpg, .gif, .svg 格式，最多同时上传 10 张
                </div>
              </template>
            </n-upload>
          </div>
        </n-card>

        <!-- 图片展示区域 -->
        <n-spin :show="isLoading">
          <div v-if="imageGroups.size === 0" class="empty-images">
            <n-empty description="暂无图片" />
          </div>
          
          <div v-else class="image-groups">
            <n-card
              v-for="[postPath, images] in imageGroups"
              :key="postPath"
              :title="postsStore.getPostByPath(postPath)?.filename || postPath"
              style="margin-bottom: 16px"
            >
              <template #header-extra>
                <n-tag type="info">{{ images.length }} 张图片</n-tag>
              </template>
              
              <n-image-group>
                <n-grid :cols="4" :x-gap="16" :y-gap="16">
                  <n-gi v-for="image in images" :key="image.path">
                    <div class="image-card">
                      <div class="image-preview" @click="handlePreview(image)">
                        <n-image
                          :src="image.url"
                          :alt="image.name"
                          object-fit="cover"
                          width="100%"
                          height="150"
                          lazy
                        />
                      </div>
                      
                      <div class="image-info">
                        <div class="image-name" :title="image.name">
                          {{ image.name }}
                        </div>
                        
                        <n-space justify="space-between" style="margin-top: 8px">
                          <n-button
                            size="small"
                            type="primary"
                            @click="copyMarkdownPath(image)"
                          >
                            复制引用
                          </n-button>
                          
                          <n-popconfirm @positive-click="handleDeleteImage(image)">
                            <template #trigger>
                              <n-button size="small" type="error">
                                删除
                              </n-button>
                            </template>
                            确定要删除这张图片吗？
                          </n-popconfirm>
                        </n-space>
                      </div>
                    </div>
                  </n-gi>
                </n-grid>
              </n-image-group>
            </n-card>
          </div>
        </n-spin>
      </n-layout>
    </n-layout>

    <!-- 图片预览弹窗 -->
    <n-modal
      v-model:show="previewVisible"
      preset="card"
      style="width: 800px"
      title="图片预览"
    >
      <div v-if="previewImageInfo" class="preview-content">
        <n-image
          :src="previewImageUrl"
          :alt="previewImageInfo.name"
          object-fit="contain"
          width="100%"
        />
        <div class="preview-info">
          <p><strong>文件名：</strong>{{ previewImageInfo.name }}</p>
          <p><strong>路径：</strong>{{ previewImageInfo.path }}</p>
          <p v-if="previewImageInfo.size">
            <strong>大小：</strong>{{ (previewImageInfo.size / 1024).toFixed(2) }} KB
          </p>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<style scoped>
.media-page {
  height: 100%;
  overflow: hidden;
}

.media-page :deep(.n-layout) {
  height: 100%;
}

.media-page :deep(.n-layout-sider) {
  height: 100%;
  overflow-y: auto;
}

.sider-header {
  margin-bottom: 16px;
}

.sider-header h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
}

.sider-header .hint {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.post-list {
  max-height: calc(100% - 60px);
  overflow-y: auto;
}

.post-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.post-item:hover {
  background-color: #f5f5f5;
}

.post-item.active {
  background-color: #e8f4ff;
  border: 1px solid #1890ff;
}

.post-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.upload-hint {
  padding: 40px 0;
  text-align: center;
}

.selected-post-info {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

.empty-images {
  padding: 60px 0;
  text-align: center;
}

.image-groups {
  /* 图片分组容器 */
}

.image-card {
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.image-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.image-preview {
  cursor: pointer;
  background-color: #f5f5f5;
}

.image-info {
  padding: 12px;
}

.image-name {
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #666;
}

.preview-content {
  text-align: center;
}

.preview-info {
  margin-top: 16px;
  text-align: left;
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.preview-info p {
  margin: 8px 0;
  font-size: 14px;
}
</style>