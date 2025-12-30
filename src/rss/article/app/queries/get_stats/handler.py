"""Handler para query de estadísticas de artículos."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from src.rss.article.app.queries.get_stats.dto import ArticleStatsDTO, TimelineDataPoint
from src.rss.article.app.queries.get_stats.query import GetArticleStatsQuery
from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.interfaces.repositories import IArticleReadRepository
from src.rss.feed.domain.value_objects import SourceId


class GetArticleStatsHandler:
    """
    Handler para query de estadísticas de artículos.

    Este handler implementa la lógica de negocio para calcular
    estadísticas completas de artículos, usando queries simples
    para acceso a datos.

    Responsabilidades:
    - Obtener artículos usando IArticleReadRepository
    - Calcular estadísticas generales (totales, promedios)
    - Calcular distribución por fuente y estado
    - Calcular distribución de calidad
    - Generar timeline de publicaciones
    - Componer DTO de respuesta
    """

    def __init__(self, article_queries: IArticleReadRepository):
        """
        Inicializa el handler.

        Args:
            article_queries: Interface para queries simples de artículos
        """
        self._article_queries = article_queries

    async def handle(self, query: GetArticleStatsQuery) -> ArticleStatsDTO:
        """
        Ejecuta el query de estadísticas de artículos.

        Args:
            query: Query con filtros opcionales

        Returns:
            DTO con estadísticas completas calculadas
        """
        # 1. Obtener artículos usando query simple
        source_id = SourceId(query.source_id) if query.source_id else None
        articles = await self._article_queries.find_all(source_id=source_id)

        # 2. Si no hay artículos, retornar estadísticas vacías
        if not articles:
            return ArticleStatsDTO(
                total_articles=0,
                by_source={},
                by_status={},
                average_quality=0.0,
                recent_count=0,
                quality_distribution={
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "unscored": 0,
                },
                publication_timeline=[],
                source_id=str(query.source_id) if query.source_id else None,
            )

        # 3. Calcular estadísticas
        total_articles = len(articles)
        by_source = self._calculate_by_source(articles)
        by_status = self._calculate_by_status(articles)
        average_quality = self._calculate_average_quality(articles)
        recent_count = self._calculate_recent_count(articles)
        quality_distribution = self._calculate_quality_distribution(articles)
        publication_timeline = self._calculate_publication_timeline(
            articles, query.timeline_days
        )

        return ArticleStatsDTO(
            total_articles=total_articles,
            by_source=by_source,
            by_status=by_status,
            average_quality=average_quality,
            recent_count=recent_count,
            quality_distribution=quality_distribution,
            publication_timeline=publication_timeline,
            source_id=str(query.source_id) if query.source_id else None,
        )

    def _calculate_by_source(self, articles: List[Article]) -> Dict[str, int]:
        """
        Calcula distribución de artículos por fuente.

        Args:
            articles: Lista de artículos

        Returns:
            Diccionario con conteo por source_id
        """
        by_source = defaultdict(int)
        for article in articles:
            source_id_str = str(article.metadata.source_id.value)
            by_source[source_id_str] += 1
        return dict(by_source)

    def _calculate_by_status(self, articles: List[Article]) -> Dict[str, int]:
        """
        Calcula distribución de artículos por estado.

        Determina el estado basándose en los timestamps:
        - archived: tiene archived_at
        - published: tiene published_at pero no archived_at
        - draft: no tiene ni published_at ni archived_at

        Args:
            articles: Lista de artículos

        Returns:
            Diccionario con conteo por status
        """
        by_status = defaultdict(int)
        for article in articles:
            if article._archived_at is not None:
                by_status["archived"] += 1
            elif article._published_at is not None:
                by_status["published"] += 1
            else:
                by_status["draft"] += 1
        return dict(by_status)

    def _calculate_average_quality(self, articles: List[Article]) -> float:
        """
        Calcula el score promedio de calidad.

        Args:
            articles: Lista de artículos

        Returns:
            Score promedio (0.0-1.0), o 0.0 si no hay scores
        """
        scores = [
            a.quality.quality_score
            for a in articles
            if a.quality and a.quality.quality_score is not None
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _calculate_recent_count(self, articles: List[Article]) -> int:
        """
        Calcula el número de artículos en las últimas 24 horas.

        Args:
            articles: Lista de artículos

        Returns:
            Número de artículos recientes
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        return sum(1 for a in articles if a.created_at >= cutoff)

    def _calculate_quality_distribution(
        self, articles: List[Article]
    ) -> Dict[str, int]:
        """
        Calcula la distribución de artículos por rangos de calidad.

        Rangos:
        - high: >= 0.7
        - medium: >= 0.4
        - low: < 0.4
        - unscored: sin quality_score

        Args:
            articles: Lista de artículos

        Returns:
            Diccionario con conteo por rango
        """
        distribution = {
            "high": 0,  # >= 0.7
            "medium": 0,  # >= 0.4
            "low": 0,  # < 0.4
            "unscored": 0,  # None
        }

        for article in articles:
            if article.quality.quality_score is None:
                distribution["unscored"] += 1
            elif article.quality.quality_score >= 0.7:
                distribution["high"] += 1
            elif article.quality.quality_score >= 0.4:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1

        return distribution

    def _calculate_publication_timeline(
        self, articles: List[Article], days: int
    ) -> List[TimelineDataPoint]:
        """
        Calcula el timeline de publicaciones por fecha.

        Args:
            articles: Lista de artículos
            days: Número de días a incluir en el timeline

        Returns:
            Lista de puntos de datos ordenados por fecha
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Filtrar artículos recientes
        recent_articles = [a for a in articles if a.created_at >= cutoff]

        # Agrupar por fecha
        by_date = defaultdict(int)
        for article in recent_articles:
            date_str = article.created_at.date().isoformat()
            by_date[date_str] += 1

        # Convertir a lista de TimelineDataPoint y ordenar
        timeline = [
            TimelineDataPoint(date=date, count=count) for date, count in by_date.items()
        ]
        timeline.sort(key=lambda x: x.date)

        return timeline
