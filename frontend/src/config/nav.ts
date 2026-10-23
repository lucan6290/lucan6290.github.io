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
  return tree.filter((node) => !node.article)
    .sort((a, b) => rank(a.name) - rank(b.name))
    .map((node) => ({
      key: node.name,
      label: sectionLabel(node.name),
      rootPath: node.path,
      items: [
        { label: `${sectionLabel(node.name)}首页`, to: contentHref(node.path) },
        ...node.children
          .filter((child) => node.name !== 'knowledge' || !child.article)
          .map((child) => ({ label: child.label, to: contentHref(child.path) })),
      ],
    }));
}
