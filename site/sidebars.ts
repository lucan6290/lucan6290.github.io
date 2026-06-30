import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  overviewSidebar: [
    'intro',
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

  // 以下分类为占位结构，待补充对应文档后取消注释启用：
  // techStudySidebar（技术研习 / Java 面试题 / Java 基础）
  // resourceSharingSidebar（资源分享 / 测试）
};

export default sidebars;
