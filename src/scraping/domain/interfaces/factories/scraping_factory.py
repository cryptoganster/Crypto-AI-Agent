"""Interface para ScrapingFactory moderno."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.value_objects import SourceId
from src.scraping.domain.aggregates import Scraping

if TYPE_CHECKING:
    from src.scraping.domain.factories import ValidationResult
    from src.scraping.domain.value_objects import ScrapingConfig


class IScrapingFactory(ABC):
    """
    Interface para ScrapingFactory que trabaja con Scraping aggregate.

    Define contrato para creación de Scrapings con configuraciones avanzadas,
    optimizaciones por dominio y manejo de sesiones prioritarias.
    """

    @abstractmethod
    def create_for_source(
        self,
        source: Source,
        config: Optional["ScrapingConfig"] = None,
        scraping_id: Optional[str] = None,
    ) -> Scraping:
        """
        Crea Scraping optimizada para una Source específica.

        Args:
            source: Source aggregate para la cual crear la sesión
            config: Configuración específica (usa inteligente si None)
            scraping_id: ID específico (genera uno si None)

        Returns:
            Nueva instancia de Scraping con configuración optimizada

        Raises:
            ValueError: Si los datos no pasan validaciones de dominio
        """
        pass

    @abstractmethod
    def create_batch_session(
        self,
        sources: List[Source],
        config: Optional["ScrapingConfig"] = None,
        session_name: Optional[str] = None,
    ) -> List[Scraping]:
        """
        Crea múltiples Scrapings para procesamiento en lote.

        Args:
            sources: Lista de Sources para procesar
            config: Configuración base (se optimiza por source)
            session_name: Nombre descriptivo para el lote

        Returns:
            Lista de Scrapings configuradas para cada source

        Raises:
            ValueError: Si alguna source no es válida
        """
        pass

    @abstractmethod
    def validate_scraping_config(self, config: "ScrapingConfig") -> "ValidationResult":
        """
        Valida configuración de Scraping con reglas de dominio.

        Args:
            config: Configuración a validar

        Returns:
            Resultado de validación con errores y warnings detallados
        """
        pass

    @abstractmethod
    def get_configuration_preset(self, preset_name: str) -> "ScrapingConfig":
        """
        Obtiene configuración predefinida por nombre.

        Args:
            preset_name: Nombre del preset (fast, standard, slow, bulk, priority)

        Returns:
            ScrapingConfig predefinida

        Raises:
            ValueError: Si el preset no existe
        """
        pass

    @abstractmethod
    def create_priority_session(
        self,
        source: Source,
        priority_level: str = "high",
        scraping_id: Optional[str] = None,
    ) -> Scraping:
        """
        Crea sesión de scraping con prioridad específica.

        Args:
            source: Source para scraping prioritario
            priority_level: Nivel de prioridad (high, medium, low)
            scraping_id: ID específico (opcional)

        Returns:
            Scraping configurada para prioridad específica
        """
        pass

    @abstractmethod
    def reconstruct_from_persistence(
        self,
        sources_to_scrape: List[SourceId],
        scraping_id: str,
        max_concurrent_scrapes: int,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        status: Optional[str] = None,
        error_details: Optional[dict] = None,
        scraping_results: Optional[dict] = None,
        **kwargs,
    ) -> Scraping:
        """
        Reconstruye Scraping desde datos de persistencia.

        Args:
            sources_to_scrape: Lista de IDs de sources
            scraping_id: ID de la sesión
            max_concurrent_scrapes: Máximo de scrapes concurrentes
            created_at: Timestamp de creación
            updated_at: Timestamp de última actualización
            started_at: Timestamp de inicio (opcional)
            completed_at: Timestamp de finalización (opcional)
            status: Estado actual (opcional)
            error_details: Detalles de errores (opcional)
            scraping_results: Resultados de scraping (opcional)

        Returns:
            Scraping reconstruida sin ejecutar validaciones ni eventos de dominio

        Note:
            Este método se usa para reconstruir agregados desde persistencia,
            por lo que omite validaciones de dominio y eventos.
        """
        pass
