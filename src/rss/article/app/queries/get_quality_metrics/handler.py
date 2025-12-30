"""Handler para query de métricas de calidad de artículos."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List

from src.rss.article.app.queries.get_quality_metrics.dto import QualityMetricsDTO
from src.rss.article.app.queries.get_quality_metrics.query import GetQualityMetricsQuery
from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.repositories import IArticleReadRepository
from src.rss.feed.domain.value_objects import SourceId


class GetQualityMetricsHandler:
    """
    Handler para query de métricas de calidad.

    Este handler implementa la lógica de negocio para calcular
    métricas de calidad de artículos, usando queries simples
    para acceso a datos.

    Responsabilidades:
    - Obtener artículos usando IArticleReadRepository
    - Filtrar por tiempo si es necesario
    - Calcular promedio de calidad
    - Calcular distribución por rangos
    - Componer DTO de respuesta
    """

    def __init__(self, article_queries: IArticleReadRepository):
        """
        Inicializa el handler.

        Args:
            article_queries: Interface para queries simples de artículos
        """
        self._article_queries = article_queries

    async def handle(self, query: GetQualityMetricsQuery) -> QualityMetricsDTO:
        """
        Ejecuta el query de métricas de calidad.

        Args:
            query: Query con filtros opcionales

        Returns:
            DTO con métricas de calidad calculadas
        """
        # 1. Obtener artículos usando query simple
        source_id = SourceId(query.source_id) if query.source_id else None
        articles = await self._article_queries.find_all(source_id=source_id)

        # 2. Filtrar por tiempo si es necesario
        if query.hours:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=query.hours)
            articles = [a for a in articles if a.created_at >= cutoff]

        # 3. Filtrar solo artículos con quality_score
        articles_with_score = [
            a for a in articles if a.quality.quality_score is not None
        ]

        # 4. Calcular métricas
        if not articles_with_score:
            return QualityMetricsDTO(
                average_score=0.0,
                distribution={
                    "excellent": 0,
                    "good": 0,
                    "average": 0,
                    "poor": 0,
                },
                total_articles=0,
                source_id=str(query.source_id) if query.source_id else None,
            )

        # Calcular promedio
        scores = [a.quality.quality_score for a in articles_with_score]
        average_score = sum(scores) / len(scores)

        # Calcular distribución
        distribution = self._calculate_distribution(articles_with_score)

        return QualityMetricsDTO(
            average_score=average_score,
            distribution=distribution,
            total_articles=len(articles_with_score),
            source_id=str(query.source_id) if query.source_id else None,
        )

    def _calculate_distribution(self, articles: List[Article]) -> Dict[str, int]:
        """
        Calcula la distribución de artículos por rangos de calidad.

        Rangos:
        - excellent: >= 0.8
        - good: >= 0.6
        - average: >= 0.4
        - poor: < 0.4

        Args:
            articles: Lista de artículos con quality_score

        Returns:
            Diccionario con conteo por rango
        """
        distribution = {
            "excellent": 0,  # >= 0.8
            "good": 0,  # >= 0.6
            "average": 0,  # >= 0.4
            "poor": 0,  # < 0.4
        }

        for article in articles:
            if article.quality.quality_score is None:
                continue

            if article.quality.quality_score >= 0.8:
                distribution["excellent"] += 1
            elif article.quality.quality_score >= 0.6:
                distribution["good"] += 1
            elif article.quality.quality_score >= 0.4:
                distribution["average"] += 1
            else:
                distribution["poor"] += 1

        return distribution
