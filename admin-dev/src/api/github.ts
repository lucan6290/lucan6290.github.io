/**
 * GitHub API 封装
 * 使用 Octokit 操作 GitHub 仓库
 */
import { Octokit } from 'octokit'
import { useAuthStore } from '@/stores/auth'
import type {
  PostInfo,
  PostFrontMatter,
  DirectoryItem,
  CommitResponse
} from '@/types/github'
/**
 * 轻量 Front Matter 解析（浏览器兼容，不依赖 gray-matter）
 */
function parseMatter(content: string): { data: Record<string, unknown>; content: string } {
  const trimmed = content.replace(/^﻿/, '')
  const match = trimmed.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/)
  if (!match) {
    return { data: {}, content: trimmed }
  }
  const yaml = match[1]
  const body = trimmed.slice(match[0].length)
  // 复用 frontmatter.ts 的解析逻辑
  const data: Record<string, unknown> = {}
  let currentKey = ''
  const currentList: unknown[] = []

  function flushList() {
    if (currentKey && currentList.length > 0) {
      data[currentKey] = currentList
      currentKey = ''
      currentList.length = 0
    }
  }

  for (const rawLine of yaml.split(/\r?\n/)) {
    if (rawLine.trim() === '') continue
    const listMatch = rawLine.match(/^(\s+)-\s+(.*)$/)
    if (listMatch) {
      let val: unknown = listMatch[2].trim()
      const arrMatch = (val as string).match(/^\[(.*)\]$/)
      if (arrMatch) {
        val = arrMatch[1].split(',').map((s: string) => s.trim())
      } else if (val === 'true') val = true
      else if (val === 'false') val = false
      else if (/^\d+$/.test(val as string)) val = Number(val)
      currentList.push(val)
      continue
    }
    flushList()
    const kvMatch = rawLine.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$/)
    if (kvMatch) {
      const key = kvMatch[1]
      const val = kvMatch[2].trim()
      if (val === '') {
        currentKey = key
        continue
      }
      if (val === 'true') data[key] = true
      else if (val === 'false') data[key] = false
      else if (/^\d+$/.test(val)) data[key] = Number(val)
      else {
        // 内联数组格式：[a, b, c]
        const inlineArrMatch = val.match(/^\[(.*)\]$/)
        if (inlineArrMatch) {
          data[key] = inlineArrMatch[1].split(',').map((s: string) => s.trim())
        } else {
          data[key] = val
        }
      }
    }
  }
  flushList()

  return { data, content: body }
}

/**
 * 仓库配置
 */
const REPO_CONFIG = {
  owner: 'lucan6290',
  repo: 'lucan6290.github.io',
  branch: 'main',
  postsPath: 'source/_posts'
} as const

/**
 * Base64 编码（浏览器兼容）
 */
function base64Encode(str: string): string {
  // 使用 TextEncoder 将字符串转换为 UTF-8 字节
  const bytes = new TextEncoder().encode(str)
  // 转换为二进制字符串
  let binary = ''
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  // 使用 btoa 编码为 Base64
  return btoa(binary)
}

/**
 * Base64 解码（浏览器兼容）
 */
function base64Decode(base64: string): string {
  // 使用 atob 解码 Base64
  const binary = atob(base64)
  // 转换为 UTF-8 字节
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  // 使用 TextDecoder 转换为字符串
  return new TextDecoder().decode(bytes)
}

/**
 * Buffer 转 Base64（浏览器兼容）
 */
