"""
index.md 解析器测试 fixtures
"""
import pytest


INDEX_MD_SAMPLE = """\
---
title: 博客文章目录
date: 2026-05-28 10:00:00
categories:
  - [博客导航]

tags:

description: 箓川码笺博客文章总目录，按分类组织所有已发布文章。

cover: /img/covers/blog-index.svg
sticky: 9999
slug: blog-index
status: published
---

**📚 箓川码笺文章总目录**

---

## 一、技术研习

### 1.1 AI 探索

- [Agent 入门笔记](/2026/05/20/tech-study/ts-ai-agent入门笔记/)
- [Claude Code 入门指南](/2026/05/22/tech-study/ts-claude-code入门与安装/)

### 1.2 入门笔记

- [Git 使用笔记与经验总结](/2024/10/20/tech-study/ts-git-git使用笔记与经验总结/)

---

## 二、踩坑复盘

### 2.1 环境配置

- [虚拟机配置共享目录](/2025/03/29/pitfall-review/pr-vmware-共享目录配置/)

---

## 三、项目实战

*暂无文章，敬请期待*

---

## 四、成长随笔

### 4.1 博客建设

- [博客架构与长期发展规划](/2026/05/23/growth-essay/ge-blog-博客架构与长期发展规划/)
- [Hexo 博客搭建记录](/2026/05/21/growth-essay/ge-hexo-博客搭建记录/)

### 4.2 AI 思考

- [别再研究Prompt了](/2026/06/04/growth-essay/ge-ai-thinking-别再研究Prompt了/)

---

## 五、资源分享

*暂无文章，敬请期待*

---

*持续更新，记录成长*
"""


@pytest.fixture
def sample_index_md() -> str:
    """包含 5 个一级分类的完整样本 index.md"""
    return INDEX_MD_SAMPLE
