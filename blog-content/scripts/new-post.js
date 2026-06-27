'use strict';

const path = require('path');
const fs = require('fs');

function loadCategoryRegistry(hexo) {
  const registryPath = path.join(hexo.base_dir, 'config', 'category-registry.json');
  const raw = fs.readFileSync(registryPath, 'utf8');
  return JSON.parse(raw);
}

function findCategory(registry, prefix1, prefix2) {
  const primary = registry.find(item => item.note_prefix1 === prefix1);
  if (!primary) return { primary: null, secondary: null };
  const secondary = (primary.children || []).find(item => item.note_prefix2 === prefix2);
  if (!secondary) return { primary, secondary: null };
  return { primary, secondary };
}

hexo.extend.console.register('np', '创建新文章（手动指定前缀）', {
  usage: '<一级前缀> <二级前缀> <标题>',
  arguments: [
    { name: '一级前缀', desc: 'ts(技术研习) / pr(踩坑复盘) / pp(项目实战) / ge(成长随笔) / rs(资源分享)' },
    { name: '二级前缀', desc: '技术栈/主题前缀，如 vue3, docker, annual 等' },
    { name: '标题', desc: '文章标题' }
  ]
}, function(args) {
  const hexo = this;
  
  const prefix1 = args._[0];
  const prefix2 = args._[1];
  const title = args._[2];
  
  if (!prefix1 || !prefix2 || !title) {
    console.log('错误: 参数不完整');
    console.log('\n用法: hexo np <一级前缀> <二级前缀> <标题>');
    console.log('\n一级前缀:');
    console.log('  ts - 技术研习 (source/_posts/tech-study/)');
    console.log('  pr - 踩坑复盘 (source/_posts/pitfall-review/)');
    console.log('  pp - 项目实战 (source/_posts/project-practice/)');
    console.log('  ge - 成长随笔 (source/_posts/growth-essay/)');
    console.log('  rs - 资源分享 (source/_posts/resource-sharing/)');
    console.log('\n示例:');
    console.log('  hexo np ts vue3 "Vue3组合式 API详解"');
    console.log('  → source/_posts/tech-study/ts-vue3-Vue3组合式 API详解.md');
    return;
  }
  
  let registry;
  try {
    registry = loadCategoryRegistry(hexo);
  } catch (error) {
    console.log(`错误: 无法读取分类注册表 config/category-registry.json: ${error.message}`);
    return;
  }

  const category = findCategory(registry, prefix1, prefix2);
  if (!category.primary) {
    console.log(`错误: 无效的一级前缀 "${prefix1}"`);
    console.log('请先在分类管理中维护 note_prefix1 对应关系');
    return;
  }
  if (!category.secondary) {
    console.log(`错误: 无效的二级前缀 "${prefix2}"`);
    console.log(`请先在分类管理中给 "${category.primary.frontend_name1}" 添加 note_prefix2`);
    return;
  }
  const { primary, secondary } = category;
  if (primary.enabled === false) {
    console.log(`错误: 一级分类已停用: ${primary.frontend_name1}`);
    return;
  }
  if (secondary.enabled === false) {
    console.log(`错误: 二级分类已停用: ${secondary.frontend_name2}`);
    return;
  }
  
  const fileName = `${prefix1}-${prefix2}-${title}.md`;
  const targetDir = path.join(hexo.source_dir, '_posts', primary.category_slug);
  
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }
  
  const filePath = path.join(targetDir, fileName);
  
  if (fs.existsSync(filePath)) {
    console.log(`错误: 文件已存在: ${filePath}`);
    return;
  }
  
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 19).replace('T', ' ');
  
  const content = `---
title: ${title}
date: ${dateStr}
updated:

categories:
  - [${primary.frontend_name1}, ${secondary.frontend_name2}]

tags:

description:

# Hexo 官方参数
layout: post
comments: true
permalink:
excerpt:
published: true
lang: zh-CN

# Butterfly 主题参数
cover: ${primary.cover}
sticky:

# 博客自定义参数
slug:
status: draft

# 系列文章（可选，3篇以上相关文章时使用）
series:
series_order:
---

`;

  fs.writeFileSync(filePath, content);
  
  console.log(`\n✅ 文章创建成功!`);
  console.log(`   文件: ${filePath}`);
  console.log(`   分类: ${primary.frontend_name1} / ${secondary.frontend_name2}`);
  console.log(`   前缀: ${prefix1}-${prefix2}-`);
  console.log(`   状态: draft (草稿)`);
});
