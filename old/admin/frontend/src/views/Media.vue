<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, h } from 'vue'
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
  useMessage,
  type UploadFileInfo,
  type SelectOption
} from 'naive-ui'
import { usePostsStore } from '@/stores/posts'
import { getAPI } from '@/api/index'
import type { ImageInfo, ImageFolderInfo } from '@/types/api'

const message = useMessage()
const postsStore = usePostsStore()
type SelectValue = string | number | null

// 状态
const isLoading = ref(false)
const isSiderCollapsed = ref(false)
const siderWidth = ref(380)
const isResizingSider = ref(false)
const siderResizeStartX = ref(0)
const siderResizeStartWidth = ref(380)
const selectedPostPath = ref<string | null>(null)
const imageGroups = ref<Map<string, ImageInfo[]>>(new Map())
const imageFolders = ref<ImageFolderInfo[]>([])
const selectedCategory = ref<string | null>(null)
const selectedSubCategory = ref<string | null>(null)
const previewVisible = ref(false)
const previewImageUrl = ref('')
const previewImageInfo = ref<ImageInfo | null>(null)

// 上传相关
const fileList = ref<UploadFileInfo[]>([])
const uploading = ref(false)

const SIDER_MIN_WIDTH = 300
const SIDER_MAX_WIDTH = 560

const siderToggleStyle = computed(() => ({
  left: isSiderCollapsed.value ? '6px' : `${siderWidth.value - 18}px`
}))

const filteredImageFolders = computed(() => {
  return imageFolders.value.filter((folder) => {
    const post = postsStore.getPostByPath(folder.articlePath)
    if (selectedCategory.value && post?.category !== selectedCategory.value) {
      return false
    }
    if (selectedSubCategory.value && post?.subCategory !== selectedSubCategory.value) {
      return false
    }
    return true
  })
})

const folderOptions = computed<SelectOption[]>(() => {
  return filteredImageFolders.value.map((folder) => ({
    label: getFolderOptionLabel(folder),
    value: folder.articlePath,
    disabled: false
  }))
})

const categoryOptions = computed<SelectOption[]>(() => {
  const categories = new Set<string>()
  for (const folder of imageFolders.value) {
    const category = postsStore.getPostByPath(folder.articlePath)?.category
    if (category) categories.add(category)
  }
  return Array.from(categories).sort().map((category) => ({
    label: category,
    value: category
  }))
})

const subCategoryOptions = computed<SelectOption[]>(() => {
  const subCategories = new Set<string>()
  for (const folder of imageFolders.value) {
    const post = postsStore.getPostByPath(folder.articlePath)
    if (!post?.subCategory) continue
    if (selectedCategory.value && post.category !== selectedCategory.value) continue
    subCategories.add(post.subCategory)
  }
  return Array.from(subCategories).sort().map((subCategory) => ({
    label: subCategory,
    value: subCategory
  }))
})

const displayedImageGroups = computed<[string, ImageInfo[]][]>(() => {
  if (selectedPostPath.value) {
    const images = imageGroups.value.get(selectedPostPath.value)
    return images ? [[selectedPostPath.value, images]] : []
  }

  return filteredImageFolders.value
    .map((folder): [string, ImageInfo[]] | null => {
      const images = imageGroups.value.get(folder.articlePath)
      return images ? [folder.articlePath, images] : null
    })
    .filter((group): group is [string, ImageInfo[]] => Boolean(group))
})

const selectedFolder = computed<ImageFolderInfo | undefined>(() => {
  if (!selectedPostPath.value) return undefined
  return imageFolders.value.find((folder) => folder.articlePath === selectedPostPath.value)
})

const selectedResourceLabel = computed(() => {
  if (!selectedPostPath.value) return ''
  return getFolderTitle(selectedPostPath.value)
})

const selectedFolderOptionTitle = computed(() => {
  if (!selectedPostPath.value) return '搜索图片文件夹'
  if (selectedFolder.value) return getFolderOptionLabel(selectedFolder.value)
  return getFolderTitle(selectedPostPath.value)
})

const imageViewTitle = computed(() =>
  selectedPostPath.value ? getFolderTitle(selectedPostPath.value) : '全部图片文件夹'
)

