"""
Task 3-5 测试：add_to_index / remove_from_index / update_in_index / handle_status_change
"""
import pytest
from app.services.index_updater import (
    add_to_index,
    handle_status_change,
    match_link_by_filename,
    parse_index,
    remove_from_index,
    serialize,
    update_in_index,
)


# ============================================================
# add_to_index 测试
# ============================================================

class TestAddToExistingSubcategory:
    """追加到已有二级分类"""

    def test_add_article(self, sample_index_md):
        new_text, msg = add_to_index(
            sample_index_md,
            title="新AI文章",
            date="2026-06-10 10:00:00",
            categories=["技术研习", "AI 探索"],
            filename="ts-ai-newarticle",
            category_slug="tech-study",
        )
        assert "已将" in msg
        assert match_link_by_filename(new_text, "ts-ai-newarticle") is not None
        # 解析验证
        s = parse_index(new_text)
        ai_sub = s.categories[0].subcategories[0]
        assert len(ai_sub.articles) == 3  # 原有2 + 新1


class TestAddCreatesNewSubcategory:
    """自动创建新二级分类"""

    def test_new_sub(self, sample_index_md):
        new_text, msg = add_to_index(
            sample_index_md,
            title="Docker踩坑",
            date="2026-06-10 10:00:00",
            categories=["踩坑复盘", "Docker"],
            filename="pr-docker-test",
            category_slug="pitfall-review",
        )
        assert "已将" in msg
        s = parse_index(new_text)
        pr_cat = s.categories[1]
        # 应该有2个二级分类：环境配置 + Docker
        assert len(pr_cat.subcategories) == 2
        assert pr_cat.subcategories[1].title == "Docker"
        assert pr_cat.subcategories[1].number == "2.2"


class TestAddCreatesNewPrimaryCategory:
    """自动创建新一级分类"""

    def test_new_primary(self, sample_index_md):
        new_text, msg = add_to_index(
            sample_index_md,
            title="新分类文章",
            date="2026-06-10 10:00:00",
            categories=["全新分类", "子分类"],
            filename="xx-test-article",
            category_slug="new-category",
        )
        assert "已将" in msg
        s = parse_index(new_text)
        assert len(s.categories) == 6
        assert s.categories[5].title == "全新分类"
        assert s.categories[5].number == "六"


class TestAddIdempotent:
    """重复添加静默跳过"""

    def test_duplicate_skip(self, sample_index_md):
        # 先添加
        new_text, msg1 = add_to_index(
            sample_index_md,
            title="测试文章",
            date="2026-06-10 10:00:00",
            categories=["技术研习", "AI 探索"],
            filename="ts-ai-duplicate",
            category_slug="tech-study",
        )
        assert "已将" in msg1
        # 再添加同文件名
        new_text2, msg2 = add_to_index(
            new_text,
            title="测试文章改标题",
            date="2026-06-10 10:00:00",
            categories=["技术研习", "AI 探索"],
            filename="ts-ai-duplicate",
            category_slug="tech-study",
        )
        assert "跳过" in msg2
        assert new_text == new_text2


class TestAddRemovesPlaceholder:
    """添加时清除占位符"""

    def test_placeholder_cleared(self, sample_index_md):
        new_text, msg = add_to_index(
            sample_index_md,
            title="实战项目",
            date="2026-06-10 10:00:00",
            categories=["项目实战", "Web开发"],
            filename="pp-web-test",
            category_slug="project-practice",
        )
        s = parse_index(new_text)
        # 项目实战原来有 placeholder，添加后应消失
        assert s.categories[2].placeholder is None
        assert len(s.categories[2].subcategories) == 1


class TestAddMissingCategories:
    """缺少 categories 字段时报错"""

    def test_empty_categories(self, sample_index_md):
        with pytest.raises(ValueError, match="categories"):
            add_to_index(
                sample_index_md,
                title="测试", date="2026-06-10",
                categories=[],
                filename="test", category_slug="ts",
            )

    def test_none_categories(self, sample_index_md):
        with pytest.raises(ValueError, match="categories"):
            add_to_index(
                sample_index_md,
                title="测试", date="2026-06-10",
                categories=None,
                filename="test", category_slug="ts",
            )


