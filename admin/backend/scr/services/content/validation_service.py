"""站点内容校验服务。"""

from scr.core.exceptions import AppError
from scr.models.article import ArticleType
from scr.schemas.validation import (
    ArticleValidationSummaryDTO,
    SiteValidationRequestDTO,
    SiteValidationResultDTO,
)
from scr.services.content.article_service import ArticleService
from scr.services.content.filesystem_service import FileSystemService


class ValidationService:
    """执行 docs/blog 全站内容校验。"""

    def __init__(self) -> None:
        self.article_service = ArticleService()
        self.filesystem = FileSystemService()

    def validate_site(self, payload: SiteValidationRequestDTO) -> SiteValidationResultDTO:
        """扫描文章并复用单篇校验规则生成汇总结果。"""
        try:
            requested_types = [payload.type] if payload.type else [ArticleType.docs, ArticleType.blog]
            articles: list[ArticleValidationSummaryDTO] = []
            checked_count = 0
            issue_count = 0
            error_count = 0
            warning_count = 0

            for article_type in requested_types:
                for path in self.filesystem.scan_article_files(article_type):
                    checked_count += 1
                    relative_path = self.filesystem.relative_posix_path(article_type, path)
                    article_id = self.article_service.encode_article_id(article_type, relative_path)
                    validation = self.article_service.validate_article(article_id)
                    issues = validation.issues
                    if not payload.include_warnings:
                        issues = [issue for issue in issues if issue.severity == "error"]

                    issue_count += len(issues)
                    error_count += sum(1 for issue in issues if issue.severity == "error")
                    warning_count += sum(1 for issue in issues if issue.severity == "warning")

                    if payload.only_with_issues and not issues:
                        continue

                    articles.append(
                        ArticleValidationSummaryDTO(
                            article_id=article_id,
                            type=article_type,
                            relative_path=relative_path,
                            issues=issues,
                        )
                    )

            return SiteValidationResultDTO(
                type=payload.type,
                checked_count=checked_count,
                article_count=len(articles),
                issue_count=issue_count,
                error_count=error_count,
                warning_count=warning_count,
                articles=articles,
            )
        except AppError:
            raise
        except OSError as exc:
            raise AppError("全站内容校验失败。", code="site_validation_failed") from exc
