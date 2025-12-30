"""DTOs para CalculateArticleMetrics command."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CalculateArticleMetricsRequestDto:
    """
    DTO de request para presentation layer.

    Usado por UI/API para solicitar cálculo de métricas.
    """

    article_id: str
    force_recalculate: bool = False
    update_article: bool = True


@dataclass(frozen=True)
class CalculateArticleMetricsResponseDto:
    """
    DTO de response para presentation layer.

    Retornado a UI/API con resultado del cálculo.
    """

    success: bool
    article_id: str
    word_count: int
    reading_time_minutes: int
    was_updated: bool
    error_message: Optional[str] = None

    @classmethod
    def from_result(cls, result) -> "CalculateArticleMetricsResponseDto":
        """Crea DTO desde Result del handler."""
        return cls(
            success=result.success,
            article_id=str(result.article_id),
            word_count=result.word_count,
            reading_time_minutes=result.reading_time_minutes,
            was_updated=result.was_updated,
            error_message=result.error_message,
        )