class TestAddMissingDate:
    """日期格式异常时报错"""

    def test_bad_date(self, sample_index_md):
        with pytest.raises(ValueError, match="日期格式异常"):
            add_to_index(
                sample_index_md,
                title="测试", date="bad",
                categories=["技术研习"],
                filename="test", category_slug="ts",
            )

    def test_empty_date(self, sample_index_md):
        with pytest.raises(ValueError, match="日期格式异常"):
            add_to_index(
                sample_index_md,
                title="测试", date="",
                categories=["技术研习"],
                filename="test", category_slug="ts",
            )


class TestAddSingleCategory:
    """只有一级分类时，用一级名作二级"""

    def test_single_category_as_sub(self, sample_index_md):
        new_text, msg = add_to_index(
            sample_index_md,
            title="实战文章",
            date="2026-06-10 10:00:00",
            categories=["项目实战"],
            filename="pp-test-single",
            category_slug="project-practice",
        )
        s = parse_index(new_text)
        assert s.categories[2].subcategories[0].title == "项目实战"


# ============================================================
# remove_from_index 测试
# ============================================================

class TestRemoveExistingArticle:
    """正常移除"""

    def test_remove(self, sample_index_md):
        new_text, msg = remove_from_index(sample_index_md, "ts-git-git使用笔记与经验总结")
        assert "移除" in msg
        assert match_link_by_filename(new_text, "ts-git-git使用笔记与经验总结") is None


class TestRemoveEmptySubcategoryRemoved:
    """二级分类清空时自动移除"""

    def test_sub_removed_when_empty(self, sample_index_md):
        # 踩坑复盘只有一个文章，移除后该二级分类应消失
        new_text, msg = remove_from_index(sample_index_md, "pr-vmware-共享目录配置")
        s = parse_index(new_text)
        # 踩坑复盘应该恢复占位符（因为唯一的二级分类被移除了）
        assert s.categories[1].placeholder == "*暂无文章，敬请期待*"


class TestRemoveRenumbersSubcategories:
    """移除后重新编号"""

    def test_renumber_after_remove(self, sample_index_md):
        # 先添加一个新二级分类到技术研习
        new_text, _ = add_to_index(
            sample_index_md,
            title="新笔记",
            date="2026-06-10 10:00:00",
            categories=["技术研习", "新分类"],
            filename="ts-new-test",
            category_slug="tech-study",
        )
        # 现在技术研习有 1.1, 1.2, 1.3
        s = parse_index(new_text)
        nums = [sub.number for sub in s.categories[0].subcategories]
        assert nums == ["1.1", "1.2", "1.3"]

        # 移除 1.2（入门笔记）
        new_text2, msg = remove_from_index(new_text, "ts-git-git使用笔记与经验总结")
        s2 = parse_index(new_text2)
        nums2 = [sub.number for sub in s2.categories[0].subcategories]
        assert nums2 == ["1.1", "1.2"]  # 1.3 变成了 1.2
        assert s2.categories[0].subcategories[1].title == "新分类"


class TestRemoveRestoresPlaceholder:
    """一级分类清空时恢复占位符"""

    def test_placeholder_restored(self, sample_index_md):
        # 成长随笔有文章，全部移除后应恢复占位符
        new_text, _ = remove_from_index(sample_index_md, "ge-blog-博客架构与长期发展规划")
        new_text2, _ = remove_from_index(new_text, "ge-hexo-博客搭建记录")
        new_text3, _ = remove_from_index(new_text2, "ge-ai-thinking-别再研究Prompt了")
        s = parse_index(new_text3)
        assert s.categories[3].placeholder == "*暂无文章，敬请期待*"


class TestRemoveNotFoundSilent:
    """不存在的文章静默跳过"""

    def test_not_found(self, sample_index_md):
        new_text, msg = remove_from_index(sample_index_md, "not-exist-filename")
        assert "未在目录中找到" in msg
        # 文本不变
        assert new_text == sample_index_md or serialize(parse_index(new_text)) == serialize(parse_index(sample_index_md))


class TestRemoveDuplicateFilenameError:
    """重复文件名时报错"""

    def test_duplicate_error(self, sample_index_md):
        # 人为制造重复链接
        modified = sample_index_md.replace(
            "ts-git-git使用笔记与经验总结",
            "ts-ai-agent入门笔记",  # 复制一个已存在的文件名
        )
        # 现在 ts-ai-agent入门笔记 出现两次
        with pytest.raises(ValueError, match="重复文件名"):
            remove_from_index(modified, "ts-ai-agent入门笔记")


# ============================================================
# update_in_index 测试
# ============================================================

