# 独立桌面内容后端

- 契约：`../docs/内容接口契约.md`；仅以项目 `frontend/content/` 的原始 Markdown 为事实源。
- `content_store.py` 集中处理路径、YAML、扫描、版本与原子写入；`app.py` 仅提供 HTTP/认证适配。
- 不导入 `old/`、旧管理工作流或生成内容清单。新普通文章按 `docs/SITE_CONTENT_GUIDE.md` 校验六字段；已有完整六字段文章真实修改时仅维护 updated，不猜补历史 date，不添加旧站作者等字段。
- 独立联调用 `python main.py --project-root <根目录> --port 18000 --reload`。桌面通过 `--fallback-port` 允许端口回退，通过 `--session-file` 传入独立会话路径。会话 token 不得打印或提交。
- 回归：项目根执行 `python -m unittest discover -s admin-desktop/src-backend/tests -v`；写入测试只能使用临时目录。
- 扫描规则以 `frontend/scripts/lib/buildContent.mjs` 为准；不要为了桌面修改前台行为。
