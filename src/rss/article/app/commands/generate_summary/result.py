"""Result para GenerateArticleSummary command."""

from dataclasses import dataclass
from typing import Optional

from src.rss.article.domain.value_objects import ArticleId


@dataclass(frozen=True)
class GenerateArticleSummaryResult:
    """Result inmutable para operación de generación de resúmenes."""

    success: bool
    article_id: ArticleId
    summary: str
    was_updated: bool
    error_message: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        article_id: ArticleId,
        summary: str,
        was_updated: bool = True,
    ) -> "GenerateArticleSummaryResult":
        """Crea resultado exitoso."""
        return cls(
            success=True,
            article_id=article_id,
            summary=summary,
            was_updated=was_updated,
            error_message=None,
        )

    @classmethod
    def failure_result(
        cls,
        article_id: ArticleId,
        error_message: str,
    ) -> "GenerateArticleSummaryResult":
        """Crea resultado de error."""
        return cls(
            success=False,
            article_id=article_id,
            summary="",
            was_updated=False,
            error_message=error_message,
        )
