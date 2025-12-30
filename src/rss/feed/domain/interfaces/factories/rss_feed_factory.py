"""Interface para SourceFactory moderno."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.value_objects.configuration import SourceConfiguration
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId

if TYPE_CHECKING:
    from src.rss.feed.domain.factories.rss_feed_factory import (
        FeedMetadata,
        ValidationResult,
    )


class ISourceFactory(ABC):
    """
    Interface para SourceFactory que trabaja con Source aggregate.

    Define contrato para creación de Sources con validaciones avanzadas,
    derivación inteligente de nombres y blacklist de dominios.
    """

    @abstractmethod
    def create_source(
        self,
        url: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        configuration: Optional[SourceConfiguration] = None,
        source_id: Optional[SourceId] = None,
    ) -> Source:
        """
        Crea nueva Source con validaciones y limpieza de dominio.

        Args:
            url: URL del feed RSS (string raw)
            name: Nombre opcional para la source
            description: Descripción opcional
            configuration: Configuración específica (usa default si None)
            source_id: ID específico (genera uno si None)

        Returns:
            Nueva instancia de Source con eventos de dominio

        Raises:
            ValueError: Si los datos no pasan validaciones de dominio
        """
        pass

    @abstractmethod
    def create_from_feed_metadata(
        self,
        url: str,
        metadata: "FeedMetadata",
        configuration: Optional[SourceConfiguration] = None,
    ) -> Source:
        """
        Crea Source desde metadatos de feed RSS con inteligencia de dominio.

        Args:
            url: URL del feed RSS
            metadata: Metadatos extraídos del feed RSS
            configuration: Configuración específica (opcional)

        Returns:
            Nueva instancia de Source con metadatos aplicados y eventos
        """
        pass

    @abstractmethod
    def validate_source_creation_data(
        self,
        url: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "ValidationResult":
        """
        Valida datos para creación de source con reglas de dominio avanzadas.

        Args:
            url: URL del feed RSS a validar
            name: Nombre opcional a validar
            description: Descripción opcional a validar

        Returns:
            Resultado de validación con errores y warnings detallados
        """
        pass

    @abstractmethod
    def reconstruct_from_persistence(
        self,
        source_id: SourceId,
        url: str,
        name: str,
        description: Optional[str] = None,
        configuration: Optional[SourceConfiguration] = None,
        status: Optional[str] = None,
        created_at: Optional[object] = None,
        updated_at: Optional[object] = None,
        last_fetch_at: Optional[object] = None,
        health_metrics: Optional[dict] = None,
        **kwargs,
    ) -> Source:
        """
        Reconstruye Source desde datos de persistencia.

        Args:
            source_id: ID de la source
            url: URL del feed RSS
            name: Nombre de la source
            description: Descripción (opcional)
            configuration: Configuración específica (opcional)
            status: Estado actual (opcional)
            created_at: Timestamp de creación (opcional)
            updated_at: Timestamp de última actualización (opcional)
            last_fetch_at: Timestamp del último fetch (opcional)
            health_metrics: Métricas de salud (opcional)

        Returns:
            Source reconstruida sin ejecutar validaciones ni eventos de dominio

        Note:
            Este método se usa para reconstruir agregados desde persistencia,
            por lo que omite validaciones de dominio y eventos.
        """
        pass
