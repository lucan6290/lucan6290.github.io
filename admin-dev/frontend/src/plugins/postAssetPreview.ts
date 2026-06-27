import type { BytemdPlugin } from 'bytemd'

function isExternalUrl(src: string): boolean {
  return /^(https?:)?\/\//i.test(src)
    || src.startsWith('/')
    || src.startsWith('data:')
    || src.startsWith('blob:')
    || src.startsWith('#')
}

function encodePath(path: string): string {
  return path
    .split('/')
    .filter(Boolean)
    .map((part) => encodeURIComponent(part))
    .join('/')
}

function decodePath(value: string): string {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

function getArticleAssetDir(articlePath: string): string {
  return articlePath.replace(/\.md$/i, '')
}

function resolveAssetPreviewUrl(articlePath: string, src: string, apiBaseUrl: string): string {
  const cleanSrc = decodePath(src.replace(/^\.\/+/, ''))
  const assetPath = `${getArticleAssetDir(articlePath)}/${cleanSrc}`
  return `${apiBaseUrl.replace(/\/$/, '')}/api/admin/v1/assets/file/${encodePath(assetPath)}`
}

function resolveDevPreviewUrl(articlePath: string, src: string): string {
  const cleanSrc = decodePath(src.replace(/^\.\/+/, ''))
  const assetPath = `${getArticleAssetDir(articlePath)}/${cleanSrc}`
  return `/source/_posts/${encodePath(assetPath)}`
}

export function postAssetPreview(articlePath: string, apiBaseUrl: string): BytemdPlugin {
  return {
    viewerEffect({ markdownBody }) {
      if (!articlePath || !apiBaseUrl) return

      const images = Array.from(markdownBody.querySelectorAll('img'))
      for (const image of images) {
        const src = image.getAttribute('src')
        if (!src || isExternalUrl(src)) continue

        const fallbackUrl = resolveDevPreviewUrl(articlePath, src)
        image.setAttribute('data-original-src', src)
        image.setAttribute('data-fallback-src', fallbackUrl)
        image.onerror = () => {
          if (image.src.endsWith(fallbackUrl)) return
          image.src = fallbackUrl
        }
        image.setAttribute('src', resolveAssetPreviewUrl(articlePath, src, apiBaseUrl))
      }
    }
  }
}
