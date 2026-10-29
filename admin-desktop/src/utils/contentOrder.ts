/** 按前台扫描器的数字前缀与本机 localeCompare 逐层排列内容路径。 */
export function compareContentPaths(left: string, right: string): number {
  const a = left.split('/')
  const b = right.split('/')
  for (let index = 0; index < Math.min(a.length, b.length); index++) {
    if (a[index] === b[index]) continue
    const prefixA = a[index].match(/^(\d+)[-_]/)?.[1]?.padStart(6, '0')
    const prefixB = b[index].match(/^(\d+)[-_]/)?.[1]?.padStart(6, '0')
    if (prefixA && prefixB) return prefixA.localeCompare(prefixB)
    if (prefixA) return -1
    if (prefixB) return 1
    return a[index].localeCompare(b[index])
  }
  return a.length - b.length
}
