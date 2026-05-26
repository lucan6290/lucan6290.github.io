# 箓川码笺

> 箓藏千思，川流不息 —— 于技术之川，拾字成箓

个人技术博客，记录学习、踩坑、成长的点滴。

## 博客信息

- **站点**：https://lucan6290.github.io
- **作者**：lucan
- **技术栈**：Hexo 8.1.2 + Butterfly 5.5.5-b1
- **部署**：GitHub Pages + GitHub Actions

## 本地开发

```bash
# 安装依赖
npm install

# 安装主题（如果 themes/butterfly/ 不存在）
# 下载 https://github.com/jerryc127/hexo-theme-butterfly/releases/tag/v5.5.5-b1
# 解压到 themes/butterfly/

# 本地预览
npm run server

# 构建静态文件
npm run build
```

## 目录结构

```
source/_posts/     # 博客文章
source/img/        # 图片资源
_config.yml        # Hexo 配置
_config.butterfly.yml  # 主题配置
source/css/custom.css  # 自定义样式
```

## 文章分类

| 分类 | 说明 |
|------|------|
| 技术研习 | 技术学习笔记、教程 |
| 踩坑复盘 | 问题排查与解决方案 |
| 项目实战 | 项目开发记录 |
| 成长随笔 | 求职、学习方法等 |
| 资源分享 | 工具推荐、资源整理 |

## 更多信息

- 主题安装：见 `THEME_SETUP.md`
- 开发规范：见 `.claude-guidelines.md`