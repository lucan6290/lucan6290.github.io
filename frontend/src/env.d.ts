/// <reference types="vite/client" />

// @bytemd/vue-next 1.22 的 Viewer 声明只导出了 DefineComponent 类型，补齐运行时组件签名。
declare module '@bytemd/vue-next' {
  import type { DefineComponent } from 'vue';
  import type { BytemdPlugin } from 'bytemd';
  export const Viewer: DefineComponent<{ value: string; plugins?: BytemdPlugin[] }>;
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue';
  const component: DefineComponent<object, object, unknown>;
  export default component;
}

declare module 'virtual:content-manifest' {
  import type { ContentManifest } from '@/types/content';
  const manifest: ContentManifest;
  export default manifest;
}
