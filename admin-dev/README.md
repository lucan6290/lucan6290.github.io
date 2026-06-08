# 博客管理后台

箓川码笺博客的 Vue3 管理后台，支持在线和本地两种模式管理博客文章。

## 功能列表

- **文章管理**：创建、编辑、删除博客文章
- **Markdown 编辑器**：基于 ByteMD 的实时编辑体验
- **Front Matter 编辑**：可视化编辑文章元数据
- **媒体资源管理**：上传和管理文章图片
- **分类与标签**：管理文章分类和标签
- **AI 助手**：集成 AI 辅助写作功能
- **双模式支持**：
  - **在线模式**：通过 GitHub API 远程管理，适合云端部署
  - **本地模式**：通过本地服务器直接操作文件，适合本地开发

## 技术栈

- **前端框架**：Vue 3 + TypeScript
- **构建工具**：Vite 8
- **路由管理**：Vue Router 5
- **状态管理**：Pinia 3
- **UI 组件**：Naive UI 2
- **Markdown 编辑**：ByteMD + bytemd/vue-next
- **GitHub API**：Octokit 5
- **本地服务器**：Express + TypeScript

## 开发指南

### 安装依赖

```bash
# 安装前端依赖
cd admin-dev
npm install

# 安装本地服务器依赖（用于本地模式）
cd server
npm install
```

### 启动开发服务器

```bash
# 在 admin-dev 目录下
npm run dev
```

开发服务器启动后访问 http://localhost:5173/admin/

### 启动本地模式后端

本地模式需要启动 Express 服务器：

```bash
# 在 admin-dev/server 目录下
npm run dev
```

服务器启动在 http://localhost:3001

### 本地模式使用流程

1. 启动本地服务器（`admin-dev/server`）
2. 启动前端开发服务器（`admin-dev`）
3. 在管理后台切换到「本地模式」
4. 开始管理博客文章

## 构建部署

### 构建命令

```bash
# 在 admin-dev 目录下
npm run build
```

构建产物输出到 `../source/admin/` 目录，与 Hexo 博客静态文件一同部署。

### 部署到 GitHub Pages

管理后台随博客一起部署到 GitHub Pages：

1. 运行 `npm run build` 构建管理后台
2. 在博客根目录运行 `npm run build` 构建 Hexo
3. 推送到 GitHub，触发自动部署

访问地址：`https://your-blog.github.io/admin/`

## 配置说明

### GitHub OAuth App 配置

在线模式需要配置 GitHub OAuth App：

#### 创建 OAuth App

1. 访问 GitHub Settings → Developer settings → OAuth Apps → New OAuth App
2. 填写应用信息：
   - **Application name**：博客管理后台
   - **Homepage URL**：`https://your-blog.github.io/admin/`
   - **Authorization callback URL**：`https://your-blog.github.io/admin/login`
3. 创建后获取 **Client ID**

#### 配置 Client ID

修改 `src/config/github.ts`：

```typescript
export const githubConfig = {
  clientId: 'YOUR_GITHUB_CLIENT_ID', // 替换为你的 Client ID
  scope: 'repo',
  owner: 'your-username', // 替换为你的 GitHub 用户名
  // ...
}
```

### AI 模型配置

在管理后台的「设置」页面配置 AI 模型：

- **API 地址**：AI 服务端点（如 Ollama、OpenAI 等）
- **模型名称**：使用的模型名称
- **API Key**：如果需要认证

### 环境变量

如需在生产环境使用不同的配置，可以创建 `.env.production`：

```env
VITE_GITHUB_CLIENT_ID=your_client_id
VITE_GITHUB_OWNER=your_username
```

## 使用说明

### 在线模式

1. 访问管理后台 `/admin/`
2. 点击「使用 GitHub 登录」
3. 输入 GitHub 提供的验证码
4. 完成授权后即可管理文章
5. 所有操作通过 GitHub API 进行

**适用场景**：
- 远程管理博客
- 无需本地环境
- 需要推送更改到 GitHub

### 本地模式

1. 启动本地服务器（`admin-dev/server`）
2. 访问管理后台 `/admin/`
3. 切换到「本地模式」
4. 直接操作本地文件系统

**适用场景**：
- 本地开发调试
- 快速编辑文章
- 无需网络连接

## 项目结构

```
admin-dev/
├── server/           # 本地模式 Express 服务器
│   ├── index.ts      # 服务器入口
│   ├── types.ts      # 类型定义
│   └── package.json
├── src/
│   ├── api/          # API 调用层
│   │   ├── auth.ts   # 认证相关
│   │   ├── github.ts # GitHub API
│   │   ├── local.ts  # 本地服务器 API
│   │   └── index.ts  # API 统一入口
│   ├── components/   # Vue 组件
│   │   ├── AIAssistant.vue
│   │   └── NewPostModal.vue
│   ├── config/       # 配置文件
│   │   └── github.ts
│   ├── stores/       # Pinia 状态管理
│   │   ├── auth.ts   # 认证状态
│   │   ├── mode.ts   # 模式切换
│   │   ├── posts.ts  # 文章状态
│   │   └── settings.ts
│   ├── types/        # TypeScript 类型
│   ├── utils/        # 工具函数
│   ├── views/        # 页面视图
│   │   ├── Dashboard.vue
│   │   ├── Editor.vue
│   │   ├── Home.vue
│   │   ├── Login.vue
│   │   ├── Media.vue
│   │   ├── Posts.vue
│   │   └── Settings.vue
│   ├── App.vue
│   ├── main.ts
│   └── router.ts
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## 常见问题

### Q: 构建后页面空白？

检查 `vite.config.ts` 的 `base` 配置是否正确设置为 `/admin/`。

### Q: GitHub 登录失败？

1. 确认 OAuth App 配置正确
2. 检查 Client ID 是否已替换
3. 确认回调地址与实际地址一致

### Q: 本地模式无法连接？

1. 确认本地服务器已启动（`admin-dev/server`）
2. 检查端口 3001 是否被占用
3. 确认 CORS 配置包含前端地址

### Q: 如何添加新功能？

1. 在 `src/views/` 创建新页面
2. 在 `src/router.ts` 添加路由
3. 在 `src/stores/` 添加状态管理（如需要）
4. 在 `src/api/` 添加 API 调用

### Q: 如何修改博客根目录？

修改 `server/index.ts` 中的 `BLOG_ROOT` 常量：

```typescript
const BLOG_ROOT = 'E:\\A-Code\\blog'; // 替换为你的博客路径
```

## 开发注意事项

- **不要修改 `source/admin/`**：这是构建产物，每次构建都会清空
- **本地服务器仅用于开发**：生产环境使用在线模式
- **提交前先构建**：确保管理后台更新已包含在博客部署中
- **Client ID 不要提交**：建议使用环境变量管理敏感配置