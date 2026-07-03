"""Blog navigation operations."""

from scr.services.content.docusaurus.docusaurus_config_service import DocusaurusConfigService


class BlogNavService:
    """Maintain blog entries in the Docusaurus top navigation."""

    def __init__(self) -> None:
        self.docusaurus_config = DocusaurusConfigService()

    def upsert_top_category(self, slug: str, label: str) -> None:
        self.docusaurus_config.upsert_blog_nav_item(slug, label)
