export function previewImagePath(reference: string, documentDirectory: string): string | null {
  const [path] = reference.split(/[?#]/, 1)
  if (!path || path.startsWith('/') || /^[a-z][\w+.-]*:/i.test(path)) return null
  const parts = documentDirectory ? documentDirectory.split('/') : []
  try {
    for (const encoded of path.split('/')) {
      const part = decodeURIComponent(encoded)
      if (/[\\/]/.test(part)) return null
      if (part === '..') {
        if (!parts.length) return null
        parts.pop()
      } else if (part && part !== '.') parts.push(part)
    }
  } catch { return null }
  return parts.join('/') || null
}
