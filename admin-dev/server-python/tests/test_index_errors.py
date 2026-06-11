"""
Task 7 测试：错误处理 + 边界情况
"""
import pytest
from app.services.index_updater import (
    IndexStructure,
    PrimaryCategory,
    add_to_index,
    parse_index,
    remove_from_index,
    serialize,
    update_in_index,
)


# ============================================================
# 文件级错误
# ============================================================

class TestIndexFileErrors:
    """5.1 文件级错误"""

    def test_index_not_exists(self):
        """index.md 不存在 → 路由层处理，引擎层只处理文本"""
        # 引擎层不涉及文件 I/O，这里测试空/无效输入
        with pytest.raises(ValueError, match="内容为空"):
            parse_index("")

    def test_index_empty_body(self):
        """body 为空但有 front matter"""
        text = "---\ntitle: test\n---\n"
        s = parse_index(text)
        assert len(s.categories) == 0

    def test_no_primary_categories(self):
        """无一级分类时正常解析，但操作函数不应崩溃"""
        text = "---\ntitle: test\n---\n\n## 不是分类标题\n\n一些内容\n"
        s = parse_index(text)
        assert len(s.categories) == 0


# ============================================================
# 特殊字符
# ============================================================

class TestSpecialCharsInTitle:
    """6.1 标题/文件名中的特殊字符"""

    def test_brackets_in_title(self):
        """标题含方括号"""
        text = "---\ntitle: test\n---\n\n## 一、测试\n\n### 1.1 子测试\n\n- [Vue3 [笔记]](/2026/01/01/ts/ts-vue3note/)\n"
        s = parse_index(text)
        assert len(s.categories[0].subcategories[0].articles) == 1
        assert "[笔记]" in s.categories[0].subcategories[0].articles[0].line

    def test_chinese_brackets_in_title(self):
        """标题含全角括号"""
        text = "---\ntitle: test\n---\n\n## 一、测试\n\n### 1.1 子测试\n\n- [AI编程工具的真实体验：强但没那么神](/2026/01/01/ts/ts-test/)\n"
        s = parse_index(text)
        assert len(s.categories[0].subcategories[0].articles) == 1

    def test_special_chars_add_and_find(self, sample_index_md):
        """含特殊字符的文件名能正确添加和匹配"""
        new_text, msg = add_to_index(
            sample_index_md,
            title="测试[笔记]",
            date="2026-06-10 10:00:00",
            categories=["技术研习", "AI 探索"],
            filename="ts-ai-test[notes]",
            category_slug="tech-study",
        )
        assert "已将" in msg
        # 能正确移除
        new_text2, msg2 = remove_from_index(new_text, "ts-ai-test[notes]")
        assert "移除" in msg2


# ============================================================
# 编号边界
# ============================================================

class TestManyPrimaryCategories:
    """5.5 编号边界 - 超过 10 个一级分类"""

    def test_many_categories(self, sample_index_md):
        """连续创建多个新一级分类"""
        text = sample_index_md
        for i in range(6, 12):
            text, msg = add_to_index(
                text,
                title=f"分类{i}文章",
                date="2026-06-10 10:00:00",
                categories=[f"分类{i}", f"子{i}"],
                filename=f"cat{i}-test",
                category_slug=f"cat{i}",
            )
            assert "已将" in msg

        s = parse_index(text)
        assert len(s.categories) == 11  # 原有5 + 新增6
        # 第6个应该是 "六"，第11个应该是 "11"（超出映射表）
        assert s.categories[5].number == "六"
        assert s.categories[10].number == "十一"


class TestHighSubNumber:
    """二级分类编号 ≥ 10"""

    def test_sub_number_10_plus(self, sample_index_md):
        """创建超过 10 个二级分类"""
        text = sample_index_md
        # 技术研习已有 1.1, 1.2 → 从 1.3 开始
        for i in range(3, 12):
            text, msg = add_to_index(
                text,
                title=f"文章{i}",
                date="2026-06-10 10:00:00",
                categories=["技术研习", f"子分类{i}"],
                filename=f"ts-sub{i}-test",
                category_slug="tech-study",
            )
            assert "已将" in msg

        s = parse_index(text)
        sub_nums = [sub.number for sub in s.categories[0].subcategories]
        assert "1.10" in sub_nums
        assert "1.11" in sub_nums


