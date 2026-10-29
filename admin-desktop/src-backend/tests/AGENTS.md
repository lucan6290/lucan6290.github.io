# 内容后端测试

入口 `test_content.py`，使用 unittest、FastAPI TestClient 和 TemporaryDirectory。所有写入使用隔离内容根，不以真实笔记做破坏性测试。

项目根执行 `python -m unittest discover -s admin-desktop/src-backend/tests -v`。前台一致性用例只向临时目录生成内容清单，不写实际 generated。

覆盖接口契约、路径边界、原文往返、版本冲突、失败保留原文件、扫描一致性及开发会话稳定；回归记录见 README.md。
