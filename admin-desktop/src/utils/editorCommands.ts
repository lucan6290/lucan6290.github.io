export type MarkdownCommand = 'bold' | 'italic' | 'heading' | 'link' | 'quote' | 'bullet' | 'task' | 'code'

export const markdownCommands: { action: MarkdownCommand; label: string; shortcut?: string }[] = [
  { action: 'heading', label: '二级标题' },
  { action: 'bold', label: '粗体', shortcut: 'Ctrl+B' },
  { action: 'italic', label: '斜体', shortcut: 'Ctrl+I' },
  { action: 'link', label: '链接', shortcut: 'Ctrl+K' },
  { action: 'quote', label: '引用' },
  { action: 'bullet', label: '列表' },
  { action: 'task', label: '待办' },
  { action: 'code', label: '代码' },
]

const prefixes = { heading: '## ', quote: '> ', bullet: '- ', task: '- [ ] ' }

export function applyMarkdownCommand(text: string, start: number, end: number, command: MarkdownCommand) {
  const selected = text.slice(start, end)
  if (command === 'heading' || command === 'quote' || command === 'bullet' || command === 'task') {
    const beginning = start === 0 ? 0 : text.lastIndexOf('\n', start - 1) + 1
    const newline = text.indexOf('\n', Math.max(start, end - 1))
    const finish = newline < 0 ? text.length : newline
    const lines = text.slice(beginning, finish) || (command === 'heading' ? '标题' : '内容')
    const prefix = prefixes[command]
    const formatted = lines.split('\n').map(line => prefix + line).join('\n')
    return {
      text: text.slice(0, beginning) + formatted + text.slice(finish),
      start: beginning + prefix.length,
      end: beginning + formatted.length,
    }
  }
  if (command === 'link') {
    const label = selected || '链接文字'
    const address = 'https://'
    const insertion = '[' + label + '](' + address + ')'
    const addressStart = start + label.length + 3
    return { text: text.slice(0, start) + insertion + text.slice(end), start: addressStart, end: addressStart + address.length }
  }
  const mark = command === 'bold' ? '**' : command === 'italic' ? '*' : String.fromCharCode(96)
  const value = selected || (command === 'code' ? 'code' : '文字')
  const delimiter = command === 'code' && selected.includes('\n') ? mark.repeat(3) + '\n' : mark
  const suffix = delimiter.endsWith('\n') ? '\n' + delimiter.trimEnd() : delimiter
  return {
    text: text.slice(0, start) + delimiter + value + suffix + text.slice(end),
    start: start + delimiter.length,
    end: start + delimiter.length + value.length,
  }
}