class TestUpdateTitleOnly:
    """只改标题"""

    def test_update_title(self, sample_index_md):
        new_text, msg = update_in_index(
            sample_index_md,
            old_filename="ts-ai-agent入门笔记",
            new_title="Agent 入门笔记（修订版）",
            new_date="2026-05-20 00:00:00",
            new_categories=["技术研习", "AI 探索"],
            new_filename="ts-ai-agent入门笔记",
            new_category_slug="tech-study",
        )
        assert "更新" in msg
        assert "Agent 入门笔记（修订版）" in new_text


class TestUpdateDate:
    """改日期更新 URL"""

    def test_update_date(self, sample_index_md):
        new_text, msg = update_in_index(
            sample_index_md,
            old_filename="ts-git-git使用笔记与经验总结",
            new_title="Git 使用笔记与经验总结",
            new_date="2025-01-15 10:00:00",
            new_categories=["技术研习", "入门笔记"],
            new_filename="ts-git-git使用笔记与经验总结",
            new_category_slug="tech-study",
        )
        assert "/2025/01/15/" in new_text


class TestUpdateCategoryMove:
    """分类变更（remove + add）"""

    def test_move_category(self, sample_index_md):
        new_text, msg = update_in_index(
            sample_index_md,
            old_filename="ts-git-git使用笔记与经验总结",
            new_title="Git 使用笔记",
            new_date="2024-10-20 00:00:00",
            new_categories=["踩坑复盘", "Git"],
            new_filename="ts-git-git使用笔记与经验总结",
            new_category_slug="pitfall-review",
        )
        # 从技术研习移除，添加到踩坑复盘
        s = parse_index(new_text)
        # 技术研习只剩1个二级分类（入门笔记被移除因为文章清空了）
        assert len(s.categories[0].subcategories) == 1
        assert s.categories[0].subcategories[0].title == "AI 探索"
        # 踩坑复盘应该有新二级分类
        assert any("Git" in sub.title for sub in s.categories[1].subcategories)


class TestUpdateNoChange:
    """无变化时跳过"""

    def test_no_change(self, sample_index_md):
        new_text, msg = update_in_index(
            sample_index_md,
            old_filename="ts-ai-agent入门笔记",
            new_title="Agent 入门笔记",
            new_date="2026-05-20 00:00:00",
            new_categories=["技术研习", "AI 探索"],
            new_filename="ts-ai-agent入门笔记",
            new_category_slug="tech-study",
        )
        assert "无变化" in msg


# ============================================================
# handle_status_change 测试
# ============================================================

class TestStatusDraftToPublished:
    """插入"""

    def test_draft_to_published(self, sample_index_md):
        new_text, msg = handle_status_change(
            sample_index_md,
            title="新发布文章",
            date="2026-06-10 10:00:00",
            categories=["技术研习", "AI 探索"],
            filename="ts-ai-newpublished",
            category_slug="tech-study",
            old_status="draft",
            new_status="published",
        )
        assert "添加" in msg
        assert match_link_by_filename(new_text, "ts-ai-newpublished") is not None


class TestStatusPublishedToDraft:
    """移除"""

    def test_published_to_draft(self, sample_index_md):
        new_text, msg = handle_status_change(
            sample_index_md,
            title="Agent 入门笔记",
            date="2026/05/20",
            categories=["技术研习", "AI 探索"],
            filename="ts-ai-agent入门笔记",
            category_slug="tech-study",
            old_status="published",
            new_status="draft",
        )
        assert "移除" in msg
        assert match_link_by_filename(new_text, "ts-ai-agent入门笔记") is None


class TestStatusPublishedToWip:
    """移除"""

    def test_published_to_wip(self, sample_index_md):
        new_text, msg = handle_status_change(
            sample_index_md,
            title="Agent 入门笔记",
            date="2026/05/20",
            categories=["技术研习", "AI 探索"],
            filename="ts-ai-agent入门笔记",
            category_slug="tech-study",
            old_status="published",
            new_status="wip",
        )
        assert "移除" in msg


class TestStatusDraftToWip:
    """不处理"""

    def test_draft_to_wip(self, sample_index_md):
        new_text, msg = handle_status_change(
            sample_index_md,
            title="测试",
            date="2026-06-10",
            categories=["技术研习"],
            filename="ts-draft-test",
            category_slug="tech-study",
            old_status="draft",
            new_status="wip",
        )
        assert "无需更新" in msg
