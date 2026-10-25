这套方案采用的是 Claude Code / Claude 类 Agent 在“代码编辑、工具调用、权限控制”上的一些公开可观察思路，再按博客后台场景重新收敛成三个垂直 Agent。

主要借鉴点可以这样理解。

**1. Tool-first，而不是让模型直接操作文件**

Claude Code 的核心体验之一是：模型不直接“神秘地改文件”，而是通过受控工具读文件、改文件、看 diff、跑测试。

对应到博客 Agent：

- `read_current_article`
- `preview_current_article_edit`
- `write_current_article`
- `create_post`
- `write_created_post`
- `scan_article_index`
- `search_article_chunks`

模型负责“想”，工具负责“做”。

---

**2. 先读上下文，再计划，再执行**

Claude Code 通常会先看相关文件，再形成修改方案，然后执行。

对应到这里：

```text
读取当前文章 / 分类 / 规则 / 已有文章
-> 生成结构化计划
-> preview diff
-> 用户确认或自动执行
-> 写入
-> 返回结果
```

所以我没有设计成“一句话直接写文章”，而是拆成可审计步骤。

---

**3. Diff 预览优先**

Claude Code 修改代码前后很强调 diff、patch、变更说明。

对应到编辑器 Agent：

- 先 `preview_current_article_edit`
- 返回 `diff`
- 展示 `riskFlags`
- 展示 `errors`
- 再决定是否 `write_current_article`

这能避免 AI 直接覆盖文章。

---

**4. 权限模式 / Approval 模型**

Claude Code 有“需要确认的操作”和“可自动执行的操作”这种交互思路。

对应到这里设计成三档：

- `request-approval`：所有写入都要确认。
- `delegate-approval`：低风险自动，高风险确认。
- `full-access`：允许自动执行，但仍做安全校验。

这不是无限权限，而是“可自动走工具，但不能绕过边界”。

---

**5. 受控工具作用域**

Claude Code 的好 Agent 不应该能任意操作整个系统，而是按任务限定范围。

对应到博客 Agent：

- 编辑器 Agent 只能操作当前文章。
- 写作 Agent 只能写自己创建的草稿。
- 知识库 Agent 只读不写。
- 网页工具只能抓用户显式提供的 URL。
- 禁止 git、deploy、任意 shell、任意文件删除。

---

**6. Session / Resume 思路**

Claude Code 类工具通常有连续任务上下文，不是每次请求都从零开始。

对应到这里：

- `sessionId`
- 绑定当前文章
- 保存当前选区
- 保存 pending approval payload
- 用户确认后 resume
- 防止审批时 payload 被偷偷换掉，用 `payloadHash`

这个特别像 Agent 执行链里的“暂停-确认-恢复”。

---

**7. Event 流程可观测**

Claude Code 执行时会展示它正在做什么，比如读取文件、运行命令、修改文件。

对应到这里统一事件：

```text
session
tool_call
tool_result
approval_required
done
error
```

前端可以展示 Agent 每一步，不是只给最终答案。

---

**8. WebFetch 的安全收敛**

Claude Code 有 WebFetch / WebSearch 这类工具，但不会等同于任意浏览器控制。

对应到这里：

- 只做 `fetch_url`
- 不做通用浏览器 Agent
- 不做任意搜索代理
- SSRF 防护
- 限制跳转、大小、超时
- 不带 cookie / 登录态

这也是典型“工具能力要窄”的 Agent 设计。

---

**9. Evidence-based QA**

Claude 类知识库问答强调基于上下文和引用回答。

对应到知识库 Agent：

- 先检索文章 chunks
- 有 evidence 才回答
- 必须带 citations
- 没证据明确说不知道
- 不允许知识库 Agent 写文章

---

**10. 保守执行，不自动发布**

Claude Code 常见边界是：可以帮你改、测、解释，但高风险操作要显式授权。

对应到博客：

- 不自动 git commit
- 不自动 push
- 不自动 deploy
- 不自动发布文章
- 不自动改主题源码
- 不自动新增分类结构

---

一句话总结：

这套 Agent 采用的是 Claude Code 式的 **“读上下文 -> 工具化计划 -> diff 预览 -> 权限审批 -> 受控写入 -> 可观测事件 -> 可恢复会话”** 思路，但没有采用 Claude 内部源码，也没有做通用万能 Agent，而是把这些能力压缩到博客后台最需要的三个 Agent：编辑器、新文章、知识库。