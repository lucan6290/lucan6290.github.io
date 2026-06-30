# Docs 专题侧边栏规范

## 目标

`site/docs` 采用“专题级侧边栏”。

进入某个专题后，左侧只显示当前专题自己的目录，不显示全站所有一级分类。

例如：

```text
进入 技术研习
左侧只显示 技术研习 下的 Java 面试题、AI 学习等内容

进入 项目实战
左侧只显示 项目实战 下的项目文章

进入 资源分享
左侧只显示 资源分享 下的资源文章
```

## 目录原则

```text
site/docs/
├── tech-study/             # 技术研习
├── project-practice/       # 项目实战
├── resource-sharing/       # 资源分享
└── intro.md                # 知识库入口
```

新增专题时，建议使用英文 slug 作为文件夹名，中文只用于页面标题和侧边栏显示。

## 侧边栏规则

每个一级专题在 `site/sidebars.ts` 中拥有独立 sidebar。

示例：

```ts
const sidebars = {
  techStudySidebar: [
    {
      type: 'category',
      label: '技术研习',
      collapsed: false,
      items: [
        'tech-study/example',
      ],
    },
  ],

  projectPracticeSidebar: [
    {
      type: 'category',
      label: '项目实战',
      collapsed: false,
      items: [
        'project-practice/example',
      ],
    },
  ],
};
```

## 新增文章流程

1. 在对应专题目录下新增 Markdown 文件。
2. 在文章 Front Matter 中填写 `title`、`description`、`sidebar_position`。
3. 在对应 sidebar 中添加文章路径。
4. 运行 `npm run build` 验证。

## 新增专题流程

1. 在 `site/docs` 下新增英文专题文件夹。
2. 在 `site/sidebars.ts` 中新增独立 sidebar。
3. 将该专题下的文章加入新的 sidebar。
4. 后续如需入口，可在首页或知识库入口页添加链接。

## 不推荐做法

- 不把所有一级分类都放进同一个 sidebar。
- 不使用中文路径作为长期 URL。
- 不让无关专题出现在当前专题的左侧目录中。