# ============================================================
# 系列文章保留
# ============================================================

class TestSeriesArticlesPreserved:
    """#### 系列文章原样保留"""

    def test_series_preserved_after_add(self, sample_index_md):
        """添加文章时系列文章块不受影响"""
        # sample_index_md 不含系列文章，用含系列的文本
        series_text = """\
---
title: test
---

## 一、测试

### 1.1 子测试

- [文章A](/2026/01/01/ts/ts-a/)

#### 系列文章（3篇）

- [系列1](/2026/01/01/ts/ts-s1/)
- [系列2](/2026/01/02/ts/ts-s2/)
- [系列3](/2026/01/03/ts/ts-s3/)

### 1.2 另一个子分类

- [文章B](/2026/01/01/ts/ts-b/)

---

*持续更新，记录成长*
"""
        # 添加到 1.1
        new_text, msg = add_to_index(
            series_text,
            title="新文章",
            date="2026-06-10",
            categories=["测试", "子测试"],
            filename="ts-new-series",
            category_slug="ts",
        )
        assert "已将" in msg
        # 系列文章应保留
        assert "系列文章（3篇）" in new_text
        assert "系列1" in new_text

    def test_series_preserved_after_remove(self):
        """移除文章时系列文章块不受影响（子分类内仍保留其他文章）"""
        series_text = """\n---
title: test
---

## 一、测试

### 1.1 子测试

- [文章A](/2026/01/01/ts/ts-a/)
- [文章B](/2026/01/02/ts/ts-b/)

#### 系列文章（3篇）

- [系列1](/2026/01/01/ts/ts-s1/)
- [系列2](/2026/01/02/ts/ts-s2/)

---

*持续更新，记录成长*
"""
        new_text, msg = remove_from_index(series_text, "ts-a")
        assert "移除" in msg
        assert "系列文章" in new_text
class TestFirstUse:
    """6.3 首次使用"""

    def test_add_to_empty_category(self, sample_index_md):
        """第一个添加到空分类（有 placeholder）"""
        new_text, msg = add_to_index(
            sample_index_md,
            title="首个分享",
            date="2026-06-10 10:00:00",
            categories=["资源分享", "工具推荐"],
            filename="rs-tool-first",
            category_slug="resource-sharing",
        )
        s = parse_index(new_text)
        assert s.categories[4].placeholder is None
        assert len(s.categories[4].subcategories) == 1
        assert s.categories[4].subcategories[0].articles[0].line == (
            "- [首个分享](/2026/06/10/resource-sharing/rs-tool-first/)"
        )


# ============================================================
# 数据一致性
# ============================================================

class TestDataConsistency:
    """6.5 数据一致性"""

    def test_roundtrip_preserves_structure(self, sample_index_md):
        """多次增删操作后结构仍然有效"""
        text = sample_index_md
        # 添加
        text, _ = add_to_index(text, "T1", "2026-06-01", ["技术研习", "AI 探索"], "ts-t1", "tech-study")
        text, _ = add_to_index(text, "T2", "2026-06-02", ["踩坑复盘", "Docker"], "pr-t2", "pitfall-review")
        text, _ = add_to_index(text, "T3", "2026-06-03", ["项目实战", "Web"], "pp-t3", "project-practice")

        # 移除
        text, _ = remove_from_index(text, "ts-t1")
        text, _ = remove_from_index(text, "pr-t2")

        # 最终结构应合法
        s = parse_index(text)
        assert len(s.categories) == 5
        # 技术研习应有 AI 探索（原有2篇）+ 入门笔记（1篇）
        assert len(s.categories[0].subcategories) == 2

    def test_idempotent_after_many_ops(self, sample_index_md):
        """多次操作后 roundtrip 仍然幂等"""
        text, _ = add_to_index(sample_index_md, "T1", "2026-06-01", ["技术研习", "AI 探索"], "ts-t1", "tech-study")
        text1 = serialize(parse_index(text))
        text2 = serialize(parse_index(text1))
        assert text1 == text2
