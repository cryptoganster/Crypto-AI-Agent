"""Interface para RSS Feed Fetcher Service.

Servicio externo para fetch de feeds RSS/Atom.
Pertenece al bounded context Scraping.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.rss.feed.domain.aggregates import Source
from src.rss.feed.domain.value_objects import SourceId
from src.rss.feed.domain.value_objects.rss_feed_url import SourceUrl
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.value_objects import ScrapingIdentity as ScrapingId


@dataclass(frozen=True)
class ArticleData:
    """Datos de artículo RSS para crear Article aggregates.

    Value Object que representa los datos extraídos de un feed RSS
    antes de ser convertidos en Article aggregates.
    """

    title: str
    url: str
    description: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    published_at: Optional[datetime] = None
    guid: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Optional[dict] = None

    def __post_init__(self):
        if self.tags is None:
            object.__setattr__(self, "tags", [])
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


@dataclass(frozen=True)
class FetchResult:
    """Resultado de fetch RSS adaptado a agregados DDD.

    Value Object que encapsula el resultado de una operación
    de fetch de un feed RSS.
    """

    success: bool
    source_id: SourceId
    source_url: SourceUrl
    scraping_id: str
    articles_found: int
    articles_new: int
    fetch_duration_ms: float
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    http_status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    bytes_processed: Optional[int] = None
    should_suspend_source: bool = False
    article_data_list: Optional[List[ArticleData]] = None
    articles_data: Optional[List[ArticleData]] = None

    def __post_init__(self):
        if self.article_data_list is None:
            object.__setattr__(self, "article_data_list", [])
        if self.articles_data is None:
            object.__setattr__(self, "articles_data", self.article_data_list)
        elif self.article_data_list == []:
            object.__setattr__(self, "article_data_list", self.articles_data)


class IRssFeedFetcherService(ABC):
    """
    Interface para servicio de fetch de feeds RSS/Atom.

    Responsabilidades:
    - Descargar y parsear feeds RSS/Atom
    - Extraer metadatos de artículos
    - Manejar errores de red y parsing
    - Reportar estadísticas de fetch

    Características DDD:
    - Opera con Source y Scraping aggregates
    - Retorna ArticleData para crear Article aggregates
    - Abstracción pura sin dependencias de infraestructura
    """

    @abstractmethod
    async def fetch_from_source(
        self,
        source: Source,
        scraping: Scraping,
        scraping_id: ScrapingId,
    ) -> FetchResult:
        """
        Fetch contenido RSS desde un Source aggregate.

        Args:
            source: Source aggregate con URL y configuración
            scraping: Scraping aggregate para tracking
            scraping_id: ID del scraping record

        Returns:
            FetchResult con datos para crear Article aggregates
        """
        pass

    @abstractmethod
    async def fetch_multiple_sources(
        self,
        sources: List[Source],
        scraping: Scraping,
    ) -> List[FetchResult]:
        """
        Fetch múltiples Source aggregates.

        Args:
            sources: Lista de Source aggregates a procesar
            scraping: Scraping aggregate para tracking

        Returns:
            Lista de FetchResult para crear Article aggregates
        """
        pass

    @abstractmethod
    async def fetch_by_url(
        self,
        source_url: SourceUrl,
        scraping_id: str,
    ) -> FetchResult:
        """
        Fetch directo por URL (para casos simples).

        Args:
            source_url: URL RSS como Value Object
            scraping_id: ID de sesión para tracking

        Returns:
            FetchResult con datos de artículos
        """
        pass

    @abstractmethod
    def get_fetcher_statistics(self) -> dict:
        """Obtiene estadísticas del fetcher RSS."""
        pass

    @abstractmethod
    def reset_fetcher_statistics(self) -> None:
        """Resetea estadísticas del fetcher RSS."""
        pass
