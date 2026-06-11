"""
Task 2 测试：辅助函数
"""
import pytest
from app.services.index_updater import (
    IndexStructure,
    PrimaryCategory,
    Subcategory,
    chinese_to_number,
    count_links_by_filename,
    find_primary_category,
    find_subcategory,
    generate_link_line,
    get_next_chinese_number,
    get_next_sub_number,
    match_link_by_filename,
    number_to_chinese,
    parse_index,
    renumber_subcategories,
)


# ============================================================
# 中文序号映射
# ============================================================

class TestNumberToChinese:
    def test_1(self):
        assert number_to_chinese(1) == "一"

    def test_5(self):
        assert number_to_chinese(5) == "五"

    def test_15(self):
        assert number_to_chinese(15) == "十五"

    def test_out_of_range(self):
        assert number_to_chinese(20) == "20"


class TestChineseToNumber:
    def test_yi(self):
        assert chinese_to_number("一") == 1

    def test_wu(self):
        assert chinese_to_number("五") == 5

    def test_shi(self):
        assert chinese_to_number("十") == 10

    def test_unknown(self):
        assert chinese_to_number("foo") == 0


# ============================================================
# 链接生成
# ============================================================

class TestGenerateLinkLine:
    def test_normal_date(self):
        result = generate_link_line(
            "2026-06-08", "tech-study", "ts-ai-test", "测试文章"
        )
        assert result == "- [测试文章](/2026/06/08/tech-study/ts-ai-test/)"

    def test_date_with_time(self):
        result = generate_link_line(
            "2026-06-08 15:30:00", "tech-study", "ts-ai-test", "测试文章"
        )
        assert result == "- [测试文章](/2026/06/08/tech-study/ts-ai-test/)"

    def test_bad_date_raises(self):
        with pytest.raises(ValueError, match="日期格式异常"):
            generate_link_line("bad-date", "tech-study", "ts-ai-test", "测试文章")


# ============================================================
# 链接匹配
# ============================================================

class TestMatchLinkByFilename:
    def test_found(self):
        text = "- [Agent 入门笔记](/2026/05/20/tech-study/ts-ai-agent入门笔记/)"
        m = match_link_by_filename(text, "ts-ai-agent入门笔记")
        assert m is not None
        assert "Agent" in m.group(0)

    def test_not_found(self):
        text = "- [Agent 入门笔记](/2026/05/20/tech-study/ts-ai-agent入门笔记/)"
        assert match_link_by_filename(text, "not-exist") is None


class TestCountLinksByFilename:
    def test_single(self):
        text = "- [A](/2026/01/01/ts/ts-a/)\n- [B](/2026/01/02/ts/ts-b/)"
        assert count_links_by_filename(text, "ts-a") == 1

    def test_duplicate(self):
        text = "- [A](/2026/01/01/ts/ts-a/)\n- [A copy](/2026/01/02/ts/ts-a/)"
        assert count_links_by_filename(text, "ts-a") == 2

    def test_zero(self):
        text = "- [A](/2026/01/01/ts/ts-a/)"
        assert count_links_by_filename(text, "ts-b") == 0


# ============================================================
# 分类名匹配
# ============================================================

class TestFindPrimaryCategory:
    def test_exact_match(self, sample_index_md):
        structure = parse_index(sample_index_md)
        cat = find_primary_category(structure, "技术研习")
        assert cat is not None
        assert cat.number == "一"

    def test_partial_match(self, sample_index_md):
        structure = parse_index(sample_index_md)
        cat = find_primary_category(structure, "技术")
        assert cat is not None
        assert cat.title == "技术研习"

    def test_not_found(self, sample_index_md):
        structure = parse_index(sample_index_md)
        assert find_primary_category(structure, "不存在") is None


class TestFindSubcategory:
    def test_found(self, sample_index_md):
        structure = parse_index(sample_index_md)
        primary = find_primary_category(structure, "技术研习")
        sub = find_subcategory(primary, "AI 探索")
        assert sub is not None
        assert sub.number == "1.1"

    def test_not_found(self, sample_index_md):
        structure = parse_index(sample_index_md)
        primary = find_primary_category(structure, "技术研习")
        assert find_subcategory(primary, "不存在") is None


# ============================================================
# 编号工具
# ============================================================

class TestGetNextChineseNumber:
    def test_next_after_5(self, sample_index_md):
        structure = parse_index(sample_index_md)
        assert get_next_chinese_number(structure) == "六"


class TestGetNextSubNumber:
    def test_next_after_2(self, sample_index_md):
        structure = parse_index(sample_index_md)
        primary = find_primary_category(structure, "技术研习")
        # 技术研习有 1.1 和 1.2，下一个应该是 1.3
        assert get_next_sub_number(primary) == "1.3"

    def test_empty_primary(self):
        primary = PrimaryCategory(number="三", title="测试", heading="## 三、测试")
        assert get_next_sub_number(primary) == "3.1"


class TestRenumberSubcategories:
    def test_fill_gaps(self):
        primary = PrimaryCategory(number="一", title="测试", heading="## 一、测试")
        primary.subcategories = [
            Subcategory(number="1.1", title="A", heading="### 1.1 A"),
            Subcategory(number="1.3", title="B", heading="### 1.3 B"),
            Subcategory(number="1.5", title="C", heading="### 1.5 C"),
        ]
        renumber_subcategories(primary)
        numbers = [s.number for s in primary.subcategories]
        assert numbers == ["1.1", "1.2", "1.3"]
        # heading 也应该更新
        assert primary.subcategories[1].heading == "### 1.2 B"

    def test_already_sequential(self):
        primary = PrimaryCategory(number="二", title="测试", heading="## 二、测试")
        primary.subcategories = [
            Subcategory(number="2.1", title="A", heading="### 2.1 A"),
            Subcategory(number="2.2", title="B", heading="### 2.2 B"),
        ]
        renumber_subcategories(primary)
        numbers = [s.number for s in primary.subcategories]
        assert numbers == ["2.1", "2.2"]
