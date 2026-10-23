export type FrontMatter = {
  title?: string;
  date?: string;
  updated?: string;
  tags?: string[];
  description?: string;
  sticky?: boolean;
};

export type ArticleMeta = {
  slug: string;
  path: string;
  relativePath: string;
  frontmatter: FrontMatter & { title: string; date: string; updated: string };
  sortKey: string | null;
  mtimeMs: number;
  excerpt: string;
  /** MD 原文（不含 frontmatter），构建期写入 manifest */
  rawContent: string;
};

export type TreeNode = {
  name: string;
  label: string;
  path: string;
  sortKey: string | null;
  children: TreeNode[];
  article?: ArticleMeta;
  introduction?: ArticleMeta;
};

export type PrevNext = {
  prev: Pick<ArticleMeta, 'slug' | 'path'> & { title: string } | null;
  next: Pick<ArticleMeta, 'slug' | 'path'> & { title: string } | null;
};

export type ContentManifest = {
  tree: TreeNode[];
  articles: Record<string, ArticleMeta>;
  prevNext: Record<string, PrevNext>;
  tags: Record<string, string[]>;
  archive: Record<string, Record<string, string[]>>;
  recent: string[];
};

export type NavEntry = {
  key: string;
  label: string;
  rootPath: string;
  items: { label: string; to: string }[];
};
