from scr.infrastructure.filesystem.markdown_service import MarkdownService


def test_compose_writes_iso_date_strings_as_yaml_timestamps() -> None:
    content = MarkdownService().compose(
        {
            "title": "测试博客",
            "date": "2026-07-08T15:46:39+08:00",
            "last_update": {
                "date": "2026-07-08T15:48:21+08:00",
                "author": "lucan",
            },
        },
        "正文",
    )

    assert "date: 2026-07-08T15:46:39+08:00\n" in content
    assert "  date: 2026-07-08T15:48:21+08:00\n" in content
    assert "date: '2026-07-08T15:46:39+08:00'\n" not in content
