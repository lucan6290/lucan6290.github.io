# 桌面文章六字段模板 Implementation Plan

> 用户已明确“开始实现”；使用 writing-plans、test-driven-development 和独立子任务/审阅流程，不再重复询问编码授权。禁止提交 Git。

**Goal:** 普通新文章自动具备统一 YAML，保存时校验，实际修改维护 updated，保护原有文档与外部编辑冲突。

**Spec:** `docs/SITE_CONTENT_GUIDE.md` 的统一 YAML 头部；本次用户六字段要求与实现授权。此前第一阶段“不补头部/日期”被本次明确要求在普通文章范围内替代。

**Architecture:** Vue 生成可编辑六字段模板；Python 按同一契约验证新文章，并在通过版本检查后只替换 updated 的值，不全量重序列化原文。字段顺序 title/date/updated/description/tags/sticky，字符串双引号，tags行内数组，sticky布尔。

## Decisions / Interfaces

- POST `/api/v1/documents` 新增 `article: boolean = true`，普通新建默认true；显式说明文档用false。README.md/AGENTS.md不区分大小写自动豁免。不根据其它文件名猜用途。
- `ContentStore.create(path, raw, article=True)`：普通文章须符合六字段、标题正文H1一致、非空摘要、有效+08:00秒级字符串日期、初始date=updated、标签非空不重复字符串、sticky布尔、无旧字段。说明文档沿用原文创建。
- 不以服务端首次保存时间冒充开始写作时间：前端进入新建写作状态时记录真实北京时间生成模板；后端验证提交的date，保留作者/导入的真实值，不补猜历史日期。
- `contentApi.create(path, raw, article=true)`。`DocumentSession` 新建/另存可显式传用途；另存是复制，默认 `article=false`，保留原date/updated，不伪装为全新开始写作。普通新建须明确使用true。
- 新建默认六字段空title/description，用户填写；模板本身不造成误报未保存。编辑器可由文件名在空标题时回填去编号标题，但不得覆盖作者已填写内容。模板生成不放示例标签，不写示例时间。
- 已有完整六字段文章，实际修改正文或元信息时后端设置updated为真实北京时间（不早于date），保留磁盘date；无变化不写盘。历史文档不批量补日期，README/AGENTS不自动维护。
- 已有标准文章被删必填字段时拒绝保存；单行updated精确替换，保留其余注释、字段、BOM及换行。前端保存期间的新输入继续保留，并同步服务端更新的updated行，避免下一次误提交过期元信息。
- 用途选择对脏缓冲不得静默重置。普通文章切为说明文档不要求删现有头部；已有说明文档保持可编辑。

## Tasks

1. [x] 后端：新增聚焦的 `article_frontmatter.py`、测试；更新 content_store/app；先失败后实现。测试固定顺序/引号/类型/标签/正文标题/日期/豁免/历史文档/无变化/冲突/只改updated及保留date。
2. [x] 前端：新增 `articleTemplate.ts` 与测试；更新Editor、documentSession、content API及测试runner。测试北京时间、转义、空字段验证、新建用途、模板不误dirty、另存保留日期、保存中输入与服务端updated合并。
3. [x] 集成：更新相关README/AGENTS/接口与验证文档，跑全后端/桌面/前台测试及桌面build；以临时内容根实际验证新建普通文章、豁免说明、冲突和更新时间。
4. [x] 独立只读审阅，修复重要问题并复核。保留其它工作区改动，不提交。

后端与前端任务仅共享上述接口，文件不重叠，可分配独立工作者。主执行者负责契约、集成和验收。测试只写临时目录，不修改真实笔记。

## 审阅后的明确取舍

- PUT 新增可选 article：省略自动识别，true 明确文章，false 明确说明原文保存。已有文档可选择本次编辑用途；新建说明后当前会话保持说明用途，重开回到自动识别。不额外持久化文档用途，避免建立第二份内容注册表；作者可以再次明确用途。
- 作者明确按文章补齐历史字段时允许其提供真实 date，服务端不猜测已有历史时间；原有效 date 保持保护。
- updated 的 YAML 共享引用必须拒绝以避免间接改 date 或未知字段；merge 无法定位时返回校验错误。作者当前已将其修成独立字段，应允许修复保存，而不是被旧快照结构阻挡。


## 完成与证据

- 后端54、桌面26、站点32项测试通过；桌面类型检查与生产构建通过。
- 真实页面验证自动模板、标题回填、缺摘要拒绝、新建成功、date保留与updated维护、README及说明豁免；HTTP验证无变化不写与过期版本409。
- 独立审阅发现的YAML共享节点/merge定位/旧结构修复/说明保存问题已加失败回归并修复，最终定向复审通过。
- 详见 admin-desktop/docs/六字段文章模板验证记录.md。仅写隔离样例，未提交Git。
