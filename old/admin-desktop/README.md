# 箓川码笺管理端（admin-desktop）

> 中文 | [English](docs/README.en.md)

箓川码笺（xiaocancoding）个人技术站与知识库系统的桌面端管理应用，基于 Tauri 2 + Vue 3，提供文章写作、编辑、图片管理、分类标签维护、预览构建等写作辅助能力。

## 主要功能

- 文章管理与编辑（ByteMD 富文本 + Front Matter）
- 媒体 / 图片管理
- 分类 / 标签维护（Registry）
- 预览构建
- AI 写作辅助
- 仪表盘与设置

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Pinia、ByteMD
- 桌面：Tauri 2（Rust）
- 打包：NSIS / MSI

## 快速开始

### 环境要求

- Node.js 22+
- Rust（stable）
- Tauri 系统依赖（Windows：WebView2、MSVC 构建工具）

### 安装与启动

```bash
npm install
npm run tauri:dev   # 本地开发（前端端口 14200）
```

## 开发

### 构建

```bash
npm run build           # 前端类型检查 + 构建
npm run tauri:build     # 打包安装包（NSIS / MSI）
```

### 质量检查

```bash
npm run build           # vue-tsc 类型检查 + vite build
```

## 项目结构

```
admin-desktop/
├── src/               # Vue 前端源码
├── src-tauri/         # Tauri / Rust 后端
├── src-backend/       # 本地 Python 后端（开发辅助）
├── scripts/           # 版本号 / changelog 脚本
└── docs/              # 英文文档
```

## 常见问题

- 打包失败：确认已安装 WebView2 与 Visual Studio C++ 构建工具
- 自动更新：需要配置签名密钥（见发布流程文档）

## 贡献与安全

- 贡献指南：[`CONTRIBUTING.md`](CONTRIBUTING.md)
- 行为准则：[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- 安全策略：[`SECURITY.md`](SECURITY.md)

## 开源协议

GPL-3.0 — 详见 [`LICENSE`](LICENSE)。
