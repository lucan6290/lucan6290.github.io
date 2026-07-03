"""API 依赖工厂。

集中管理端点层需要注入的服务实例，便于 FastAPI dependency_overrides
在测试或后续扩展中替换具体实现。
"""

from functools import lru_cache

from scr.application.content.workflows.article_workflow import ArticleWorkflowService
from scr.application.content.workflows.category_workflow import CategoryWorkflowService
from scr.infrastructure.registry.registry_index_service import RegistryIndexService
from scr.infrastructure.registry.registry_yaml_service import RegistryYamlService
from scr.infrastructure.registry.schema_service import SchemaService
from scr.infrastructure.registry.tag_service import TagService
from scr.services.content.articles.article_service import ArticleService
from scr.services.content.blog.blog_index_service import BlogIndexService
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.services.content.categories.category_service import CategoryService
from scr.services.content.docusaurus.docusaurus_config_management_service import DocusaurusConfigManagementService
from scr.services.content.sidebars.sidebar_management_service import SidebarManagementService
from scr.services.content.validation.validation_service import ValidationService
from scr.services.site.build_service import BuildService


@lru_cache(maxsize=1)
def get_article_service() -> ArticleService:
    return ArticleService()


@lru_cache(maxsize=1)
def get_article_workflow_service() -> ArticleWorkflowService:
    return ArticleWorkflowService()


@lru_cache(maxsize=1)
def get_category_service() -> CategoryService:
    return CategoryService()


@lru_cache(maxsize=1)
def get_category_workflow_service() -> CategoryWorkflowService:
    return CategoryWorkflowService(get_category_service())


@lru_cache(maxsize=1)
def get_sidebar_management_service() -> SidebarManagementService:
    return SidebarManagementService()


@lru_cache(maxsize=1)
def get_category_index_service() -> CategoryIndexService:
    return CategoryIndexService()


@lru_cache(maxsize=1)
def get_blog_index_service() -> BlogIndexService:
    return BlogIndexService()


@lru_cache(maxsize=1)
def get_registry_index_service() -> RegistryIndexService:
    return RegistryIndexService()


@lru_cache(maxsize=1)
def get_registry_yaml_service() -> RegistryYamlService:
    return RegistryYamlService()


@lru_cache(maxsize=1)
def get_docusaurus_config_management_service() -> DocusaurusConfigManagementService:
    return DocusaurusConfigManagementService()


@lru_cache(maxsize=1)
def get_schema_service() -> SchemaService:
    return SchemaService()


@lru_cache(maxsize=1)
def get_tag_service() -> TagService:
    return TagService()


@lru_cache(maxsize=1)
def get_validation_service() -> ValidationService:
    return ValidationService()


@lru_cache(maxsize=1)
def get_build_service() -> BuildService:
    return BuildService()
