import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  overviewSidebar: [
    'index',
  ],

  projectPracticeSidebar: [
    {
      type: 'category',
      label: '项目实战',
      collapsed: false,
      link: {
        type: 'doc',
        id: 'project-practice/index',
      },
      items: [
        {
          type: 'category',
          label: '开发规范',
          collapsed: false,
          items: [
            'project-practice/开发规范/单人全栈开发高效流程',
          ],
        },
        {
          type: 'category',
          label: '博客建设',
          collapsed: false,
          items: [
            'project-practice/博客建设/新增文章同步维护规范',
          ],
        },
      ],
    },
  ],

  'resource-sharingSidebar': [
    {
      type: 'category',
      label: '资源分享',
      collapsed: false,
      link: {
        type: 'doc',
        id: 'resource-sharing/index',
      },
      items: [
        {
          type: 'category',
          label: '测试资源分享',
          collapsed: false,
          items: [
            'resource-sharing/测试资源分享/测试资源分享',
          ],
        },
      ],
    },
  ],

  techStudySidebar: [
    {
      type: 'category',
      label: '技术研习',
      collapsed: false,
      link: {
        type: 'doc',
        id: 'tech-study/index',
      },
      items: [
        {
          type: 'category',
          label: 'AI 探索',
          collapsed: false,
          items: [
            'tech-study/AI 探索/agent入门笔记',
            'tech-study/AI 探索/claude-code入门与安装',
            'tech-study/AI 探索/claude-code项目开发规范',
            'tech-study/AI 探索/claude-code使用技巧',
            'tech-study/AI 探索/ocr模型生产环境部署',
          ],
        },
        {
          type: 'category',
          label: 'Jetson Orin Nano',
          collapsed: false,
          items: [
            'tech-study/Jetson Orin Nano/开发板信息概览',
            'tech-study/Jetson Orin Nano/板载硬件信息',
            'tech-study/Jetson Orin Nano/完整换源操作指南',
            'tech-study/Jetson Orin Nano/Miniforge安装',
            'tech-study/Jetson Orin Nano/Conda常用命令',
            'tech-study/Jetson Orin Nano/深度学习环境搭建',
            'tech-study/Jetson Orin Nano/性能模式管理',
            'tech-study/Jetson Orin Nano/温度自动调整风扇转速',
            'tech-study/Jetson Orin Nano/Docker常用命令',
            'tech-study/Jetson Orin Nano/Ollama部署LLM',
            'tech-study/Jetson Orin Nano/Ollama开机自启与局域网访问',
            'tech-study/Jetson Orin Nano/Ollama常用命令',
            'tech-study/Jetson Orin Nano/Ollama模型选择指南',
            'tech-study/Jetson Orin Nano/YOLO后台独立训练',
            'tech-study/Jetson Orin Nano/YOLO内存不足问题解决',
            'tech-study/Jetson Orin Nano/查询系统与开发环境命令',
            'tech-study/Jetson Orin Nano/Vim命令操作手册',
            'tech-study/Jetson Orin Nano/常见错误解决笔记',
            'tech-study/Jetson Orin Nano/相关教程与资源链接',
          ],
        },
        {
          type: 'category',
          label: '开发工具入门',
          collapsed: false,
          items: [
            'tech-study/开发工具入门/git使用笔记与经验总结',
            'tech-study/开发工具入门/帮我写一篇hexo博客迁移成Docusaurus的方案',
          ],
        },
      ],
    },
  ],

};

export default sidebars;
