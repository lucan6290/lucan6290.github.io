import type { NavEntry } from '@/types/content';

/**
 * 顶部导航栏 ↔ 内容树根节点映射。
 * 新增分区只需在此追加一条；CategoryView 根据 route.params 自动定位子树。
 */
export const NAV_ENTRIES: NavEntry[] = [
  {
    key: 'knowledge',
    label: '知识库',
    rootPath: '/knowledge',
    items: [
      { label: '首页', to: '/knowledge' },
      { label: '技术研习', to: '/knowledge/tech-study' },
      { label: '项目实战', to: '/knowledge/project-practice' },
      { label: '资源分享', to: '/knowledge/resource-sharing' },
    ],
  },
  {
    key: 'blog',
    label: '博客',
    rootPath: '/blog',
    items: [
      { label: '博客首页', to: '/blog' },
      { label: 'AI观察', to: '/blog/AI观察' },
      { label: '随笔感想', to: '/blog/随笔感想' },
    ],
  },
];

export const STATIC_NAV_ITEMS = [
  { label: '项目展示', to: '/projects' },
  { label: '关于本站', to: '/about' },
] as const;