const imageViewHint = computed(() =>
  selectedPostPath.value
    ? getFolderPathLabel(selectedPostPath.value)
    : `共 ${displayedImageGroups.value.length} 个文件夹，${displayedImageGroups.value.reduce((sum, [, images]) => sum + images.length, 0)} 张图片`
)

function handleCategoryChange(value: SelectValue) {
  selectedCategory.value = value === null ? null : String(value)
  selectedSubCategory.value = null
  selectedPostPath.value = null
}

function handleSubCategoryChange(value: SelectValue) {
  selectedSubCategory.value = value === null ? null : String(value)
  selectedPostPath.value = null
}

function clampSiderWidth(width: number) {
  return Math.min(SIDER_MAX_WIDTH, Math.max(SIDER_MIN_WIDTH, width))
}

function handleSiderResizeMove(event: PointerEvent) {
  if (!isResizingSider.value || isSiderCollapsed.value) return
  const viewportLimit = Math.max(SIDER_MIN_WIDTH, window.innerWidth - 520)
  const maxWidth = Math.min(SIDER_MAX_WIDTH, viewportLimit)
  const nextWidth = siderResizeStartWidth.value + event.clientX - siderResizeStartX.value
  siderWidth.value = Math.min(maxWidth, Math.max(SIDER_MIN_WIDTH, nextWidth))
}

function stopSiderResize() {
  if (!isResizingSider.value) return
  isResizingSider.value = false
  document.body.classList.remove('is-resizing-media-sider')
  window.removeEventListener('pointermove', handleSiderResizeMove)
  window.removeEventListener('pointerup', stopSiderResize)
}

function startSiderResize(event: PointerEvent) {
  if (isSiderCollapsed.value) return
  event.preventDefault()
  isResizingSider.value = true
  siderResizeStartX.value = event.clientX
  siderResizeStartWidth.value = siderWidth.value
  siderWidth.value = clampSiderWidth(siderWidth.value)
  document.body.classList.add('is-resizing-media-sider')
  window.addEventListener('pointermove', handleSiderResizeMove)
  window.addEventListener('pointerup', stopSiderResize)
}

function resetSiderWidth() {
  siderWidth.value = 380
}

function getAssetFolderPath(articlePath: string): string {
  return articlePath.replace(/\.md$/i, '')
}

function getPathBasename(path: string): string {
  return getAssetFolderPath(path).split('/').filter(Boolean).pop() || path
}

function getFolderOptionLabel(folder: ImageFolderInfo): string {
  const post = postsStore.getPostByPath(folder.articlePath)
  const title = post?.filename || post?.title || getPathBasename(folder.folderPath)
  return `${title} (${folder.imageCount} 张)`
}

function getOptionText(option: SelectOption): string {
  return typeof option.label === 'string' ? option.label : String(option.value ?? '')
}

function renderSelectOption({ option }: { option: SelectOption }) {
  const text = getOptionText(option)
  return h('div', {
    title: text,
    style: {
      display: 'block',
      minWidth: '360px',
      maxWidth: 'min(72vw, 680px)',
      whiteSpace: 'normal',
      lineHeight: '1.35',
      wordBreak: 'break-all',
      padding: '2px 0'
    }
  }, text)
}

function getFolderTitle(articlePath: string): string {
  const post = postsStore.getPostByPath(articlePath)
  return post?.filename || post?.title || getPathBasename(articlePath)
}

function getFolderPathLabel(articlePath: string): string {
  const folder = imageFolders.value.find((item) => item.articlePath === articlePath)
  return folder?.folderPath || getAssetFolderPath(articlePath)
}

function applyImageFolders(folders: ImageFolderInfo[]) {
  imageFolders.value = folders
  imageGroups.value = new Map(
    folders.map((folder) => [folder.articlePath, folder.images])
  )
}

function upsertImageFolder(articlePath: string, images: ImageInfo[]) {
  const folderPath = getAssetFolderPath(articlePath)
  const existingIndex = imageFolders.value.findIndex((folder) => folder.articlePath === articlePath)

  if (images.length === 0) {
    if (existingIndex !== -1) {
      imageFolders.value.splice(existingIndex, 1)
    }
    const nextGroups = new Map(imageGroups.value)
    nextGroups.delete(articlePath)
    imageGroups.value = nextGroups
    if (selectedPostPath.value === articlePath) {
      selectedPostPath.value = null
    }
    return
  }

  const nextFolder: ImageFolderInfo = {
    folderPath,
    articlePath,
    articleExists: Boolean(postsStore.getPostByPath(articlePath)),
    imageCount: images.length,
    images
  }

  if (existingIndex === -1) {
    imageFolders.value.push(nextFolder)
  } else {
    imageFolders.value.splice(existingIndex, 1, nextFolder)
  }

  const nextGroups = new Map(imageGroups.value)
  nextGroups.set(articlePath, images)
  imageGroups.value = nextGroups
}

