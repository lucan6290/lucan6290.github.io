import type { NavEntry, TreeNode } from '@/types/content';
import { contentHref } from '../composables/contentPaths.ts';

// 仅保留四个既有栏目的名称与顺序；栏目是否存在由 content 一级目录决定。
const KNOWN_SECTIONS = [
  { key: 'knowledge', label: '知识库' },
  { key: 'blog', label: '博客' },
  { key: 'projects', label: '项目' },
  { key: 'about', label: '关于' },
];

export function sectionLabel(name: string) {
  return KNOWN_SECTIONS.find((section) => section.key === name)?.label || name.replace(/^\d+[-_]/, '');
}

export function createNavEntries(tree: TreeNode[]): NavEntry[] {
  const rank = (name: string) => {
    const index = KNOWN_SECTIONS.findIndex((section) => section.key === name);
    return index < 0 ? KNOWN_SECTIONS.length : index;
  };
  const entries: NavEntry[] = tree.filter((node) => !node.article && node.name !== 'about')
    .map((node) => ({
      key: node.name,
      label: sectionLabel(node.name),
      rootPath: node.path,
      items: [
        { label: node.name === 'knowledge' ? '首页' : `${sectionLabel(node.name)}首页`, to: contentHref(node.path) },
        ...node.children
          .filter((child) => node.name !== 'knowledge' || !child.article)
          .map((child) => ({ label: child.label, to: contentHref(child.path) })),
      ],
    }));
  entries.push({ key: 'about', label: '关于', rootPath: '/about', items: [] });
  return entries.sort((a, b) => rank(a.key) - rank(b.key));
}

/** Navbar 右侧独立链接 */
export const NAV_RIGHT_ITEMS = [
  { label: 'GitHub', href: 'https://github.com/lucan6290' },
] as const;

/** Logo 配置 */
export const NAV_LOGO = {
  src: '/img/favicon.png',
  alt: '箓川码笺',
} as const;
