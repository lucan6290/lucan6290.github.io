export type BlogSidebarItem = {
  label: string;
  path: string;
  to: string;
  count?: number;
  collapsed?: boolean;
  items?: BlogSidebarDocItem[];
};

export type BlogSidebarDocItem = {
  label: string;
  to: string;
};

const blogSidebars: BlogSidebarItem[] = [
  {
    label: '成长随笔',
    path: '成长随笔',
    to: '/blog/成长随笔',
    items: [
      {
        label: '旧标题',
        to: '/blog/新标题',
      },
    ],
  },
  {
    label: '随笔感想',
    path: '随笔感想',
    to: '/blog/随笔感想',
    items: [
    ],
  },
];

export default blogSidebars;