// 图片格式限制
const acceptFormats = '.png,.jpg,.gif,.svg'

function getImagePreviewUrl(image: ImageInfo): string {
  return image.url || image.markdownUrl || ''
}

/**
 * 加载所有文章的图片
 */
async function loadAllImages() {
  isLoading.value = true
  applyImageFolders([])

  try {
    const api = getAPI()

    if (api.getImageFolders) {
      const folders = await api.getImageFolders()
      applyImageFolders(folders)
      return
    }

    const results = await Promise.all(
      postsStore.posts.map(async (post) => {
        if (!api.getImages) return null

        try {
          const images = await api.getImages(post.path)
          return images && images.length > 0
            ? {
              folderPath: getAssetFolderPath(post.path),
              articlePath: post.path,
              articleExists: true,
              imageCount: images.length,
              images
            }
            : null
        } catch (error) {
          // 忽略单个文章的图片加载错误
          console.warn(`加载文章 ${post.path} 的图片失败:`, error)
          return null
        }
      })
    )

    applyImageFolders(results.filter((folder): folder is ImageFolderInfo => Boolean(folder)))
  } catch (error) {
    console.error('加载图片失败:', error)
    message.error('加载图片失败')
  } finally {
    isLoading.value = false
  }
}

/**
 * 加载指定文章的图片
 */
async function reloadPostImages(postPath: string) {
  const api = getAPI()
  if (!api.getImages) return

  try {
    const images = await api.getImages(postPath)
    upsertImageFolder(postPath, images || [])
  } catch (error) {
    console.warn(`加载文章 ${postPath} 的图片失败:`, error)
  }
}

/**
 * 加载选中文章的图片
 */
async function loadSelectedPostImages() {
  if (!selectedPostPath.value) return

  isLoading.value = true
  try {
    await reloadPostImages(selectedPostPath.value)
  } finally {
    isLoading.value = false
  }
}

/**
 * 加载当前可见范围的图片。
 * 首屏只加载有资源目录的文章会更理想；当前文章量不大时并发加载即可。
 */
async function loadVisibleImages() {
  await loadAllImages()
}

/**
 * 兼容旧调用：刷新图片列表
 */
async function refreshImages() {
  if (selectedPostPath.value) {
    await loadSelectedPostImages()
    return
  }

  await loadVisibleImages()
}

/**
 * 生成图片文件名
 * 格式：[文章名]-imgN.扩展名
 */
async function generateImageFilename(
  articlePath: string,
  originalFilename: string
): Promise<string> {
  // 获取文件扩展名
  const ext = originalFilename.split('.').pop() || 'png'
  const post = postsStore.getPostByPath(articlePath)
  if (!post) {
    return `${getPathBasename(articlePath)}-img1.${ext}`
  }

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
    message.error('请先选择图片文件夹')
    onError()
    return
  }

  try {
    uploading.value = true
    
    // 读取文件内容
    const fileData = await readFileAsArrayBuffer(file.file)
    
    // 生成文件名
    const filename = await generateImageFilename(selectedPostPath.value, file.name)
    
    const api = getAPI()
    await api.uploadImage(selectedPostPath.value, fileData, filename)
    message.success(`图片上传成功: ${filename}`)
    
    // 刷新图片列表
    await refreshImages()
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
  const markdown = image.markdown || `![${image.name}](${image.markdownUrl || image.name})`
  
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
  previewImageUrl.value = getImagePreviewUrl(image)
  previewVisible.value = true
}

/**
 * 删除图片
 */
