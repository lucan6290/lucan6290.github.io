export const imageExtensions = '.png,.jpg,.jpeg,.gif,.svg,.webp,.avif,.bmp,.ico'

export function fileBase64(file: File): Promise<string> {
  if (file.size > 12 * 1024 * 1024) return Promise.reject(new Error('单张图片不能超过 12 MiB'))
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('无法读取图片文件'))
    reader.onload = () => resolve(String(reader.result).slice(String(reader.result).indexOf(',') + 1))
    reader.readAsDataURL(file)
  })
}

export function insertImageReferences(text: string, selectionEnd: number, references: string[]) {
  const header = /^---[ \t]*\n[\s\S]*?^---[ \t]*(?=\n|$)/m.exec(text)
  if (header?.index === 0) selectionEnd = Math.max(selectionEnd, header[0].length)
  const lineEnd = text.indexOf('\n', selectionEnd)
  const end = lineEnd < 0 ? text.length : lineEnd
  const before = text.slice(0, end)
  const after = text.slice(end + 1)
  const separator = before ? (before.endsWith('\n') ? '\n' : '\n\n') : ''
  const inserted = before + separator + references.join('\n\n') + '\n\n'
  return { text: inserted + after, caret: inserted.length }
}
