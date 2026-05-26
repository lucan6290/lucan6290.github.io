# 博客依赖与版本记录

## 主题信息

**主题名称**：hexo-theme-butterfly  
**当前版本**：v5.5.5-b1  
**GitHub 仓库**：https://github.com/jerryc127/hexo-theme-butterfly  
**首次使用日期**：2026-05

## 主题安装说明

如果需要在新环境重新部署博客，请按以下步骤安装主题：

```bash
# 进入博客目录
cd blog

# 创建 themes 目录（如果不存在）
mkdir -p themes
cd themes

# 下载指定版本的主题
# 方式一：克隆完整仓库
git clone https://github.com/jerryc127/hexo-theme-butterfly.git butterfly
cd butterfly
git checkout v5.5.5-b1  # 切换到指定版本

# 或者方式二：下载压缩包（更简单）
# 访问 https://github.com/jerryc127/hexo-theme-butterfly/releases/tag/v5.5.5-b1
# 下载 Source code (zip) 并解压到 themes/butterfly/

# 回到项目根目录，安装依赖
cd ..
npm install
```

## 重要提醒

⚠️ **不要修改 `themes/butterfly/` 下的任何文件！**  
所有定制都在 `_config.butterfly.yml` 和 `source/css/custom.css` 中完成。

这样做的好处：
- 主题可以随时升级，不丢失配置
- 仓库更干净
- 未来迁移更容易

## 升级主题（当需要时）

```bash
cd themes/butterfly
git fetch origin
git checkout <新版本号>

# 或者
# 1. 删除旧的 themes/butterfly/
# 2. 重新下载新版本
```

升级前请：
1. 备份 `_config.butterfly.yml`
2. 查看主题的 CHANGELOG
3. 先在本地测试

---

## 其他依赖

| 依赖 | 用途 |
|-----|------|
| Hexo 8.1.2 | 静态网站生成器 |
| Butterfly 5.5.5-b1 | 主题 |
| hexo-generator-search | 搜索功能 |
| hexo-wordcount | 字数统计 |
| hexo-generator-feed | RSS 订阅 |

## 部署环境

- 平台：GitHub Pages
- CI/CD：GitHub Actions
- Node.js 版本：建议 >= 18.x