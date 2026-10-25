**GitHub 是唯一长期可信源；本地电脑和腾讯云服务器都只是工作端。**

然后发布逻辑不要分裂成两套，而是在现有 `DeployService` 上扩展成三类能力：

```text
1. 发布/同步到 GitHub
2. 从 GitHub 更新服务器
3. GitHub SSH 权限配置检测
```

**一、三个端的职责**
本地端，你的电脑：

```text
用途：
- 管理后端开发
- 管理前端开发
- 博客写作
- 整站代码维护

发布范围：
- 可以 git add -A
- 可以推 main / develop / 自定义分支
```

腾讯云服务器端：

```text
用途：
- 线上博客运行
- 线上管理端写文章
- 内容维护、图片维护、分类维护

默认发布范围：
- 默认只 git add site
- 也允许高级选择 git add -A / 自定义路径
- 默认推 develop
- 可选推 main / 自定义分支
```

GitHub 端：

```text
用途：
- 存最新代码
- 存最新文章
- main 触发 GitHub Pages 静态博客
- develop 作为默认内容同步/备份分支
```

**二、现有 DeployService 应该怎么改**
你说的这个方向是对的：

> DeployService 把 `git add -A` 改成可配置路径。

我建议新增这些字段：

```python
stage_mode: "site" | "all" | "custom" = "site"
paths: list[str] = ["site"]
branch: str = "develop"
run_build_first: bool = True
clean_build: bool = False
allow_rebase: bool = True
```

对应逻辑：

```text
stage_mode = site
  -> git add -- site

stage_mode = all
  -> git add -A

stage_mode = custom
  -> git add -- <用户选择的路径>
```

前端发布弹窗里可以这样设计：

```text
目标分支：
[develop] [main] [自定义]

同步范围：
[site 内容（默认）]
[当前文章和图片]
[全部变更 -A]
[自定义路径]

发布前：
[x] npm run build
[ ] 清理 site/build
```

默认值我建议：

```text
branch = develop
stage_mode = site
run_build_first = true
```

这样最符合你服务器端“只写文章、同步备份”的核心场景。

**三、推送前 fetch 和分支关系检查**
必须加，而且不能简单粗暴 `git pull`。

推荐流程是：

```text
1. git fetch origin <branch>
2. 保存文章
3. npm run build
4. git add -- <范围>
5. git commit -m "<message>"
6. git fetch origin <branch>
7. 判断本地 HEAD 和 origin/<branch> 的关系
8. 能直接 push 就 push
9. 需要 rebase 就自动 rebase
10. rebase 冲突就停止，返回冲突日志给前端
```

判断逻辑：

```bash
git merge-base --is-ancestor origin/develop HEAD
```

如果成立：

```text
远端分支是本地 HEAD 的祖先
本地包含远端最新内容
可以 push
```

如果不成立，再判断：

```bash
git merge-base --is-ancestor HEAD origin/develop
```

如果成立：

```text
本地落后于 GitHub
可以尝试 git rebase origin/develop
rebase 成功后再 push
```

如果两边都不成立：

```text
本地和 GitHub 分叉了
可以尝试 rebase
有冲突就停止
绝不自动 force push
```

我的原则：

```text
允许自动 rebase
允许无冲突自动继续
不允许自动解决冲突
不允许 force push
```

**四、如果服务器和 GitHub 不一致怎么办**
分情况。

情况 1：服务器只有文章改动，GitHub 没新提交：

```text
直接 commit + push
```

情况 2：GitHub 有新提交，服务器也有文章改动，但不冲突：

```text
服务器 commit
git fetch
git rebase origin/<branch>
npm run build
git push
```

情况 3：GitHub 和服务器改了同一篇文章：

```text
rebase 冲突
停止发布
前端显示冲突文件
用户手动处理
```

情况 4：服务器有未提交的非 site 改动，但用户选择只同步 site：

```text
允许只提交 site
但推送前日志要提示：
存在未同步的非 site 变更，不会被提交
```

情况 5：用户要“服务器更新最新代码”：

```text
先检查 git status
如果有未发布文章变更：
  提示先发布/同步，或者放弃本地变更
如果干净：
  git fetch origin <branch>
  git pull --ff-only origin <branch>
  npm ci / npm run build
  构建管理前端
  更新后端依赖
  restart systemd
  reload nginx
```

这个应该是单独按钮，不要和“发布文章”混在一个按钮里。

**五、服务器 GitHub 权限怎么做**
我的意见依然是：

**不要做 GitHub 登录。不要让用户在后台填 GitHub 密码或 PAT。先做 Deploy Key 管理。**

原因：

```text
GitHub OAuth / PAT 管理复杂
要加密存储 token
要做 token 失效处理
要做权限最小化
要防止 token 泄露
你的场景其实只是“这台服务器能写这个仓库”
Deploy Key 正好匹配
```

管理前端可以加一个“GitHub 同步设置”，但不是账号登录，而是服务器密钥配置：

```text
GitHub 同步设置
- 当前 remote URL
- 默认同步分支：develop
- 默认同步范围：site
- Git 用户名
- Git 邮箱
- 生成服务器 SSH Deploy Key
- 显示 public key
- 测试 GitHub SSH 连接
- 测试 push 权限
```

流程：

```text
1. 管理端点击“生成 Deploy Key”
2. 后端在服务器生成 ~/.ssh/xiaocancoding_deploy
3. 前端显示公钥
4. 用户复制公钥
5. 到 GitHub 仓库 Settings -> Deploy keys 添加
6. 勾选 Allow write access
7. 管理端点击“测试连接”
```

服务器内部配置：

```bash
git remote set-url origin git@github.com:lucan6290/lucan6290.github.io.git
git config user.name "lucan-server"
git config user.email "server@xiaocancoding.local"
```

**六、我建议最终功能分成两个入口**
入口 1：编辑器里的“发布/同步到 GitHub”

```text
用于文章写完后同步
默认：
  branch = develop
  stage = site
  build = true
```

入口 2：设置页里的“服务器更新”

```text
用于把 GitHub 最新代码拉到服务器
默认：
  branch = main 或 develop，可配置
  pull 前必须工作区干净
  拉取后重建前端、重启后端
```

这样语义很清楚：

```text
发布/同步：服务器 -> GitHub
服务器更新：GitHub -> 服务器
```

**七、我最推荐的落地顺序**
第一阶段，先改核心发布逻辑：

```text
1. DeployRequestDTO 增加 stage_mode / paths / allow_rebase
2. DeployService 支持 git add -- site / git add -A / git add -- custom paths
3. push 前增加 git fetch + 分支关系检查 + 安全 rebase
4. 前端发布弹窗增加“同步范围”
```

第二阶段，加 GitHub 同步设置：

```text
1. 生成 Deploy Key
2. 显示公钥
3. 测试 SSH
4. 测试 push 权限
```

第三阶段，加服务器更新：

```text
1. 检查 dirty
2. fetch/pull
3. npm ci/build
4. 重启 backend
5. reload nginx
```

**最终我的判断**
你现在的目标不需要新造一套系统。最稳的是：

```text
沿用现有“发布到 GitHub”
扩展成“可选同步范围 + 安全分支同步 + Deploy Key 配置”
```

默认给服务器写作场景：

```text
推 develop
只提交 site
构建通过才推
冲突不自动处理
不 force push
```

高级场景再开放：

```text
推 main
推自定义分支
提交 -A
提交自定义路径
```

这个设计最贴合你现在的本地端、服务器端、GitHub 三端协作方式。