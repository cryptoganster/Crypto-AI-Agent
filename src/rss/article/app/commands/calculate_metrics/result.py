"""Result para CalculateArticleMetrics command."""

from dataclasses import dataclass
from typing import Optional

from src.rss.article.domain.value_objects import ArticleId


@dataclass(frozen=True)
class CalculateArticleMetricsResult:
    """
    Result inmutable para operación de cálculo de métricas.

    Contiene métricas calculadas y estado de la operación.
    """

    success: bool
    """Indica si el cálculo fue exitoso."""

    article_id: ArticleId
    """ID del artículo procesado."""

    word_count: int
    """Número de palabras calculado."""

    reading_time_minutes: int
    """Tiempo de lectura estimado en minutos."""

    was_updated: bool
    """Indica si el artículo fue actualizado en el repositorio."""

    error_message: Optional[str] = None
    """Mensaje de error si success=False."""

    # Factory methods

    @classmethod
    def success_result(
        cls,
        article_id: ArticleId,
        word_count: int,
        reading_time_minutes: int,
        was_updated: bool = True,
    ) -> "CalculateArticleMetricsResult":
        """Crea resultado exitoso."""
        return cls(
            success=True,
            article_id=article_id,
            word_count=word_count,
            reading_time_minutes=reading_time_minutes,
            was_updated=was_updated,
            error_message=None,
        )

    @classmethod
    def failure_result(
        cls,
        article_id: ArticleId,
        error_message: str,
    ) -> "CalculateArticleMetricsResult":
        """Crea resultado de error."""
        return cls(
            success=False,
            article_id=article_id,
            word_count=0,
            reading_time_minutes=0,
            was_updated=False,
            error_message=error_message,
        )
