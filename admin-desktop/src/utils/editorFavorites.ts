import { shallowRef } from 'vue'
import { relocatePath, type PathMove } from './editorTabs'

export const favorites = shallowRef<string[]>([])
let workspaceKey = ''

export function openFavorites(contentRoot: string) {
  const key = 'luchuan.desktop.favorites:' + contentRoot
  if (key === workspaceKey) return
  workspaceKey = key
  try {
    const stored: unknown = JSON.parse(localStorage.getItem(workspaceKey) || '[]')
    favorites.value = Array.isArray(stored) ? stored.filter((path): path is string => typeof path === 'string') : []
  } catch { favorites.value = [] }
}

function write(paths: string[]) {
  favorites.value = paths
  try { localStorage.setItem(workspaceKey, JSON.stringify(paths)) } catch { /* 收藏仍可在当前会话使用。 */ }
}

export function toggleFavorite(path: string) {
  write(favorites.value.includes(path) ? favorites.value.filter(item => item !== path) : [...favorites.value, path])
}

export function relocateFavorites(moves: PathMove[]) {
  if (!favorites.value.length) return
  write([...new Set(favorites.value.map(path => relocatePath(path, moves)))])
}
