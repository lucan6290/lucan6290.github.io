import type { InjectionKey, Ref } from 'vue'

export const workspaceControlsKey: InjectionKey<{
  available: boolean
  root: Ref<string>
  busy: Ref<boolean>
  error: Ref<string>
  select: () => Promise<void>
}> = Symbol('workspaceControls')