function bufferToBase64(buffer: Uint8Array | ArrayBuffer): string {
  const bytes = buffer instanceof ArrayBuffer ? new Uint8Array(buffer) : buffer
  let binary = ''
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

/**
 * 获取 Octokit 实例
 * 从 auth store 中获取 token 创建实例
 */
function getOctokit(): Octokit {
  const authStore = useAuthStore()
  const token = authStore.token

  if (!token) {
    throw new Error('未授权：请先登录 GitHub')
  }

  return new Octokit({
    auth: token
  })
}

/**
 * 解析文章 Front Matter
 */
function parseFrontMatter(content: string): { frontMatter: PostFrontMatter; body: string } {
  try {
    const { data, content: body } = parseMatter(content)
    return {
      frontMatter: data as unknown as PostFrontMatter,
      body
    }
  } catch (error) {
    console.error('解析 Front Matter 失败:', error)
    throw new Error('文章格式错误：无法解析 Front Matter')
  }
}

/**
 * 获取所有文章列表
 * 遍历 source/_posts/ 目录下的所有分类目录
 */
export async function getPosts(): Promise<PostInfo[]> {
  const octokit = getOctokit()
  const posts: PostInfo[] = []

  try {
    // 获取 _posts 目录下的所有分类目录
    const { data: categories } = await octokit.rest.repos.getContent({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path: REPO_CONFIG.postsPath,
      ref: REPO_CONFIG.branch
    })

    // 如果不是数组，说明不是目录
    if (!Array.isArray(categories)) {
      return posts
    }

    // 遍历每个分类目录
    for (const category of categories) {
      if (category.type !== 'dir') continue

      // 获取分类目录下的所有文件
      const { data: files } = await octokit.rest.repos.getContent({
        owner: REPO_CONFIG.owner,
        repo: REPO_CONFIG.repo,
        path: category.path,
        ref: REPO_CONFIG.branch
      })

      if (!Array.isArray(files)) continue

      // 筛选出 .md 文件
      const mdFiles = files.filter(
        (file) => file.type === 'file' && file.name.endsWith('.md')
      )

      // 获取每个文章的内容并解析
      for (const file of mdFiles) {
        try {
          const content = await getPost(file.path)
          if (content) {
            posts.push(content)
          }
        } catch (error) {
          console.error(`获取文章 ${file.path} 失败:`, error)
        }
      }
    }

    // 按日期排序（最新的在前）
    posts.sort((a, b) => {
      const dateA = new Date(a.date).getTime()
      const dateB = new Date(b.date).getTime()
      return dateB - dateA
    })

    return posts
  } catch (error) {
    console.error('获取文章列表失败:', error)
    throw error
  }
}

/**
 * 获取单个文章信息
 * @param path 文章路径（相对于仓库根目录）
 */
export async function getPost(path: string): Promise<PostInfo | null> {
  const octokit = getOctokit()

  try {
    const { data } = await octokit.rest.repos.getContent({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path,
      ref: REPO_CONFIG.branch
    })

    if (!('content' in data) || data.type !== 'file') {
      return null
    }

    // Base64 解码内容
    const content = base64Decode(data.content)
    const { frontMatter } = parseFrontMatter(content)

    // 解析分类
    let category = ''
    let subCategory = ''

    if (Array.isArray(frontMatter.categories)) {
      if (frontMatter.categories.length >= 1) {
        category = frontMatter.categories[0]
      }
      if (frontMatter.categories.length >= 2) {
        subCategory = frontMatter.categories[1]
      }
    }

    // 从路径提取文件名
    const filename = data.name.replace(/\.md$/, '')
    const relativePath = path.replace(`${REPO_CONFIG.postsPath}/`, '')

    return {
      filename,
      path: relativePath,
      fullPath: path,
      sha: data.sha,
      title: frontMatter.title,
      category,
      subCategory,
      tags: frontMatter.tags || [],
      date: frontMatter.date,
      updated: frontMatter.updated,
      status: frontMatter.status || 'published',
      description: frontMatter.description,
      cover: frontMatter.cover,
      series: frontMatter.series,
      seriesOrder: frontMatter.series_order
    }
  } catch (error) {
    console.error(`获取文章 ${path} 失败:`, error)
    throw error
  }
}

/**
 * 获取文章原始内容
 * @param path 文章路径（相对于仓库根目录）
 */
export async function getPostContent(path: string): Promise<string> {
  const octokit = getOctokit()

  try {
    const { data } = await octokit.rest.repos.getContent({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path,
      ref: REPO_CONFIG.branch
    })

    if (!('content' in data) || data.type !== 'file') {
      throw new Error('文件不存在或不是文件类型')
    }

    // Base64 解码
    return base64Decode(data.content)
  } catch (error) {
    console.error(`获取文章内容 ${path} 失败:`, error)
    throw error
  }
}

/**
 * 创建新文章
 * @param path 文章路径（相对于 source/_posts/）
 * @param content 文章内容（包含 Front Matter）
 */
export async function createPost(
  path: string,
  content: string
): Promise<CommitResponse> {
  const octokit = getOctokit()
  const fullPath = `${REPO_CONFIG.postsPath}/${path}`

  try {
    const { data } = await octokit.rest.repos.createOrUpdateFileContents({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path: fullPath,
      message: `docs: 创建文章 ${path}`,
      content: base64Encode(content),
      branch: REPO_CONFIG.branch
    })

    return {
      sha: data.commit.sha ?? '',
      html_url: data.commit.html_url ?? ''
    }
  } catch (error) {
    console.error(`创建文章 ${path} 失败:`, error)
    throw error
  }
}

/**
 * 更新文章
 * @param path 文章路径（相对于 source/_posts/）
 * @param content 文章内容（包含 Front Matter）
 * @param sha 文件 SHA 值（用于更新）
 */
export async function updatePost(
  path: string,
  content: string,
  sha: string
): Promise<CommitResponse> {
  const octokit = getOctokit()
  const fullPath = `${REPO_CONFIG.postsPath}/${path}`

  try {
    const { data } = await octokit.rest.repos.createOrUpdateFileContents({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path: fullPath,
      message: `docs: 更新文章 ${path}`,
      content: base64Encode(content),
      sha,
      branch: REPO_CONFIG.branch
    })

    return {
      sha: data.commit.sha ?? '',
      html_url: data.commit.html_url ?? ''
    }
  } catch (error) {
    console.error(`更新文章 ${path} 失败:`, error)
    throw error
  }
}

/**
 * 删除文章
 * @param path 文章路径（相对于 source/_posts/）
 * @param sha 文件 SHA 值
 */
export async function deletePost(path: string, sha: string): Promise<CommitResponse> {
  const octokit = getOctokit()
  const fullPath = `${REPO_CONFIG.postsPath}/${path}`

  try {
    const { data } = await octokit.rest.repos.deleteFile({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path: fullPath,
      message: `docs: 删除文章 ${path}`,
      sha,
      branch: REPO_CONFIG.branch
    })

    return {
      sha: data.commit.sha ?? '',
      html_url: data.commit.html_url ?? ''
    }
  } catch (error) {
    console.error(`删除文章 ${path} 失败:`, error)
    throw error
  }
}

/**
 * 上传图片
 * @param path 图片路径（相对于仓库根目录）
 * @param content 图片数据（Uint8Array 或 ArrayBuffer）
 */
export async function uploadImage(
  path: string,
  content: Uint8Array | ArrayBuffer
): Promise<CommitResponse> {
  const octokit = getOctokit()

  try {
    const { data } = await octokit.rest.repos.createOrUpdateFileContents({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path,
      message: `chore: 上传图片 ${path}`,
      content: bufferToBase64(content),
      branch: REPO_CONFIG.branch
    })

    return {
      sha: data.commit.sha ?? '',
      html_url: data.commit.html_url ?? ''
    }
  } catch (error) {
    console.error(`上传图片 ${path} 失败:`, error)
    throw error
  }
}

/**
 * 删除图片
 * @param path 图片路径（相对于仓库根目录）
 * @param sha 文件 SHA 值
 */
export async function deleteImage(path: string, sha: string): Promise<CommitResponse> {
  const octokit = getOctokit()

  try {
    const { data } = await octokit.rest.repos.deleteFile({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path,
      message: `chore: 删除图片 ${path}`,
      sha,
      branch: REPO_CONFIG.branch
    })

    return {
      sha: data.commit.sha ?? '',
      html_url: data.commit.html_url ?? ''
    }
  } catch (error) {
    console.error(`删除图片 ${path} 失败:`, error)
    throw error
  }
}

/**
 * 获取文章的所有图片（GitHub 模式）
 * 通过 GitHub Contents API 获取文章同名资源文件夹中的图片
 * @param articlePath 文章路径（相对于 source/_posts/）
 */
export async function getImages(articlePath: string): Promise<{
  name: string
  path: string
  size: number
  sha: string
  url: string
}[]> {
  void getOctokit()

  const assetFolderPath = `${REPO_CONFIG.postsPath}/${articlePath.replace(/.md$/, "")}`.replace(/\\/g, "/")

  try {
    const items = await getDirectoryContents(assetFolderPath)
    return items
      .filter(item => /\.(png|jpg|jpeg|gif|webp|svg)$/i.test(item.name))
      .map(item => ({
        name: item.name,
        path: item.path,
        size: item.size || 0,
        sha: item.sha || '',
        url: item.downloadUrl || ''
      }))
  } catch (error: any) {
    // 资源文件夹不存在或为空，返回空数组
    if (error.status === 404) {
      return []
    }
    throw error
  }
}

/**
 * 获取目录内容列表
 * @param path 目录路径（相对于仓库根目录）
 */
export async function getDirectoryContents(path: string): Promise<DirectoryItem[]> {
  const octokit = getOctokit()

  try {
    const { data } = await octokit.rest.repos.getContent({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path,
      ref: REPO_CONFIG.branch
    })

    if (!Array.isArray(data)) {
      return []
    }

    return data.map((item) => ({
      name: item.name,
      path: item.path,
      type: item.type as 'file' | 'dir',
      sha: item.sha,
      size: item.size,
      downloadUrl: item.download_url
    }))
  } catch (error) {
    console.error(`获取目录 ${path} 内容失败:`, error)
    throw error
  }
}

/**
 * 获取文件内容（Base64 解码）
 * @param path 文件路径（相对于仓库根目录）
 */
export async function getFileContent(path: string): Promise<string> {
  const octokit = getOctokit()

  try {
    const { data } = await octokit.rest.repos.getContent({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path,
      ref: REPO_CONFIG.branch
    })

    if (!('content' in data) || data.type !== 'file') {
      throw new Error('文件不存在或不是文件类型')
    }

    // Base64 解码
    return base64Decode(data.content)
  } catch (error) {
    console.error(`获取文件 ${path} 内容失败:`, error)
    throw error
  }
}

/**
 * 获取文件 SHA 值
 * @param path 文件路径（相对于仓库根目录）
 */
export async function getFileSha(path: string): Promise<string> {
  const octokit = getOctokit()

  try {
    const { data } = await octokit.rest.repos.getContent({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path,
      ref: REPO_CONFIG.branch
    })

    if (!('sha' in data)) {
      throw new Error('无法获取文件 SHA')
    }

    return data.sha
  } catch (error) {
    console.error(`获取文件 ${path} SHA 失败:`, error)
    throw error
  }
}

/**
 * 触发 GitHub Actions 部署
 * 通过创建一个空提交来触发工作流
 * @param commitMessage 提交信息
 */
export async function triggerDeploy(commitMessage: string): Promise<CommitResponse> {
  const octokit = getOctokit()

  try {
    // 获取最新提交的 SHA
    const { data: ref } = await octokit.rest.git.getRef({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      ref: `heads/${REPO_CONFIG.branch}`
    })

    const latestCommitSha = ref.object.sha

    // 获取最新提交的树 SHA
    const { data: commit } = await octokit.rest.git.getCommit({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      commit_sha: latestCommitSha
    })

    // 创建新提交（使用相同的树）
    const { data: newCommit } = await octokit.rest.git.createCommit({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      message: commitMessage,
      tree: commit.tree.sha,
      parents: [latestCommitSha]
    })

    // 更新分支引用
    await octokit.rest.git.updateRef({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      ref: `heads/${REPO_CONFIG.branch}`,
      sha: newCommit.sha
    })

    return {
      sha: newCommit.sha,
      html_url: `https://github.com/${REPO_CONFIG.owner}/${REPO_CONFIG.repo}/commit/${newCommit.sha}`
    }
  } catch (error) {
    console.error('触发部署失败:', error)
    throw error
  }
}

/**
 * 检查文件是否存在
 * @param path 文件路径（相对于仓库根目录）
 */
export async function fileExists(path: string): Promise<boolean> {
  const octokit = getOctokit()

  try {
    await octokit.rest.repos.getContent({
      owner: REPO_CONFIG.owner,
      repo: REPO_CONFIG.repo,
      path,
      ref: REPO_CONFIG.branch
    })
    return true
  } catch (error: any) {
    if (error.status === 404) {
      return false
    }
    throw error
  }
}

/**
 * 获取分类目录列表
 * 返回 source/_posts/ 下的一级分类目录
 */
export async function getCategories(): Promise<DirectoryItem[]> {
  return getDirectoryContents(REPO_CONFIG.postsPath)
}

/**
 * 获取指定分类下的文章列表
 * @param category 分类名称
 */
export async function getPostsByCategory(category: string): Promise<PostInfo[]> {
  const allPosts = await getPosts()
  return allPosts.filter((post) => post.category === category)
}

/**
 * 构建文章 Front Matter
 */
export function buildFrontMatter(
  frontMatter: Partial<PostFrontMatter>
): string {
  const now = new Date()
  const dateStr = frontMatter.date || now.toISOString().replace('T', ' ').slice(0, 19)

  const defaultFrontMatter: PostFrontMatter = {
    title: frontMatter.title || '未命名文章',
    date: dateStr,
    categories: frontMatter.categories || ['未分类'],
    tags: frontMatter.tags || [],
    description: frontMatter.description || '',
    status: frontMatter.status || 'draft'
  }

  const merged = { ...defaultFrontMatter, ...frontMatter }

  // 构建 YAML 格式的 Front Matter
  const lines = ['---']
  lines.push(`title: ${merged.title}`)
  lines.push(`date: ${merged.date}`)

  if (merged.updated) {
    lines.push(`updated: ${merged.updated}`)
  }

  lines.push('')
  lines.push('categories:')
  if (Array.isArray(merged.categories)) {
    merged.categories.forEach((cat) => {
      lines.push(`  - ${cat}`)
    })
  }

  lines.push('')
  lines.push('tags:')
  if (merged.tags && merged.tags.length > 0) {
    merged.tags.forEach((tag) => {
      lines.push(`  - ${tag}`)
    })
  }

  if (merged.description) {
    lines.push('')
    lines.push(`description: ${merged.description}`)
  }

  if (merged.cover) {
    lines.push('')
    lines.push(`cover: ${merged.cover}`)
  }

  if (merged.status) {
    lines.push('')
    lines.push(`status: ${merged.status}`)
  }

  if (merged.series) {
    lines.push('')
    lines.push(`series: ${merged.series}`)
    if (merged.series_order) {
      lines.push(`series_order: ${merged.series_order}`)
    }
  }

  lines.push('---')
  lines.push('')

  return lines.join('\n')
}