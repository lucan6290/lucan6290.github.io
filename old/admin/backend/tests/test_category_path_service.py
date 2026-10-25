import pytest

from scr.core.exceptions import BadRequestError
from scr.services.content.categories.category_path_service import CategoryPathService


def test_category_path_service_normalizes_and_validates_segments() -> None:
    assert CategoryPathService.normalize_path([" docs ", "", "ai"]) == ["docs", "ai"]


def test_category_path_service_rejects_empty_path() -> None:
    with pytest.raises(BadRequestError) as exc_info:
        CategoryPathService.normalize_path([" ", ""])

    assert exc_info.value.code == "category_path_empty"


def test_category_path_service_rejects_unsafe_slug() -> None:
    with pytest.raises(BadRequestError) as exc_info:
        CategoryPathService.validate_slug("../ai")

    assert exc_info.value.code == "invalid_category_slug"
