import type { BytemdPlugin } from 'bytemd'

const BLOCK_TAGS = new Set([
  'blockquote',
  'btns',
  'cardList',
  'checkbox',
  'collapse',
  'gallery',
  'hideToggle',
  'link',
  'mermaid',
  'note',
  'tabs',
  'timeline'
])

const SELF_CLOSING_TAGS = new Set([
  'asset_img',
  'button',
  'btn',
  'flink',
  'ghcard',
  'image',
  'inlineImg',
  'label',
  'site'
])

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function titleCase(value: string): string {
  if (!value) return 'Hexo'
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function renderTagPreview(source: string): string {
  let html = source

  html = html.replace(
    /\{%\s*(\w+)([^%]*)%\}([\s\S]*?)\{%\s*end\1\s*%\}/g,
    (_match: string, tagName: string, args: string, body: string) => {
      const normalized = tagName.trim()
      if (!BLOCK_TAGS.has(normalized)) return _match

      const label = `${titleCase(normalized)}${args.trim() ? ` ${escapeHtml(args.trim())}` : ''}`
      const content = escapeHtml(body.trim())

      if (normalized === 'mermaid') {
        return `<pre><code class="language-mermaid">${content}</code></pre>`
      }

      return [
        `<section class="hexo-preview-block hexo-preview-${normalized}">`,
        `<div class="hexo-preview-label">${label}</div>`,
        content ? `<div class="hexo-preview-content"><pre>${content}</pre></div>` : '',
        '</section>'
      ].join('')
    }
  )

  html = html.replace(
    /\{%\s*(\w+)([^%]*)%\}/g,
    (match: string, tagName: string, args: string) => {
      const normalized = tagName.trim()
      if (!SELF_CLOSING_TAGS.has(normalized)) return match

      const label = `${titleCase(normalized)}${args.trim() ? ` ${escapeHtml(args.trim())}` : ''}`
      return `<span class="hexo-preview-inline">${label}</span>`
    }
  )

  return html
}

function renderHexoTags(markdownBody: HTMLElement): void {
  const candidates = Array.from(markdownBody.querySelectorAll('p, pre, blockquote, li'))

  for (const node of candidates) {
    const element = node as HTMLElement
    const text = element.textContent || ''

    if (!text.includes('{%')) continue

    const rendered = renderTagPreview(text)
    if (rendered === text) continue

    const wrapper = document.createElement('div')
    wrapper.innerHTML = rendered
    element.replaceWith(...Array.from(wrapper.childNodes))
  }
}

export function hexoPreview(): BytemdPlugin {
  return {
    viewerEffect({ markdownBody }) {
      renderHexoTags(markdownBody)
    }
  }
}
