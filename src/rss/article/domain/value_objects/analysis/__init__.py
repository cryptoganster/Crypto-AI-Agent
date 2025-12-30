"""
Article Analysis Value Objects.

Este módulo contiene los Value Objects para análisis de artículos
y el ArticleAnalysis compuesto que los agrupa.
"""

from dataclasses import dataclass
from typing import Optional

from .duplicate import (  # ArticleDuplicate es alias
    ArticleDuplicate,
    RssArticleDuplicate,
)
from .error import ArticleError, RssArticleError  # ArticleError es alias
from .keyword_config import KeywordExtractionConfig
from .keyword_score import KeywordScore
from .keywords import KeywordCollection
from .metrics import ArticleMetrics, RssArticleMetrics  # ArticleMetrics es alias
from .quality import ArticleQuality, RssArticleQuality  # ArticleQuality es alias
from .reading_time import ReadingTime
from .word_count import WordCount

__all__ = [
    "RssArticleDuplicate",
    "ArticleDuplicate",  # Alias para compatibilidad
    "RssArticleError",
    "ArticleError",  # Alias para compatibilidad
    "RssArticleMetrics",
    "ArticleMetrics",  # Alias para compatibilidad
    "RssArticleQuality",
    "ArticleQuality",  # Alias para compatibilidad
    "ReadingTime",
    "WordCount",
    "KeywordCollection",
    "KeywordScore",
    "KeywordExtractionConfig",
    "ArticleAnalysis",
]


@dataclass(frozen=True)
class ArticleAnalysis:
    """
    Value Object compuesto que agrupa análisis del artículo.

    Compone los Value Objects de análisis (métricas y duplicación) en una estructura cohesiva.

    Attributes:
        metrics: Métricas calculadas del contenido (word count, reading time)
        duplicate: Información de duplicación del artículo
    """

    metrics: RssArticleMetrics
    duplicate: RssArticleDuplicate

    @staticmethod
    def empty() -> "ArticleAnalysis":
        """
        Crea instancia vacía sin análisis.

        Returns:
            ArticleAnalysis con métricas vacías y sin duplicación

        Example:
            >>> analysis = ArticleAnalysis.empty()
            >>> analysis.metrics.has_metrics
            False
            >>> analysis.duplicate.is_duplicate
            False
        """
        return ArticleAnalysis(
            metrics=RssArticleMetrics.empty(),
            duplicate=RssArticleDuplicate.not_duplicate(),
        )

    @staticmethod
    def create(
        metrics: Optional[RssArticleMetrics] = None,
        duplicate: Optional[RssArticleDuplicate] = None,
    ) -> "ArticleAnalysis":
        """
        Factory method para crear ArticleAnalysis.

        Args:
            metrics: RssArticleMetrics opcional (usa empty si None)
            duplicate: RssArticleDuplicate opcional (usa not_duplicate si None)

        Returns:
            Nueva instancia de ArticleAnalysis
        """
        return ArticleAnalysis(
            metrics=metrics or RssArticleMetrics.empty(),
            duplicate=duplicate or RssArticleDuplicate.not_duplicate(),
        )

    def with_metrics(self, metrics: RssArticleMetrics) -> "ArticleAnalysis":
        """
        Retorna nueva instancia con metrics actualizado.

        Args:
            metrics: Nuevas métricas

        Returns:
            Nueva instancia de ArticleAnalysis con metrics actualizado
        """
        return ArticleAnalysis(metrics=metrics, duplicate=self.duplicate)

    def with_duplicate(self, duplicate: RssArticleDuplicate) -> "ArticleAnalysis":
        """
        Retorna nueva instancia con duplicate actualizado.

        Args:
            duplicate: Nueva información de duplicación

        Returns:
            Nueva instancia de ArticleAnalysis con duplicate actualizado
        """
        return ArticleAnalysis(metrics=self.metrics, duplicate=duplicate)

    @property
    def has_metrics(self) -> bool:
        """Verifica si tiene métricas calculadas."""
        return self.metrics.has_metrics

    @property
    def has_complete_metrics(self) -> bool:
        """Verifica si tiene métricas completas."""
        return self.metrics.has_complete_metrics

    @property
    def is_duplicate(self) -> bool:
        """Verifica si el artículo es un duplicado."""
        return self.duplicate.is_duplicate

    @property
    def has_complete_analysis(self) -> bool:
        """Verifica si tiene análisis completo (métricas + duplicación verificada)."""
        return self.has_complete_metrics
