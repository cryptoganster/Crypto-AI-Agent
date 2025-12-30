"""Domain Service para limpieza de contenido RSS."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.rss.article.domain.aggregates import RssArticle
from src.rss.article.domain.interfaces.repositories import (
    IRssArticleWriteRepository,
)
from src.rss.article.domain.value_objects import RssArticleId
from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.interfaces.services.rss_content_cleanup_service import (
    CleanupSummary,
    IRssContentCleanupService,
)
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.entities import ScrapingRecord, ScrapingRecordStatus


class RssContentCleanupService(IRssContentCleanupService):
    """
    Domain Service para operaciones de limpieza de contenido RSS.

    Responsabilidades:
    - Limpieza en cascada de artículos cuando se elimina una source
    - Limpieza de sesiones de fetch huérfanas
    - Cálculo de impacto antes de ejecutar limpieza
    - Mantenimiento de invariantes del dominio durante limpieza
    """

    def __init__(self, article_repository: IRssArticleWriteRepository):
        """
        Inicializa el servicio de limpieza de contenido RSS.

        Args:
            article_repository: Repositorio de artículos para consultas y eliminación
        """
        self._article_repository = article_repository

    async def cleanup_articles_by_source(self, source_id: RssFeedId) -> List[RssArticleId]:
        """
        Elimina todos los artículos asociados a una source RSS.

        Args:
            source_id: ID de la source RSS a limpiar

        Returns:
            Lista de IDs de artículos eliminados
        """
        # Consultar repositorio para encontrar todos los artículos de la source
        articles = await self._article_repository.find_all(source_id=source_id)

        deleted_ids = []
        for article in articles:
            # Eliminar cada artículo
            success = await self._article_repository.delete(article.id)
            if success:
                deleted_ids.append(article.id)

        return deleted_ids

    async def cleanup_orphaned_fetch_sessions(self) -> int:
        """
        Limpia sesiones de fetch huérfanas (sin sources activas).

        Returns:
            Número de sesiones eliminadas
        """
        # NOTA: Esta funcionalidad requiere un repositorio de FetchSession
        # Por ahora retornamos 0 hasta que se implemente
        return 0

    async def get_cleanup_impact_summary(self, source_id: RssFeedId) -> CleanupSummary:
        """
        Calcula el impacto de eliminar una source RSS antes de ejecutar la limpieza.

        Args:
            source_id: ID de la source RSS a evaluar

        Returns:
            Resumen del impacto de la limpieza
        """
        # Consultar repositorio para calcular el impacto basado en datos reales
        articles = await self._article_repository.find_all(source_id=source_id)

        # Calcular tamaño estimado de datos (aproximado)
        estimated_size_mb = 0.0
        affected_categories = set()

        for article in articles:
            # Estimar tamaño: título + contenido + metadata
            title_str = str(article.metadata.title) if article.metadata.title else ""
            content_size = len(article.content.markdown or "") + len(title_str)
            estimated_size_mb += content_size / (1024 * 1024)  # Convertir a MB

            # Recolectar categorías afectadas
            if article.metadata.category.value:
                affected_categories.add(article.metadata.category.value)

        return CleanupSummary(
            articles_to_remove=len(articles),
            fetch_sessions_to_cancel=0,  # Requiere repositorio de FetchSession
            estimated_data_size_mb=round(
                estimated_size_mb, 4
            ),  # 4 decimales para capturar tamaños pequeños
            affected_categories=list(affected_categories),
            orphaned_references=0,  # Requiere análisis de referencias
        )
