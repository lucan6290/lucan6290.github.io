# 后端破坏式重构契约草案

本文档记录管理后台后端从旧 API 到新版 `src` 布局与 `/api/admin/v1` 命名空间的迁移约定。它用于约束并行重构期间的接口形状，具体实现可在保持契约的前提下调整内部模块。

## 目标

- 新后端统一暴露 `/api/admin/v1` 前缀，避免和历史 `/api/*` 路径混杂。
- 健康检查固定为 `GET /api/admin/v1/health`，供前端、测试和本地启动脚本探活。
- 文件、资源、AI、Git 相关能力按领域拆分 router，业务实现迁入 `src` 布局。
- 写操作、Git 操作、AI 网络调用在契约测试中不被真实触发。

## 旧 API 到新 API 迁移表

| 旧 API | 新 API | 说明 |
|---|---|---|
| `GET /health` | `GET /api/admin/v1/health` | 根级健康检查迁入版本化管理 API。 |
| `GET /api/health` | `GET /api/admin/v1/health` | 前端路由守卫改用新健康检查。 |
| `GET /api/files/posts` | `GET /api/admin/v1/posts` | 获取文章列表。 |
| `POST /api/files/post` | `POST /api/admin/v1/posts` | 创建文章草稿。 |
| `GET /api/files/post/{path}` | `GET /api/admin/v1/posts/{path}` | 读取文章。 |
| `PUT /api/files/post/{path}` | `PUT /api/admin/v1/posts/{path}` | 更新文章。 |
| `DELETE /api/files/post/{path}` | `DELETE /api/admin/v1/posts/{path}` | 删除文章。 |
| `GET /api/files/category-registry` | `GET /api/admin/v1/categories/registry` | 读取分类注册表。 |
| `PUT /api/files/category-registry` | `PUT /api/admin/v1/categories/registry` | 保存分类注册表。 |
| `GET /api/files/article-index` | `GET /api/admin/v1/articles/index` | 读取本地文章索引。 |
| `POST /api/files/article-index/scan` | `POST /api/admin/v1/articles/index/scan` | 重建本地文章索引。 |
| `POST /api/assets/image` | `POST /api/admin/v1/assets/images` | 上传文章图片。 |
| `GET /api/assets/images/{path}` | `GET /api/admin/v1/assets/images/{path}` | 列出文章图片。 |
| `GET /api/assets/image-folders` | `GET /api/admin/v1/assets/folders` | 列出含图片的资源文件夹。 |
| `POST /api/assets/unused` | `POST /api/admin/v1/assets/unused` | 扫描未引用图片。 |
| `POST /api/assets/cleanup-unused` | `POST /api/admin/v1/assets/cleanup-unused` | 清理未引用图片。 |
| `GET /api/assets/file/{path}` | `GET /api/admin/v1/assets/file/{path}` | 预览文章资源文件。 |
| `POST /api/git/commit` | `POST /api/admin/v1/git/commit` | 本地提交。 |
| `POST /api/git/push` | `POST /api/admin/v1/git/push` | 推送远端。 |
| `POST /api/git/deploy` | `POST /api/admin/v1/git/deploy` | 一键部署。 |
| `GET /api/ai/presets` | `GET /api/admin/v1/ai/presets` | 获取 AI 模型预设。 |
| `POST /api/ai/test` | `POST /api/admin/v1/ai/test` | 测试模型连接。 |
| `POST /api/ai/chat` | `POST /api/admin/v1/ai/chat` | AI 流式对话。 |
| `POST /api/ai/writing/material/extract` | `POST /api/admin/v1/ai/writing/material/extract` | 提取写作素材文本。 |
| `POST /api/ai/writing/agent/plan` | `POST /api/admin/v1/ai/writing/agent/plan` | 生成草稿方案，不写入文件。 |
| `POST /api/ai/writing/agent/commit` | `POST /api/admin/v1/ai/writing/agent/commit` | 确认后写入草稿。 |
| `POST /api/ai/writing/edit/plan` | `POST /api/admin/v1/ai/writing/edit/plan` | 生成编辑方案。 |
| `POST /api/ai/writing/edit/apply` | `POST /api/admin/v1/ai/writing/edit/apply` | 应用编辑方案。 |
| `POST /api/ai/knowledge-qa` | `POST /api/admin/v1/articles/knowledge-qa` | 本地知识库问答。 |

## 建议的 src 布局

