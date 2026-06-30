import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  overviewSidebar: [
    'intro',
  ],

  techStudySidebar: [
    {
      type: 'category',
      label: '技术研习',
      collapsed: false,
      items: [
        {
          type: 'category',
          label: 'Java 面试题',
          collapsed: false,
          items: [
            {
              type: 'category',
              label: 'Java 基础',
              collapsed: false,
              items: [
              ],
            },
          ],
        },
      ],
    },
  ],

  projectPracticeSidebar: [
    {
      type: 'category',
      label: '项目实战',
      collapsed: false,
      items: [
        {
          type: 'category',
          label: '开发规范',
          collapsed: false,
          items: [
            'project-practice/development-standards/单人全栈开发高效流程',
          ],
        },
      ],
    },
  ],

  resourceSharingSidebar: [
    {
      type: 'category',
      label: '资源分享',
      collapsed: false,
      items: [
        {
          type: 'category',
          label: '测试',
          collapsed: false,
          items: [
          ],
        },
      ],
    },
  ],
};

export default sidebars;
