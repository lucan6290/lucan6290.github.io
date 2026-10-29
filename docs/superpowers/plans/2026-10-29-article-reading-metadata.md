# 文章阅读信息实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 知识库、博客、项目及自定义栏目的普通文章统一显示阅读时长、字数、开始写作时间、最新更新时间。

**Architecture:** 复用现有内容扫描和 `ArticleView.vue`。构建时计算 `wordCount` 与 `readingMinutes`，日期只读取 YAML，不用文件时间冒充文章时间。页面始终展示四项，缺失或无效日期显示“未记录”。

**Tech Stack:** Vue 3、TypeScript、Node.js 原生测试、gray-matter、pnpm。

**Spec:** `docs/SITE_CONTENT_GUIDE.md` 的六字段规范，以及本次用户确认的 `date` 表示开始写作时间。

## Global Constraints

- 阅读时长按每分钟 300 字估算，向上取整，至少 1 分钟；不加入 YAML。
- 中文按字、英文数字按词统计，排除 Markdown 标记、图片和围栏代码；复用现有口径。
- 新建文章的 `date` 与 `updated` 相同，页面仍同时显示两项；时间按 Asia/Shanghai 展示。
- 不批量改写已有文章，不增加自动更新时间回写或六字段强制校验，不新增依赖。
- 用户已明确授权实现；保留当前工作区的其他未提交修改。依用户 Git 边界在原工作区完成，不执行分支、提交、同步或推送操作。
- 本地服务固定 3400；已有本项目 preview 服务可用于构建后验证，不启动第二个服务。

## Review Focus

- 短文、空文和刚超过 300 字时，时长至少 1 分钟且正确进位。
- 波浪号及长反引号围栏、注释中的文本不会虚增字数。
- 缺失、无效日期不能取文件时间；未填写日期的文章仍能进入列表和搜索。
- 缺少日期的文章不会打乱有日期文章的排序，不进入错误归档月份。
- 创建与更新在同一天或同一时刻仍同时显示；窄屏正常换行。

## Task 1: 构建数据、文章展示与规范同步

**Files:**
- 修改 `frontend/scripts/lib/content.test.mjs`：内容统计、日期、排序回归测试。
- 修改 `frontend/scripts/lib/buildContent.mjs`：计算 `readingMinutes`，规范日期读取，处理无日期排序。
- 修改 `frontend/src/types/content.ts`：补齐 `readingMinutes: number`。
- 修改 `frontend/src/views/ArticleView.vue`：四项信息与北京时间显示。
- 修改 `frontend/src/components/list/SortToggle.vue`：日期入口改为创建时间。
- 修改 `frontend/src/composables/useContent.ts`、`frontend/src/views/HomePage.vue`：无日期排在日期降序的末尾。
- 同步 `docs/SITE_CONTENT_GUIDE.md`、`frontend/README.md` 的当前实现说明。

**Interfaces:**
- 输入：YAML `date` / `updated` 与去掉 YAML 的文章正文。
- 输出：`ArticleMeta.wordCount: number`、`readingMinutes: number`、有效时间字符串或空字符串。

- [x] RED：新增实际调用 `build()` 的测试，覆盖 0/1/300/301/2164 字、两种围栏、日期缺失/无效/相同/不同时刻、无日期的最近列表排序。运行 `node --test scripts/lib/content.test.mjs`，确认因缺失功能而失败。
- [x] GREEN：最少修改内容管线及类型，让上述测试通过。
- [x] 页面：复用现有 meta 区域展示四项，创建/更新时间精确到分钟，缺失显示“未记录”；保留原作者与标签区域。
- [x] 验证：运行 `pnpm test`、`pnpm build`、`git diff --check`；在现有 3400 服务检查实际文章、移动窄屏、日期相同时的展示。
- [x] 评审与文档：针对本次文件作独立代码评审，修复影响结果的问题，同步写作指南中的程序行为。

## 执行记录

- 基线：`pnpm test` 25/25 通过。
- 工作区：原有未提交修改涉及部署、搜索、桌面端等，本任务不覆盖这些改动。
- 初次 RED：新增 4 组测试均因缺失功能失败；GREEN：全套 29/29 通过，生产构建通过。
- 评审：独立评审发现代码中的注释起始符会吞掉正文、引用中的围栏代码被计数；新增两个失败用例及一个交互保护用例。
- 调整：复用现有 ByteMD `getProcessor().parse()`，只提取 Markdown 文本与行内代码节点统计，替换容易冲突的正则过滤，不新增依赖。
- 范围判定：不引入完整六字段/日期格式强校验，不批量修改历史日期；1970 年之前的写作时间无当前内容触发路径，归档按构建机器月份为原有行为，不扩展本次四项展示的范围。
- 最终修复验证：两个评审反例已 RED→GREEN，另一个注释/围栏交互用例通过；全套 `pnpm test` 32/32 通过，`pnpm build` 通过，仍有原有的大包体积提示。
- 页面验证：现有 3400 preview 服务中验证了四项、相同日期、缺失日期、创建时间排序及 390px 窄屏换行（无横向溢出）。最终构建刷新后浏览器控制台无错误，截图保存在当前会话可视化目录。
- 用户追加：四项信息悬停时按参考图显示黑底白字、小三角、说明文字加 emoji 的气泡；使用 CSS 实现，并支持 Tab 聚焦显示。
- 提交授权：用户随后明确要求“提交修改”，因此允许为本功能创建一次本地提交；不推送，不纳入其他任务的部署、搜索或桌面管理端改动。
