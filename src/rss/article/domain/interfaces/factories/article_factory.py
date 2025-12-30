"""Interface para RssArticleFactory moderno."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from src.rss.article.domain.aggregates import RssArticle

# Alias para compatibilidad
Article = RssArticle
from src.rss.article.domain.value_objects.metadata import RssArticleId
from src.rss.feed.domain.value_objects import SourceId

if TYPE_CHECKING:
    from src.rss.article.domain.factories.rss_article_factory import (
        FeedItem,
        ValidationResult,
    )


class IRssArticleFactory(ABC):
    """
    Interface para RssArticleFactory que trabaja con RssArticle aggregate.

    Define contrato para creación de RssArticles con validaciones avanzadas
    y funcionalidad de limpieza de datos preservada del factory anterior.
    """

    @abstractmethod
    def create_article(
        self,
        title: str,
        url: str,
        source_id: SourceId,
        content: Optional[str] = None,
        article_id: Optional[RssArticleId] = None,
        thumbnail_url: Optional[str] = None,
        guid: Optional[str] = None,
        published_at: Optional[datetime] = None,
        description: Optional[str] = None,
        **metadata,
    ) -> Article:
        """
        Crea nuevo Article con validaciones y limpieza de dominio.

        Args:
            title: Título del artículo
            url: URL del artículo
            source_id: ID de la source RSS
            content: Contenido opcional del artículo
            article_id: ID específico (genera determinístico si None)
            thumbnail_url: URL de thumbnail opcional
            guid: GUID único del RSS feed
            published_at: Fecha de publicación original del RSS
            description: Descripción original del RSS feed
            **metadata: Metadatos adicionales (author, tags, etc.)

        Returns:
            Nueva instancia de Article con eventos de dominio

        Raises:
            ValueError: Si los datos no pasan validaciones de dominio
        """
        pass

    @abstractmethod
    def create_from_feed_item(
        self,
        feed_item: "FeedItem",
        source_id: SourceId,
        quality_assessment: bool = True,
    ) -> Article:
        """
        Crea Article desde item de feed RSS con inteligencia de dominio.

        Args:
            feed_item: Item del feed RSS con metadatos
            source_id: ID de la source RSS origen
            quality_assessment: True para evaluar calidad automáticamente

        Returns:
            Nueva instancia de Article con metadatos aplicados y eventos
        """
        pass

    @abstractmethod
    def validate_article_creation_data(
        self, title: str, url: str, source_id: str, **kwargs
    ) -> "ValidationResult":
        """
        Valida datos para creación de artículo con reglas de dominio avanzadas.

        Args:
            title: Título del artículo a validar
            url: URL del artículo a validar
            source_id: ID de la source RSS a validar
            **kwargs: Argumentos adicionales a validar

        Returns:
            Resultado de validación con errores y warnings detallados
        """
        pass


# Alias para compatibilidad
IArticleFactory = IRssArticleFactory
