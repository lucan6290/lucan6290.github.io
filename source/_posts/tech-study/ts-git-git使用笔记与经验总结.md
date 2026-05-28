---
title: Git 使用笔记与经验总结
date: 2024-10-20 10:00:00
updated: 2026-05-26 15:00:00
categories:
  - [技术研习, 入门笔记]
tags: [git, 版本控制, 工具, note, 教程]
description: Git 常用操作笔记与踩坑经验总结，涵盖代码提交、分支管理、冲突解决、回退操作等实用场景。
cover: /img/covers/tech-study.svg
---

## 一、本地代码上传远程仓库

### 1. 提交本地修改到远程仓库（已连接到仓库分支）

已经完成代码修改并想推送到远程仓库时：

```bash
# 1. 查看本地修改（可选，确认要提交的文件）
git status

# 2. 添加所有修改的文件到暂存区（推荐）
git add .
# 若只想添加指定文件：git add 文件名（如 git add app/main.py）

# 3. 提交到本地仓库（备注要清晰）
git commit -m "你的提交备注"

# 4. 推送到远程仓库（已关联 master 分支，直接用这个）
git push
```

![git push 示意图]()

### 2. 提交本地修改到远程仓库（新建分支）

已连接到仓库、提交过代码，但仓库没有该分支，需要新建分支：

```bash
# 1. 创建并切换到本地新分支
git checkout -b 新分支名

# 2. 将本地新分支与远程仓库的同名分支建立关联（绑定上游）
git push -u origin 新分支名
```

执行后会：
- 自动在远程仓库创建 "新分支名" 分支
- 将本地 "新分支名" 与远程分支永久绑定
- 后续直接用 `git push` / `git pull` 同步

```bash
# 3. 正常执行上传流程
git add .
git commit -m "提交备注"
git push
```

### 3. 提交本地修改到远程仓库（本地分支落后于远程）

远程有你本地没有的新提交时：

**方案一：拉取合并再推送（推荐）**

```bash
# 切换到远程分支（如果不在需要拉取的仓库分支的话）
git checkout develop

# 拉取远程仓库代码到本地
git pull origin 仓库名

# 推送本地代码到远程仓库
git push
```

![git pull 示意图 1]()

![git pull 示意图 2]()

**方案二：强制推送（覆盖远程）**

{% note warning %}
除非是自己一个人开发的仓库，否则不建议这样操作！
{% endnote %}

```bash
git push -f origin 仓库名
```

![git push -f 示意图 1]()

![git push -f 示意图 2]()

### 4. 回退本地 commit（未 push）

本地代码进行了 commit 但还没进行 push 提交时：

先看提交日志，找到你想回退到的那个 commit 的哈希值：

```bash
git log --oneline
```

![git log 示意图]()

执行回退命令：

```bash
# 想保留代码修改，只删提交记录（推荐，不容易丢代码）
git reset abc123

# 想彻底删除所有改动，恢复到旧版本（慎用！改了的代码会丢）
git reset --hard abc123
```

![git reset 示意图]()

### 5. 撤回提交到暂存区但未推送的文件

提交时一些过程性文档没有被忽略，被一并提交了，但是还没有推送至远程仓库。（一些不该提交的 `.claude`、`.trae` 等目录文件，被 `git add` 甚至 `git commit` 了，现在要把它们从提交里 "退出来"）

![撤回暂存区文件示意图]()

#### 情况 1：文件已经被 add 了，但还没 commit

```bash
# 先把这些目录从暂存区全部撤下来（不影响文件内容）
git reset HEAD 文件名 文件夹/    # 撤销某个文件/文件夹的暂存
# 或者
git reset HEAD                  # 撤销所有暂存

# 然后把这些需要忽略的目录加到 .gitignore 里，永久禁止提交
echo -e ".claude/\n.trae/" >> .gitignore

# 以后再 git add -A / git add . ，这些文件就不会被加进去了
```

#### 情况 2：文件已经 commit 了（本地仓库里已经有提交记录）

这种情况，要把文件从 Git 仓库里删掉，但保留本地文件：

```bash
# 执行命令，从 Git 中移除这些目录（本地文件不会被删）
git rm --cached -r 文件名 文件夹名/
```

参数说明：
- `--cached`：只从 Git 仓库删除，不删你电脑上的文件
- `-r`：递归删除整个目录里的所有文件

```bash
# 把目录加到 .gitignore 里
echo "文件夹名/" >> .gitignore

# 提交这次清理操作
git add .gitignore
git commit -m "chore: 移除并忽略xxx目录"

# 或者使用 --amend 修改最近的一次提交
git commit --amend --no-edit

# 推送到远程（如果之前已经推过错误提交，这一步会覆盖掉它们）
git push
```

