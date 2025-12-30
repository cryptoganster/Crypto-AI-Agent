"""
Interface para ArticleDeduplicationService - Domain Service de deduplicación.

Define el contrato para detección de artículos duplicados con múltiples estrategias.
"""

from typing import Dict, List, Optional, Protocol

from src.rss.article.domain.aggregates.rss_article import RssArticle as Article
from src.rss.article.domain.value_objects import ArticleId
from src.rss.article.domain.value_objects.deduplication_result import (
    ArticleDeduplicationResult,
)
from src.rss.feed.domain.aggregates import Source
from src.scraping.domain.interfaces.external import ArticleData


class IArticleDeduplicationService(Protocol):
    """
    Interface para servicio de deduplicación de artículos.

    Estrategias soportadas:
    - hash: Deduplicación basada en content hash
    - similarity: Deduplicación basada en similaridad de contenido
    - hybrid: Combinación de hash + similarity
    - url: Deduplicación basada en URL (más rápida para fetch)
    """

    def check_duplicate(
        self,
        article: Article,
        strategy: str = "hybrid",
    ) -> ArticleDeduplicationResult:
        """
        Verifica si un artículo es duplicado usando estrategia especificada.

        Args:
            article: Article aggregate a verificar
            strategy: Estrategia de detección (hash, similarity, hybrid, url)

        Returns:
            ArticleDeduplicationResult con información de duplicado
        """
        ...

    async def check_duplicate_by_url(
        self,
        article_data: ArticleData,
        source: Source,
    ) -> bool:
        """
        Verifica si un artículo ya existe basándose en URL.

        Método optimizado para operaciones de fetch donde solo tenemos
        ArticleData y necesitamos verificación rápida antes de crear aggregate.

        Args:
            article_data: Datos del artículo desde RSS fetcher
            source: Source aggregate de origen

        Returns:
            True si el artículo ya existe (es duplicado)
        """
        ...

    def mark_as_duplicate(
        self,
        article: Article,
        original_article_id: ArticleId,
        detection_method: str,
    ) -> None:
        """
        Marca un artículo como duplicado en el aggregate.

        Args:
            article: Article a marcar como duplicado
            original_article_id: ID del artículo original
            detection_method: Método usado para detectar duplicado
        """
        ...

    def find_all_duplicates(
        self,
        articles: List[Article],
        strategy: str = "hybrid",
    ) -> Dict[ArticleId, List[ArticleId]]:
        """
        Encuentra todos los duplicados en una lista de artículos.

        Args:
            articles: Lista de artículos a verificar
            strategy: Estrategia de detección

        Returns:
            Dict con article_id -> [duplicate_ids]
        """
        ...
