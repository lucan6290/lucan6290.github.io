# 桌面前端

入口 `App.vue` 验证本机服务及会话后挂载路由。API 为 `api/content.ts`、类型为 `types/content.ts`；旧 `api/index.ts` 和旧页面暂未删除，不在当前路由执行链路。

- `views/Posts.vue`：实际目录、动态栏目、README、显式新建目录和版本化删除。
- `views/Editor.vue`：原始 Markdown 与导航/关闭保护；`utils/documentSession.ts` 为可测试会话状态。
- `utils/contentOrder.ts`：与前台使用相同数字前缀和本机名称排序。
- 不从旧 `frontmatter.ts` 拆解再重建文档。保留未知元数据、注释、BOM 与换行。
- 新普通文章由 `utils/articleTemplate.ts` 生成六字段，开始写作时记录北京时间；说明文档与 README/AGENTS 豁免。普通保存和复制另存明确传递 article 用途，服务端 updated 响应不得覆盖请求期间输入。
- 轮询不可推进脏文档基线；保存成功也不得吞掉请求期间新输入。
- `Settings.vue` 保留主题和当前内容根；媒体、AI 页面通过 `Unavailable.vue` 明确标识待适配。

测试 `npm test`（Node 内置 runner，scripts/test.mjs 内存转译到临时目录）；构建 `npm run build`。
