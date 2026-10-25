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
          numberPrefixParser: false,
          showLastUpdateTime: false,
          showLastUpdateAuthor: false,
        },
        blog: {
          path: 'blog',
          routeBasePath: 'blog',
          showReadingTime: true,
          exclude: ['**/_*.{js,jsx,ts,tsx,md,mdx}', '**/_*/**', '**/index.{md,mdx}'],
          onUntruncatedBlogPosts: 'ignore',
          postsPerPage: 8,
          blogListComponent: '@site/src/components/BlogHomePage',
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

  plugins: [
    './plugins/blog-category-pages',
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
              label: '首页',
              to: '/docs/',
            },
            {
              label: '技术研习',
              to: '/docs/tech-study',
            },
            {
              label: '项目实战',
              to: '/docs/project-practice',
            },
            {
              label: '资源分享',
              to: '/docs/resource-sharing',
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
              label: 'AI观察',
              to: '/blog/AI观察',
            },
{
  label: '随笔感想',
  to: '/blog/随笔感想',
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
              to: '/docs/project-practice',
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
            {label: '知识库', to: '/docs/'},
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