async function handleDeleteImage(image: ImageInfo) {
  try {
    isLoading.value = true
    const api = getAPI()
    
    await api.deleteImage(image.path)
    
    message.success('删除成功')
    
    // 刷新图片列表
    await refreshImages()
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
  
  // 验证是否选择了图片文件夹
  if (!selectedPostPath.value) {
    message.error('请先选择图片文件夹')
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

onBeforeUnmount(() => {
  stopSiderResize()
})
</script>

<template>
  <div class="media-page">
    <n-layout has-sider>
      <!-- 左侧：图片文件夹筛选 -->
      <n-layout-sider
        v-model:collapsed="isSiderCollapsed"
        bordered
        :width="siderWidth"
        :collapsed-width="0"
        collapse-mode="width"
        :show-collapsed-content="false"
        :native-scrollbar="false"
        :content-style="isSiderCollapsed ? 'padding: 0;' : 'padding: 20px 16px;'"
        class="media-sider"
        :class="{ resizing: isResizingSider }"
      >
        <div v-if="!isSiderCollapsed" class="sider-inner">
          <div class="sider-header">
            <p class="page-kicker">Assets</p>
            <h3>图片文件夹</h3>
            <p class="hint">仅显示已经包含图片的资源文件夹</p>
          </div>

          <div
            class="all-folders-item"
            :class="{ active: !selectedPostPath }"
            @click="selectedPostPath = null"
          >
            <div>
              <div class="post-title">全部图片</div>
              <div class="post-path">按文章资源文件夹分组展示</div>
            </div>
            <n-tag size="small" type="success">{{ filteredImageFolders.length }} 组</n-tag>
          </div>

          <div class="filter-row">
            <n-select
              v-model:value="selectedPostPath"
              :options="folderOptions"
              placeholder="搜索图片文件夹"
              filterable
              clearable
              size="small"
              :consistent-menu-width="false"
              :render-option="renderSelectOption"
              :title="selectedFolderOptionTitle"
              class="folder-filter"
            />
            <n-select
              :value="selectedCategory"
              :options="categoryOptions"
              placeholder="一级分类"
              clearable
              size="small"
              :consistent-menu-width="false"
              :render-option="renderSelectOption"
              :title="selectedCategory || '一级分类'"
              class="category-filter"
              @update:value="handleCategoryChange"
            />
            <n-select
              :value="selectedSubCategory"
              :options="subCategoryOptions"
              placeholder="二级分类"
              clearable
              :disabled="subCategoryOptions.length === 0"
              size="small"
              :consistent-menu-width="false"
              :render-option="renderSelectOption"
              :title="selectedSubCategory || '二级分类'"
              class="category-filter"
              @update:value="handleSubCategoryChange"
            />
          </div>

          <!-- 图片文件夹统计 -->
          <div v-if="filteredImageFolders.length > 0" class="post-list">
            <div
              v-for="folder in filteredImageFolders"
              :key="folder.folderPath"
              class="post-item"
              :class="{ active: selectedPostPath === folder.articlePath }"
              @click="selectedPostPath = folder.articlePath"
            >
              <div class="post-meta">
                <div class="post-title" :title="getFolderTitle(folder.articlePath)">
                  {{ getFolderTitle(folder.articlePath) }}
                </div>
                <div class="post-path" :title="folder.folderPath">{{ folder.folderPath }}</div>
              </div>
              <n-tag size="small" type="info">
                {{ folder.imageCount }} 张
              </n-tag>
            </div>
          </div>
          <n-empty v-else size="small" description="当前筛选下暂无图片文件夹" />
        </div>
        <div
          v-if="!isSiderCollapsed"
          class="sider-resizer"
          title="拖动调整图片文件夹侧栏宽度，双击恢复默认宽度"
          @pointerdown="startSiderResize"
          @dblclick="resetSiderWidth"
        />
      </n-layout-sider>

      <n-button
        size="tiny"
        quaternary
        class="sider-toggle"
        :class="{ collapsed: isSiderCollapsed }"
        :style="siderToggleStyle"
        :title="isSiderCollapsed ? '展开图片文件夹侧栏' : '收起图片文件夹侧栏'"
        @click="isSiderCollapsed = !isSiderCollapsed"
      >
        {{ isSiderCollapsed ? '›' : '‹' }}
      </n-button>

      <!-- 右侧：图片管理 -->
      <n-layout content-class="media-content" content-style="padding: 24px;">
        <div class="media-toolbar">
          <div>
            <p class="page-kicker">Image Library</p>
            <h2>{{ imageViewTitle }}</h2>
            <p>{{ imageViewHint }}</p>
          </div>

          <n-upload
            v-if="selectedPostPath"
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
          </n-upload>
          <n-tag v-else type="info">选择左侧文件夹后可上传图片</n-tag>
        </div>

        <n-card v-if="selectedPostPath" title="当前文件夹" class="upload-card">
          <template #header-extra>
            <n-tag v-if="selectedFolder" type="primary" size="small">已选择文件夹</n-tag>
          </template>
            <div class="selected-post-info">
              <span>资源文件夹：</span>
              <n-tag type="primary">{{ selectedResourceLabel }}</n-tag>
              <n-tag size="small">{{ selectedFolder?.folderPath || getAssetFolderPath(selectedPostPath) }}</n-tag>
            </div>
            <div class="upload-tip">
              支持 .png, .jpg, .gif, .svg，最多同时上传 10 张，上传后可直接复制 Markdown 引用
            </div>
        </n-card>

        <!-- 图片展示区域 -->
        <n-spin :show="isLoading">
          <div v-if="displayedImageGroups.length === 0" class="empty-images">
            <n-empty description="暂无图片" />
          </div>
          
          <div v-else class="image-groups">
            <n-card
              v-for="[postPath, images] in displayedImageGroups"
              :key="postPath"
              :title="getFolderTitle(postPath)"
              class="image-group-card"
            >
              <template #header-extra>
                <n-tag>{{ getFolderPathLabel(postPath) }}</n-tag>
                <n-tag type="info">{{ images.length }} 张图片</n-tag>
              </template>
              
              <n-image-group>
                <n-grid :cols="4" :x-gap="16" :y-gap="16">
                  <n-gi v-for="image in images" :key="image.path">
                    <div class="image-card">
                      <div class="image-preview" @click="handlePreview(image)">
                        <n-image
                          :src="getImagePreviewUrl(image)"
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
  position: relative;
}

.media-page :deep(.n-layout) {
  height: 100%;
}

.media-page :deep(.n-layout-sider) {
  height: 100%;
  overflow-y: auto;
}

.media-sider {
  position: relative;
  border-right: 1px solid rgba(41, 63, 52, 0.12);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 10px 0 30px rgba(21, 35, 29, 0.04);
  transition: width 0.16s ease;
}

.media-sider.resizing {
  transition: none;
}

.sider-resizer {
  position: absolute;
  top: 0;
  right: -5px;
  z-index: 25;
  width: 10px;
  height: 100%;
  cursor: col-resize;
  touch-action: none;
}

.sider-resizer::after {
  content: "";
  position: absolute;
  top: 18px;
  right: 4px;
  width: 2px;
  height: calc(100% - 36px);
  border-radius: 999px;
  background: rgba(37, 107, 82, 0);
  transition: width 0.18s, background-color 0.18s, box-shadow 0.18s;
}

.sider-resizer:hover::after,
.sider-resizer:active::after {
  width: 3px;
  background: rgba(37, 107, 82, 0.42);
  box-shadow: 0 0 0 4px rgba(37, 107, 82, 0.08);
}

:global(body.is-resizing-media-sider) {
  cursor: col-resize;
  user-select: none;
}

:global(body.is-resizing-media-sider *) {
  cursor: col-resize !important;
}

.sider-toggle {
  position: absolute;
  top: 18px;
  z-index: 20;
  width: 24px;
  height: 28px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.42);
  color: rgba(41, 63, 52, 0.48);
  font-size: 18px;
  line-height: 1;
  box-shadow: none;
  transition: left 0.2s ease, background-color 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
}

.sider-toggle:hover {
  border-color: rgba(37, 107, 82, 0.2);
  background: rgba(255, 255, 255, 0.96);
  color: rgba(37, 107, 82, 0.92);
  box-shadow: var(--admin-shadow-sm);
}

.sider-header {
  margin-bottom: 16px;
}

.sider-header h3 {
  margin: 0 0 8px 0;
  color: #26342e;
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 0;
  line-height: 1.3;
}

.sider-header .hint {
  margin: 0;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.5;
  color: var(--admin-muted);
}

.all-folders-item {
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid rgba(37, 107, 82, 0.14);
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  background: rgba(37, 107, 82, 0.05);
  transition: background-color 0.2s, border-color 0.2s, transform 0.2s;
}

.all-folders-item:hover {
  transform: translateX(2px);
  background: rgba(37, 107, 82, 0.09);
}

.all-folders-item.active {
  border-color: rgba(37, 107, 82, 0.28);
  background: rgba(37, 107, 82, 0.13);
}

.all-folders-item :deep(.n-tag),
.post-item :deep(.n-tag) {
  flex-shrink: 0;
  font-weight: 500;
}

.filter-row {
  display: grid;
  grid-template-columns: minmax(108px, 1fr) minmax(72px, 0.52fr) minmax(72px, 0.52fr);
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(41, 63, 52, 0.1);
  overflow: visible;
}

.filter-row :deep(.folder-filter) {
  min-width: 0;
}

.filter-row :deep(.category-filter) {
  min-width: 0;
}

.filter-row :deep(.n-base-selection-label),
.filter-row :deep(.n-base-selection-placeholder),
.filter-row :deep(.n-base-selection-input) {
  font-size: 12.5px;
  font-weight: 400;
}

.post-list {
  max-height: calc(100% - 174px);
  overflow-y: auto;
  padding-right: 2px;
}

.post-item {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, transform 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.post-item:hover {
  background-color: rgba(47, 112, 85, 0.07);
  transform: translateX(2px);
}

.post-item.active {
  background-color: rgba(47, 112, 85, 0.12);
  border-color: rgba(47, 112, 85, 0.26);
}

.post-meta {
  min-width: 0;
  flex: 1;
}

.post-title {
  overflow: hidden;
  color: #26342e;
  font-size: 14px;
  line-height: 1.48;
  font-weight: 430;
  letter-spacing: 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.post-path {
  margin-top: 4px;
  font-size: 11px;
  line-height: 1.45;
  color: var(--admin-muted);
  font-weight: 400;
  word-break: break-all;
}

.upload-card,
.image-group-card {
  margin-bottom: 18px;
}

.media-page :deep(.media-content) {
  overflow: auto;
}

.media-toolbar {
  margin-bottom: 18px;
  padding: 18px 20px;
  border: 1px solid rgba(41, 63, 52, 0.12);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: var(--admin-shadow-sm);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.media-toolbar h2 {
  margin: 2px 0 6px;
  font-size: 22px;
  line-height: 1.2;
  font-weight: 620;
  letter-spacing: 0;
}

.media-toolbar p {
  margin: 0;
  color: var(--admin-muted);
  font-size: 13px;
  font-weight: 400;
  line-height: 1.55;
}

.selected-post-info {
  margin-bottom: 16px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(37, 107, 82, 0.08);
  border: 1px solid rgba(37, 107, 82, 0.12);
  border-radius: 10px;
}

.upload-tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--admin-muted);
}

.empty-images {
  padding: 60px 0;
  text-align: center;
}

.image-groups {
  /* 图片分组容器 */
}

.image-card {
  border: 1px solid rgba(41, 63, 52, 0.12);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--admin-shadow-sm);
  transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
}

.image-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--admin-shadow-md);
  border-color: rgba(37, 107, 82, 0.2);
}

.image-preview {
  cursor: pointer;
  background:
    linear-gradient(45deg, rgba(31, 52, 43, 0.04) 25%, transparent 25% 75%, rgba(31, 52, 43, 0.04) 75%),
    linear-gradient(45deg, rgba(31, 52, 43, 0.04) 25%, transparent 25% 75%, rgba(31, 52, 43, 0.04) 75%),
    #f5f8f1;
  background-position: 0 0, 8px 8px, 0 0;
  background-size: 16px 16px;
}

.image-info {
  padding: 12px;
}

.image-name {
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--admin-muted);
  font-weight: 500;
}

.preview-content {
  text-align: center;
}

.preview-info {
  margin-top: 16px;
  text-align: left;
  padding: 16px;
  background-color: #f5f8f1;
  border: 1px solid rgba(31, 52, 43, 0.1);
  border-radius: 10px;
}

.preview-info p {
  margin: 8px 0;
  font-size: 14px;
}

@media (max-width: 760px) {
  .media-sider {
    display: none;
  }

  .media-page :deep(.media-content) {
    padding: 16px !important;
  }

  .media-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
