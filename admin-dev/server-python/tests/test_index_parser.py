"""
Task 1 测试：数据结构 + 解析器 + 序列化器
"""
import pytest
from app.services.index_updater import (
    Article,
    IndexStructure,
    PrimaryCategory,
    Subcategory,
    parse_index,
    serialize,
)


# ============================================================
# 解析测试
# ============================================================

class TestParseBasicStructure:
    """test_parse_basic_structure — 解析后结构正确（分类数量、标题、文章数）"""

    def test_category_count(self, sample_index_md):
        structure = parse_index(sample_index_md)
        assert len(structure.categories) == 5

    def test_primary_titles(self, sample_index_md):
        structure = parse_index(sample_index_md)
        titles = [c.title for c in structure.categories]
        assert titles == ["技术研习", "踩坑复盘", "项目实战", "成长随笔", "资源分享"]

    def test_primary_numbers(self, sample_index_md):
        structure = parse_index(sample_index_md)
        numbers = [c.number for c in structure.categories]
        assert numbers == ["一", "二", "三", "四", "五"]

    def test_subcategory_counts(self, sample_index_md):
        structure = parse_index(sample_index_md)
        counts = [len(c.subcategories) for c in structure.categories]
        assert counts == [2, 1, 0, 2, 0]

    def test_article_counts(self, sample_index_md):
        structure = parse_index(sample_index_md)
        # 技术研习 > AI 探索: 2 篇
        assert len(structure.categories[0].subcategories[0].articles) == 2
        # 技术研习 > 入门笔记: 1 篇
        assert len(structure.categories[0].subcategories[1].articles) == 1
        # 踩坑复盘 > 环境配置: 1 篇
        assert len(structure.categories[1].subcategories[0].articles) == 1
        # 成长随笔 > 博客建设: 2 篇
        assert len(structure.categories[3].subcategories[0].articles) == 2
        # 成长随笔 > AI 思考: 1 篇
        assert len(structure.categories[3].subcategories[1].articles) == 1

    def test_subcategory_numbers(self, sample_index_md):
        structure = parse_index(sample_index_md)
        sub_nums = [s.number for s in structure.categories[0].subcategories]
        assert sub_nums == ["1.1", "1.2"]

    def test_subcategory_titles(self, sample_index_md):
        structure = parse_index(sample_index_md)
        sub_titles = [s.title for s in structure.categories[0].subcategories]
        assert sub_titles == ["AI 探索", "入门笔记"]


class TestParsePlaceholder:
    """test_parse_placeholder — 空分类正确解析为 placeholder"""

    def test_placeholder_set_for_empty_category(self, sample_index_md):
        structure = parse_index(sample_index_md)
        # 项目实战 和 资源分享 有 placeholder
        assert structure.categories[2].placeholder == "*暂无文章，敬请期待*"
        assert structure.categories[4].placeholder == "*暂无文章，敬请期待*"

    def test_no_placeholder_for_filled_category(self, sample_index_md):
        structure = parse_index(sample_index_md)
        # 技术研习 有文章，无 placeholder
        assert structure.categories[0].placeholder is None
        assert structure.categories[1].placeholder is None


class TestParsePreservesUnknownLines:
    """test_parse_preserves_unknown_lines — 无法识别的行被保留"""

    def test_description_line_preserved(self, sample_index_md):
        structure = parse_index(sample_index_md)
        unknown_text = "\n".join(structure.unknown_lines)
        assert "箓川码笺文章总目录" in unknown_text

    def test_footer_preserved(self, sample_index_md):
        structure = parse_index(sample_index_md)
        assert "持续更新" in structure.footer


class TestPreservesFrontMatter:
    """test_preserves_front_matter — front matter 原样保留"""

    def test_front_matter_content(self, sample_index_md):
        structure = parse_index(sample_index_md)
        assert structure.front_matter.startswith("---")
        assert "title: 博客文章目录" in structure.front_matter
        assert "slug: blog-index" in structure.front_matter

    def test_front_matter_ends_with_separator(self, sample_index_md):
        structure = parse_index(sample_index_md)
        assert structure.front_matter.rstrip().endswith("---")


class TestRoundtrip:
    """test_roundtrip — parse → serialize → parse，两次解析结果一致"""

    def test_roundtrip_structure(self, sample_index_md):
        structure1 = parse_index(sample_index_md)
        text = serialize(structure1)
        structure2 = parse_index(text)

        assert len(structure1.categories) == len(structure2.categories)
        for c1, c2 in zip(structure1.categories, structure2.categories):
            assert c1.title == c2.title
            assert c1.number == c2.number
            assert len(c1.subcategories) == len(c2.subcategories)
            for s1, s2 in zip(c1.subcategories, c2.subcategories):
                assert s1.title == s2.title
                assert len(s1.articles) == len(s2.articles)

    def test_roundtrip_idempotent(self, sample_index_md):
        """serialize(parse(text)) 再 parse 再 serialize 应该得到相同文本"""
        text1 = serialize(parse_index(sample_index_md))
        text2 = serialize(parse_index(text1))
        assert text1 == text2


# ============================================================
# 边界测试
# ============================================================

class TestParseEmptyInput:
    """空内容报错"""

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="内容为空"):
            parse_index("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="内容为空"):
            parse_index("   \n\n  ")

    def test_no_front_matter_raises(self):
        with pytest.raises(ValueError, match="Front Matter"):
            parse_index("## 一、测试\n")

    def test_unclosed_front_matter_raises(self):
        with pytest.raises(ValueError, match="Front Matter"):
            parse_index("---\ntitle: test\n")