#### 情况 3：文件已经 push 到远程仓库了

![已推送文件撤回示意图]()

如果这些文件已经被推到了远程分支，除了上面的操作，还需要：

```bash
# 确保本地清理提交已经完成，再执行 git push，把清理记录推上去
```

{% note warning %}
远程仓库里旧的提交记录还是会保留这些文件，如果想彻底从历史里删除，可以用 `git filter-repo`，但这个操作风险很高，会修改提交历史，团队协作时一定要先和同事沟通好。
{% endnote %}

```bash
# 1. 从 Git 记录里删除目标文件夹（本地文件还在，不会删你东西）
git rm -r 目标文件夹/    # --cached 只取消追踪，不删除文件

# 2. 加入忽略，以后永远不会再提交
echo "目标文件夹/" >> .gitignore

# 3. 提交并推送到远程，远程就会删掉它
git add .
git commit -m "删除无用文件夹"
git push
```

### 6. 本地有修改未 add，pull 冲突

本地修改了文件，还没提交/暂存，直接执行 `git pull` 会被远程代码覆盖，Git 为了保护你的本地修改，直接中止了拉取！

![pull 冲突示意图]()

#### 方案一：保留本地修改

如果本地改动需要保留（比如本地开发时的配置修改）：

```bash
# 第一步：暂存你的本地修改（Git 会临时保存你的代码）
git stash

# 第二步：拉取远程最新代码（现在不会报错了）
git pull origin develop

# 第三步：恢复你刚才暂存的本地修改
git stash pop

# 第四步：重新推送代码
git push origin develop
```

#### 方案二：丢弃本地修改（远程覆盖本地）

如果本地改动是误改、没用的：

```bash
# 丢弃这两个文件的本地修改
git checkout -- .gitignore vite.config.js

# 拉取代码
git pull origin develop

# 推送代码
git push origin develop
```

#### 总结

| 问题 | 解决方案 |
|------|----------|
| 新报错原因 | 本地有未提交的文件修改，无法直接拉取远程代码 |
| 标准操作 | `git stash` → `git pull` → `git stash pop` → `git push` |
| 安全性 | 全程不会丢失你的代码，安全无风险 |

---

## 二、拉取远程仓库代码到本地

用 Git 拉取远程代码覆盖本地更改（本地代码更改错误，需要回退前面的更改代码）。

放弃本地所有修改，完全用远程仓库的最新代码覆盖本地，步骤如下：

### 核心操作（3 步搞定）

```bash
# 1. 先切换到目标分支（确保在正确的分支）
git checkout develop_v2.0

# 2. 放弃本地所有未提交的修改（关键！）
git reset --hard HEAD
# 或者重置到指定 commit
git reset --hard d55e4e487104ef77e02310197ea1732c0f418c25

# 3. 拉取远程最新代码，覆盖本地
git pull origin develop_v2.0
```

{% note danger %}
`git reset --hard` 会彻底清空本地工作区、暂存区的所有修改，还原到上一次提交的状态，本地改的代码会被完全清除，无法恢复，执行前确认！
{% endnote %}

### 如果本地有已提交但未推送的 commit

如果本地有 commit 没推到远程，要彻底回退到远程版本：

```bash
# 1. 切换到目标分支
git checkout develop_v2.0

# 2. 强制重置到远程分支的最新状态（完全覆盖本地所有提交）
git reset --hard origin/develop_v2.0
```

这一步会彻底删除本地所有未推送的 commit，完全和远程保持一致，是最彻底的覆盖方式。

### 命令对照表

| 命令 | 作用 | 注意事项 |
|------|------|----------|
| `git checkout develop_v2.0` | 切换到你要操作的分支 | 确保当前在正确的分支，避免误操作其他分支 |
| `git reset --hard HEAD` | 放弃本地所有未提交的修改 | 不可逆！本地修改会被永久删除 |
| `git pull origin develop_v2.0` | 拉取远程最新代码，合并到本地 | 执行完后，本地代码和远程完全一致 |
| `git reset --hard origin/develop_v2.0` | 强制本地分支和远程分支完全对齐 | 会删除本地所有未推送的 commit |

### 执行完验证

执行完后，用 `git status` 检查状态：

```bash
git status
```

正常会显示：

```
On branch develop_v2.0
Your branch is up to date with 'origin/develop_v2.0'.

nothing to commit, working tree clean
```

说明本地已经和远程完全一致，覆盖成功。

### 避坑提醒

1. 执行 `git reset --hard` 前，一定要确认本地修改不需要保留，因为这个操作不可逆，删除的代码找不回来。
2. 确保当前分支是正确的分支，不要在其他分支执行，避免误操作。
3. 如果拉取时提示 `fatal: Need to specify how to reconcile divergent branches`，执行 `git pull --rebase origin develop_v2.0` 即可。