```text
admin-dev/backend/
├── src/
│   └── blog_admin/
│       ├── main.py              # FastAPI app 工厂或 app 实例
│       ├── api/
│       │   └── admin/v1/        # /api/admin/v1 router 聚合
│       ├── core/                # 配置、日志、路径、安全边界
│       └── modules/             # content/assets/ai/article_index/categories/gitops
├── tests/
│   └── test_admin_v1_contract.py
├── main.py                      # 兼容入口，可委托到 src 包
├── pyproject.toml
├── requirements.txt
└── .env.example
```

旧 `backend/app` 包已完成迁移并删除；正式后端代码位于 `src/blog_admin/`。新路由在 `src/blog_admin/api/admin/v1/` 下注册，`main.py` 作为本地启动入口，委托到 `blog_admin.main:app`。

## 当前模块边界

- `api/admin/v1/` 只负责 HTTP 入参、路由声明和响应返回，不直接执行文件、Git 或 AI 模型操作。
- `core/` 放置跨模块公共能力，包括配置、错误、响应包络、路径安全和命令策略。
- `modules/content/` 负责文章 CRUD、Front Matter 和文章总目录同步。`content/application.py` 只编排文章用例；`content/repository.py` 负责文章文件读写与资源文件夹删除；`content/index_sync.py` 负责 `index.md` 同步；Hexo CLI 调用下沉到 `content/infrastructure.py`。
- `modules/assets/` 负责文章资源文件夹、图片上传/预览和未引用图片清理。`assets/repository.py` 只处理路径解析与文件/目录读写，`assets/scanner.py` 只解析 Markdown、HTML `<img>` 与 Hexo `{% asset_img %}` 图片引用，`assets/image_naming.py` 只处理 Base64 解码、图片编号和上传命名策略，`assets/service.py` 仅作为组合门面。
- `modules/categories/` 是分类注册表唯一来源。其它模块需要分类信息时从该模块读取，不再复制注册表实现。保存一级分类时，后端同步补齐博客侧资产：`source/_posts/{category_slug}/` 文章目录、`source/img/covers/{category_slug}.svg` 默认封面、`_config.yml` 的 `category_map` 一级映射，以及 `source/_posts/index.md` 中的一级分类占位 section。
- `modules/article_index/` 是文章索引、缓存、检索和知识库问答的唯一来源。AI 写作模块只调用它，不再维护自己的文章索引副本。
- `modules/ai/` 只负责模型构建、提示词、AI 写作/编辑编排和安全校验；真实文章读写必须通过 `modules/ai/post_io.py` 委托到 `modules/content` 用例完成，AI 模块内禁止直接文件写入、删除或创建目录。
- `modules/gitops/` 统一封装 Git commit/push/deploy，命令参数必须经过 `core.command_policy` 校验。Git 命令只允许 `git add <target>`、`git commit -m <message>`、`git push origin` 三种固定形态；路径禁止绝对路径、`..` 越权和仓库根目录指定提交；执行器写入 `.cache/gitops-audit.jsonl` 作为 JSONL 审计日志，记录 started/succeeded/failed/rejected 事件。

后续结构优化继续按“应用层编排、基础设施层封装外部副作用、领域规则逐步纯化”的方向推进。

## 响应包络

所有 JSON API 统一返回以下响应包络：

```json
{ "success": true, "data": {} }
```

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "可读错误信息",
    "details": {}
  }
}
```

业务失败、路径越权、HTTP 异常和 FastAPI 参数校验错误均映射到统一错误结构。旧式 `ApiResponse` 和响应兼容转换函数已移除；后续新增模块应直接使用 `core.response.ok()` 与 `core.response.fail()`。

## 启动命令

### 安装依赖

```bash
cd admin-dev/backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

### 本地启动

```bash
cd admin-dev/backend
.venv/Scripts/python.exe main.py
```

或直接使用 Uvicorn：

```bash
cd admin-dev/backend
.venv/Scripts/python.exe -m uvicorn blog_admin.main:app --app-dir src --host 0.0.0.0 --port 15000 --reload
```

旧 `app.main:app` 已移除，不再作为入口使用。

### 测试与静态检查

```bash
cd admin-dev/backend
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m pytest -m contract
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m mypy .
```

契约测试真实请求健康检查、分类读取、文章未找到、无效文章创建、资源参数错误和 FastAPI 422 参数校验，验证成功与失败响应包络；Assets 单元测试覆盖路径穿越、绝对路径、非图片预览、缺失图片错误和未引用图片扫描；GitOps 单元测试覆盖命令白名单、路径拒绝、commit/deploy 编排和审计日志；AI 写作单元测试覆盖 post_io 委托、agent commit/edit apply 写入边界、风险确认拦截和 Front Matter 发布限制；其它写重型或 AI 网络请求仍通过 OpenAPI path/method 检查避免真实副作用。
