export function formatBeijingTime(date: Date): string {
  return new Date(date.getTime() + 8 * 60 * 60 * 1000).toISOString().slice(0, 19) + '+08:00'
}

export function createArticleTemplate(date = new Date()): string {
  const timestamp = formatBeijingTime(date)
  return `---\ntitle: ""\ndate: "${timestamp}"\nupdated: "${timestamp}"\ndescription: ""\ntags: []\nsticky: false\n---\n\n# \n`
}

export function isArticleDocument(path: string, article = true): boolean {
  return article && !/^(readme|agents)\.md$/i.test(path.split('/').pop() || '')
}

// Only fill the empty fields of our generated template; arbitrary YAML stays untouched.
export function fillArticleTitle(raw: string, filename: string): string {
  const header = raw.match(/^---\n([\s\S]*?)\n---(?:\n|$)/)
  if (!header || !/^title: ""$/m.test(header[1])) return raw
  const body = raw.slice(header[0].length)
  const heading = body.match(/^# ([^\n]*)$/m)
  if (!heading || heading[1].trim()) return raw
  const title = filename.replace(/\.md$/i, '').replace(/^\d+[-_]/, '')
  if (!title) return raw
  return header[0].replace(/^title: ""$/m, () => `title: ${JSON.stringify(title)}`)
    + body.replace(/^# [^\n]*$/m, () => `# ${title}`)
}

function updatedField(text: string) {
  const header = text.match(/^---\n([\s\S]*?)\n---(?:\n|$)/)
  if (!header) return null
  const matches = [...header[1].matchAll(/^updated:[ \t]*("\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00")(?=[ \t]*(?:#.*)?$)/gm)]
  if (matches.length !== 1) return null
  const match = matches[0]
  return { value: match[1], offset: 4 + match.index! + match[0].length - match[1].length }
}

// Merge only the server timestamp, never the document snapshot over newer local input.
export function mergeSavedUpdated(local: string, sent: string, saved: string): string {
  const current = updatedField(local)
  const before = updatedField(sent)
  const after = updatedField(saved)
  if (!current || !before || !after || current.value !== before.value) return local
  return local.slice(0, current.offset) + after.value + local.slice(current.offset + current.value.length)
}
