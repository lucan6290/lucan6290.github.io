import type { InjectionKey, Ref } from 'vue'

export function formatWindowsPathsForDisplay(text: string): string {
  return text
    .replace(/(?<![\\/])\\\\\?\\UNC\\/gi, '\\\\')
    .replace(/(?<![\\/])\\\\\?\\(?=[a-z]:\\)/gi, '')
}

export const workspaceControlsKey: InjectionKey<{
  available: boolean
  root: Ref<string>
  busy: Ref<boolean>
  error: Ref<string>
  select: () => Promise<void>
}> = Symbol('workspaceControls')
