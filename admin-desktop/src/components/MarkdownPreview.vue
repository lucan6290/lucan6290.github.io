<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { Viewer } from '@bytemd/vue-next'
import type { BytemdPlugin } from 'bytemd'
import frontmatter from '@bytemd/plugin-frontmatter'
import gfm from '@bytemd/plugin-gfm'
import highlight from '@bytemd/plugin-highlight'
import math from '@bytemd/plugin-math'
import mermaid from '@bytemd/plugin-mermaid'
import { isTauri } from '@tauri-apps/api/core'
import { openUrl } from '@tauri-apps/plugin-opener'
import { contentApi } from '@/api/content'
import { previewImagePath } from '@/utils/previewImage'
import 'bytemd/dist/index.css'
import 'highlight.js/styles/github.css'
import 'katex/dist/katex.css'

const props = defineProps<{ text: string; documentDirectory: string }>()
const emit = defineEmits<{ openDocument: [path: string] }>()
const headings = shallowRef<HTMLElement[]>([])
const imageSources = new WeakMap<HTMLImageElement, string>()
const basePlugins = [frontmatter(), gfm(), highlight(), math(), mermaid()]
const plugins = computed<BytemdPlugin[]>(() => {
  const directory = props.documentDirectory
  return [...basePlugins, {
    viewerEffect({ markdownBody }) {
      const used = new Set<string>()
      headings.value = [...markdownBody.querySelectorAll<HTMLElement>('h1,h2,h3,h4,h5,h6')]
      for (const heading of headings.value) {
        const slug = (heading.textContent || '').trim().toLowerCase().replace(/[^\p{L}\p{N}\p{M}\s_-]/gu, '').replace(/\s/g, '-') || 'section'
        let id = slug
        for (let n = 1; used.has(id); n++) id = `${slug}-${n}`
        used.add(id)
        heading.id = id
      }
      const controller = new AbortController()
      const urls: string[] = []
      for (const image of markdownBody.querySelectorAll<HTMLImageElement>('img')) {
        const source = imageSources.get(image) ?? image.getAttribute('src') ?? ''
        const asset = previewImagePath(source, directory)
        if (!asset) continue
        imageSources.set(image, source)
        image.removeAttribute('src')
        image.removeAttribute('title')
        void contentApi.image(asset, controller.signal).then(blob => {
          if (controller.signal.aborted) return
          const url = URL.createObjectURL(blob)
          urls.push(url)
          image.src = url
        }).catch(() => {
          if (!controller.signal.aborted) image.title = '无法读取图片'
        })
      }
      return () => { controller.abort(); urls.forEach(url => URL.revokeObjectURL(url)) }
    },
  }]
})

function follow(event: MouseEvent) {
  if (!(event.target instanceof Element)) return
  const href = event.target.closest('a')?.getAttribute('href')
  if (!href) return
  event.preventDefault()
  if (href.startsWith('#')) {
    let id = href.slice(1)
    try { id = decodeURIComponent(id) } catch { return }
    headings.value.find(heading => heading.id === id)?.scrollIntoView({ block: 'start' })
  } else if (/^https?:\/\//i.test(href)) {
    if (isTauri()) void openUrl(href)
    else window.open(href, '_blank', 'noopener,noreferrer')
  } else {
    const path = previewImagePath(href, props.documentDirectory)
    if (path && /\.mdx?$/i.test(path)) emit('openDocument', path)
  }
}
</script>

<template>
  <section class="markdown-preview" aria-label="实时预览">
    <details v-if="headings.length" class="preview-outline">
      <summary>文章大纲</summary>
      <button v-for="heading in headings" :key="heading.id" type="button" class="btn btn-ghost btn-sm"
        :style="{ paddingLeft: `${Number(heading.tagName[1]) * 10}px` }"
        @click="heading.scrollIntoView({ block: 'start' })">{{ heading.textContent }}</button>
    </details>
    <div class="preview-content" @click="follow" @auxclick="follow">
      <Viewer :value="text" :plugins="plugins" />
    </div>
  </section>
</template>

<style scoped>
.markdown-preview { min-width: 0; max-height: 72vh; overflow: auto; background: var(--bg-panel); color: var(--text-primary); }
.preview-outline { padding: 10px 16px; border-bottom: 1px solid var(--border-subtle); }
.preview-outline summary { cursor: pointer; }
.preview-outline button { display: block; text-align: left; white-space: normal; overflow-wrap: anywhere; }
.preview-content { padding: 16px; overflow-wrap: anywhere; }
.preview-content :deep(.markdown-body) { background: transparent; color: inherit; }
.preview-content :deep(img) { max-width: 100%; }
</style>
