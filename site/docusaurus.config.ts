import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: '箓川码笺',
  tagline: '箓藏千思，川流不息',
  favicon: 'img/favicon.png',

  url: 'https://lucan6290.github.io',
  baseUrl: '/',

  organizationName: 'lucan6290',
  projectName: 'xiaocancoding',

  onBrokenLinks: 'warn',

  i18n: {
    defaultLocale: 'zh-CN',
    locales: ['zh-CN'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          path: 'docs',
          routeBasePath: 'docs',
          sidebarPath: './sidebars.ts',
          showLastUpdateTime: false,
          showLastUpdateAuthor: false,
        },
        blog: {
          path: 'blog',
          routeBasePath: 'blog',
          showReadingTime: true,
          onUntruncatedBlogPosts: 'ignore',
          postsPerPage: 8,
          blogSidebarTitle: '博客目录',
          blogSidebarCount: 'ALL',
          blogTitle: '博客',
          blogDescription: '阶段记录、踩坑复盘与成长随笔',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/site-card.png',
    navbar: {
      title: '箓川码笺',
      logo: {
        alt: '箓川码笺',
        src: 'img/favicon.png',
      },
      items: [
        {
          type: 'dropdown',
          label: '知识库',
          position: 'left',
          items: [
            {
              label: '知识库首页',
              to: '/docs/intro',
            },
            {
              label: '技术研习',
              to: '/docs/tech-study/java-interview/java-basic/java-vs-cpp',
            },
            {
              label: '项目实战',
              to: '/docs/project-practice/site-build',
            },
            {
              label: '资源分享',
              to: '/docs/resource-sharing/toolbox',
            },
          ],
        },
        {
          type: 'dropdown',
          label: '博客',
          position: 'left',
          items: [
            {
              label: '博客首页',
              to: '/blog',
            },
            {
              label: 'AI 编程工具真实体验',
              to: '/blog/AI编程工具真实体验',
            },
            {
              label: 'AI 正在重构行业',
              to: '/blog/AI正在重构你的行业',
            },
            {
              label: '博客架构与长期规划',
              to: '/blog/博客架构与长期发展规划',
            },
            {
              label: '博客写作完整指南',
              to: '/blog/博客写作完整指南',
            },
            {
              label: '定制创建文章命令',
              to: '/blog/定制创建文章命令记录',
            },
            {
              label: 'Hexo 博客搭建记录',
              to: '/blog/Hexo博客搭建记录',
            },
            {
              label: '重建个人技术站',
              to: '/blog/重建个人技术站',
            },
            {
              label: '虚拟机配置共享目录',
              to: '/blog/虚拟机配置共享目录',
            },
          ],
        },
        {
          type: 'dropdown',
          label: '项目',
          position: 'left',
          items: [
            {
              label: '项目展示',
              to: '/projects',
            },
            {
              label: '个人技术站',
              to: '/docs/project-practice/site-build',
            },
          ],
        },
        {
          type: 'dropdown',
          label: '关于',
          position: 'left',
          items: [
            {
              label: '关于本站',
              to: '/about',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/lucan6290',
            },
            {
              label: 'CSDN',
              href: 'https://blog.csdn.net/2301_80165396',
            },
          ],
        },
        {
          href: 'https://github.com/lucan6290',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'light',
      links: [
        {
          title: '内容',
          items: [
            {label: '知识库', to: '/docs/intro'},
            {label: '博客', to: '/blog'},
            {label: '项目', to: '/projects'},
          ],
        },
        {
          title: '站点',
          items: [
            {label: '关于', to: '/about'},
            {label: 'GitHub', href: 'https://github.com/lucan6290'},
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} 箓川码笺.`,
    },
    docs: {
      sidebar: {
        hideable: true,
        autoCollapseCategories: false,
      },
    },
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 3,
    },
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    prism: {
      additionalLanguages: ['java', 'bash', 'yaml', 'json', 'python'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
