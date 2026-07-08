import type { BytemdPlugin } from 'bytemd'
import { getAuthToken } from '@/utils/auth'

const API_PREFIX = '/api/v1'

type HastNode = {
  type?: string
  tagName?: string
  properties?: Record<string, unknown>
  children?: HastNode[]
}

function isExternalUrl(src: string): boolean {
  return /^(https?:)?\/\//i.test(src)
    || src.startsWith('/')
    || src.startsWith('data:')
    || src.startsWith('blob:')
    || src.startsWith('#')
}

function stripTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '')
}

function safeDecodeURIComponent(value: string): string {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

type ArticlePathSource = string | (() => string)

function getArticlePath(source: ArticlePathSource): string {
  return typeof source === 'function' ? source() : source
}

function resolveLocalPreviewUrl(src: string, articlePath: string, apiBaseUrl: string): string | null {
  if (!articlePath || !src || isExternalUrl(src)) return null

  const cleanedSrc = src.trim().split('#', 1)[0].split('?', 1)[0]
  const parts = cleanedSrc.replace(/\\/g, '/').replace(/^\.\//, '').split('/').filter(Boolean)
  if (parts.length !== 2) return null

  const imageName = safeDecodeURIComponent(parts[1])
  const baseUrl = `${stripTrailingSlash(apiBaseUrl)}${API_PREFIX}/articles/${encodeURIComponent(articlePath)}/images/${encodeURIComponent(imageName)}/content`
  // <img> 标签无法附加 Authorization 头，需通过 query 参数传递会话 token
  const token = getAuthToken()
  return token ? `${baseUrl}?access_token=${encodeURIComponent(token)}` : baseUrl
}

function rewriteImageNodes(node: HastNode, articlePathSource: ArticlePathSource, apiBaseUrl: string): void {
  if (node.type === 'element' && node.tagName === 'img' && node.properties) {
    const src = node.properties.src
    const previewUrl = typeof src === 'string'
      ? resolveLocalPreviewUrl(src, getArticlePath(articlePathSource), apiBaseUrl)
      : null

    if (previewUrl) {
      node.properties['data-original-src'] = src
      node.properties.src = previewUrl
    }
  }

  node.children?.forEach((child) => rewriteImageNodes(child, articlePathSource, apiBaseUrl))
}

export function postAssetPreview(articlePathSource: ArticlePathSource, apiBaseUrl: string): BytemdPlugin {
  return {
    rehype(processor) {
      return processor.use(() => (tree: HastNode) => {
        rewriteImageNodes(tree, articlePathSource, apiBaseUrl)
      })
    },
    viewerEffect({ markdownBody }) {
      const articlePath = getArticlePath(articlePathSource)
      const images = Array.from(markdownBody.querySelectorAll('img'))
      for (const image of images) {
        const src = image.getAttribute('src')
        const previewUrl = src ? resolveLocalPreviewUrl(src, articlePath, apiBaseUrl) : null
        if (!src || !previewUrl) continue
        image.setAttribute('data-original-src', src)
        image.setAttribute('src', previewUrl)
      }
    }
  }
}
