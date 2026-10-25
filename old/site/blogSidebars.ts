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
    label: 'AI观察',
    path: 'AI观察',
    to: '/blog/AI观察',
    items: [
      {
        label: '别再研究Prompt了，AI正在重构你的行业',
        to: '/blog/AI正在重构你的行业',
      },
      {
        label: 'AI编程工具的真实体验：强但没那么神',
        to: '/blog/AI编程工具真实体验',
      },
    ],
  },
  {
    label: '随笔感想',
    path: '随笔感想',
    to: '/blog/随笔感想',
    items: [
      {
        label: '我的技术表达能力：问题诊断与提升方案',
        to: '/blog/技术表达能力提升方案',
      },
      {
        label: '一看就懂，一说就卡：我为什么懂了却讲不出来',
        to: '/blog/一看就懂，一说就卡：我为什么懂了却讲不出来',
      },
      {
        label: '重建个人技术站',
        to: '/blog/重建个人技术站',
      },
    ],
  },
];

export default blogSidebars;
