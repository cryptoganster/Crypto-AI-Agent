"""Interface para RSS Content Cleanup Service del dominio RSS."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from src.rss.article.domain.value_objects import RssArticleId
from src.rss.feed.domain.value_objects import RssFeedId


@dataclass(frozen=True)
class CleanupSummary:
    """Value Object para resumen de impacto de limpieza."""

    articles_to_remove: int
    fetch_sessions_to_cancel: int
    estimated_data_size_mb: float
    affected_categories: List[str]
    orphaned_references: int

    @property
    def has_significant_impact(self) -> bool:
        """Determina si la limpieza tiene impacto significativo."""
        return (
            self.articles_to_remove > 100
            or self.fetch_sessions_to_cancel > 5
            or self.estimated_data_size_mb > 50.0
        )


class IRssContentCleanupService(ABC):
    """
    Interface para servicio de limpieza de contenido RSS.

    Define el contrato para operaciones de limpieza en cascada
    cuando se eliminan sources RSS del aggregate.
    """

    @abstractmethod
    def cleanup_articles_by_source(self, source_id: RssFeedId) -> List[RssArticleId]:
        """
        Elimina todos los artículos asociados a una source RSS.

        Args:
            source_id: ID de la source RSS a limpiar

        Returns:
            Lista de IDs de artículos eliminados
        """
        pass

    @abstractmethod
    def cleanup_orphaned_fetch_sessions(self) -> int:
        """
        Limpia sesiones de fetch huérfanas (sin sources activas).

        Returns:
            Número de sesiones eliminadas
        """
        pass

    @abstractmethod
    def get_cleanup_impact_summary(self, source_id: RssFeedId) -> CleanupSummary:
        """
        Calcula el impacto de eliminar una source RSS antes de ejecutar la limpieza.

        Args:
            source_id: ID de la source RSS a evaluar

        Returns:
            Resumen del impacto de la limpieza
        """
        pass
