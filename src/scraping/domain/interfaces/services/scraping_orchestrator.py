"""Interface para ScrapingOrchestrator - Domain Service para coordinar scraping."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.rss.article.domain.aggregates import RssArticle
from src.rss.feed.domain.aggregates import Source
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.interfaces.external import ArticleData
from src.scraping.domain.value_objects import FetchLimit
from src.shared.domain.value_objects import QualityThreshold


@dataclass(frozen=True)
class FetchResult:
    """Resultado de operación de fetch con métricas agregadas."""

    success: bool
    total_sources_processed: int
    successful_sources: int
    failed_sources: int
    total_articles_discovered: int
    total_articles_created: int
    scraping_id: Optional[str] = None
    error_message: Optional[str] = None
    article_ids: Optional[List[str]] = None

    def __post_init__(self):
        """Inicializar lista vacía si es None."""
        if self.article_ids is None:
            object.__setattr__(self, "article_ids", [])


class IScrapingCoordinator(ABC):
    """
    Interface para ScrapingCoordinatorService - Domain Service de scraping adaptado a agregados DDD.

    Responsabilidades principales:
    - Coordinar scraping entre agregados Source, Scraping y Article
    - Orquestar operaciones de fetch usando agregados como unidades de consistencia
    - Aplicar reglas de negocio específicas del dominio RSS
    - Generar domain events automáticamente via agregados
    - Mantener separación clara entre agregados según bounded context
    """

    @abstractmethod
    async def fetch_sources(
        self,
        sources: List[Source],
        scraping: Scraping,
        fetch_limit: Optional[FetchLimit] = None,
        quality_threshold: Optional[QualityThreshold] = None,
    ) -> FetchResult:
        """
        Coordina fetch para múltiples fuentes usando agregados DDD.

        Args:
            sources: Lista de agregados Source activos para fetch
            scraping: Agregado Scraping que coordina la sesión
            fetch_limit: Límite de artículos por fuente
            quality_threshold: Umbral de calidad para filtrado

        Returns:
            FetchResult con métricas agregadas de la operación
        """
        pass

    @abstractmethod
    async def fetch_single_source(
        self,
        source: Source,
        scraping: Scraping,
        fetch_limit: Optional[FetchLimit] = None,
        quality_threshold: Optional[QualityThreshold] = None,
    ) -> Dict[str, Any]:
        """
        Procesa una fuente específica usando agregados Source y Scraping.

        Args:
            source: Agregado Source a procesar
            scraping: Agregado Scraping para tracking
            fetch_limit: Límite de artículos a procesar
            quality_threshold: Umbral de calidad opcional

        Returns:
            Dict con métricas de resultado para la fuente específica
        """
        pass

    @abstractmethod
    async def create_articles_from_fetch(
        self,
        articles_data: List[ArticleData],
        source: Source,
        scraping: Scraping,
        quality_threshold: Optional[QualityThreshold] = None,
    ) -> List[RssArticle]:
        """
        Crea agregados RssArticle desde datos de fetch RSS.

        Args:
            articles_data: Lista de datos de artículos extraídos
            source: Agregado Source de origen
            scraping: Agregado Scraping para contexto
            quality_threshold: Umbral de calidad para filtrado

        Returns:
            Lista de agregados RssArticle creados (que emiten domain events)
        """
        pass

    @abstractmethod
    def validate_source_for_fetch(self, source: Source) -> bool:
        """
        Regla de dominio: validar si Source aggregate está listo para fetch.

        Args:
            source: Agregado Source a validar

        Returns:
            True si el agregado Source puede ser procesado para fetch
        """
        pass