---

## 三、创建 .gitignore 文件

### 创建并提交

```bash
# 创建 .gitignore 文件，写入忽略规则
# 把 .gitignore 加入版本管理
git add .gitignore
git commit -m "添加 .gitignore 忽略规则"
git push
```

### .gitignore 核心语法

| 规则 | 作用 | 示例 |
|------|------|------|
| 文件名 | 忽略指定文件 | `config.ini` |
| `*.后缀` | 忽略所有该后缀文件 | `*.log`、`*.pyc` |
| 目录名/ | 忽略整个目录 | `__pycache__/`、`node_modules/` |
| `!文件名` | 不忽略（例外） | `!.env.example` |
| `**/目录/` | 忽略任意层级的该目录 | `**/logs/` |
| `# 注释` | 说明文字 | `# 环境变量文件` |

### 从 Git 中移除已提交的忽略文件

若已经把 `.idea/`、`__pycache__/` 等提交到仓库了，`.gitignore` 不会自动删除已跟踪文件，需要执行：

```bash
# 从 Git 索引中移除，但保留本地文件
git rm -r --cached .idea/
git rm -r --cached __pycache__/
git rm -r --cached .env

# 提交移除操作
git add .
git commit -m "移除已提交的忽略文件"
git push
```

### 常用命令（管理忽略）

```bash
# 查看哪些文件会被忽略
git check-ignore -v 文件名

# 刷新忽略规则（修改 .gitignore 后）
git rm -r --cached . && git add .
```

---

## 四、Git 提交 commit 规范

### 最常用 7 种类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能（feature） | `feat: 添加用户登录功能` |
| `fix` | 修复 bug | `fix: 修复登录验证失败问题` |
| `docs` | 只修改文档（README、注释等） | `docs: 更新安装说明` |
| `style` | 格式调整（不影响代码逻辑，空格、分号、换行） | `style: 格式化代码` |
| `refactor` | 重构（既不是新增功能，也不是改 bug） | `refactor: 重构用户模块` |
| `test` | 测试相关 | `test: 添加登录单元测试` |
| `chore` | 构建/工具/依赖更新（打包、配置、脚手架） | `chore: 更新依赖版本` |

---

## 五、报错总结

### 1. git push 推送失败 - 本地分支落后于远程

推送本地修改的代码到远程分支时，远程分支有新代码，但是本地代码没有先更新（pull），本地修改推送失败。

**原因**：报错 `(fetch first)`，提示本地分支落后于远程，需要先拉取。

**解决方案**：

```bash
git pull    # 拉取远程最新代码
git push    # 重新推送
```

报错示例：

```
error: failed to push some refs to 'https://gitlab.example.com/project.git'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally. This is usually caused by another repository pushing to
hint: the same ref. You may want to first integrate the remote changes
hint: (e.g., 'git pull ...') before pushing again.
```

![git push 失败示意图]()

### 2. git pull 拉取失败 - 本地有未提交的修改

**原因**：本地有文件有未提交的修改，直接拉取远程代码会被覆盖，Git 为了保护改动，直接中止了合并操作。

**解决方案**：参考 [本地有修改未 add，pull 冲突](#6-本地有修改未-addpull-冲突)

**详细拆解**：

1. 前置信息：远程仓库的 develop 分支，已经更新到了新版本，比本地版本新，所以需要拉取更新。
2. 报错触发点：拉取过程中，Git 发现本地文件的改动还没 commit，如果直接合并，这些改动会被远程的代码覆盖。
3. Git 给的解决方案：提示 `Please commit your changes or stash them before you merge.`，也就是：
   - 要么先把本地修改提交（`git add . && git commit`）
   - 要么先暂存本地修改（`git stash`）

![git pull 失败示意图]()

---

## 总结

Git 是开发者必备的版本控制工具，掌握常用命令和踩坑解决方案能大大提高开发效率。本文总结了日常开发中最常见的 Git 操作场景：

1. **代码提交**：从基础的 add/commit/push 到分支管理
2. **冲突解决**：本地落后远程、本地有未提交修改等情况的处理
3. **回退操作**：commit 回退、暂存区撤回、强制覆盖等
4. **忽略规则**：.gitignore 的使用和已提交文件的移除
5. **提交规范**：保持代码仓库整洁的 commit message 规范

{% note info %}
记住一个原则：遇到问题先 `git status` 查看状态，大多数 Git 操作都可以通过 `--help` 参数查看帮助文档。
{% endnote %}

---
*每一次探索，都是成长*