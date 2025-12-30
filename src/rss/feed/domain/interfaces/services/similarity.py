"""Interface para Source Similarity Service."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.rss.feed.domain.aggregates import Source

from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl


class ISourceSimilarityService(ABC):
    """
    Interface para Domain Service de análisis de similaridad de fuentes RSS.

    Responsabilidades:
    - Detectar sources duplicadas por URL
    - Calcular scores de similaridad entre sources
    - Comparación de URLs y metadatos
    - Análisis de dominios y subdominios relacionados
    """

    @abstractmethod
    def find_exact_duplicate_source(
        self,
        target_url: RssFeedUrl,
        sources: List["Source"],
    ) -> Optional["Source"]:
        """
        Busca source con URL exactamente igual.

        Args:
            target_url: URL objetivo a buscar
            sources: Lista de sources donde buscar

        Returns:
            Source duplicada o None si no se encuentra
        """
        ...

    @abstractmethod
    def find_similar_sources(
        self,
        target_url: RssFeedUrl,
        sources: List["Source"],
        similarity_threshold: float = 0.8,
        max_results: int = 10,
        include_inactive: bool = False,
    ) -> List["Source"]:
        """
        Encuentra sources similares usando algoritmo de similaridad URL.

        Args:
            target_url: URL objetivo
            sources: Lista de sources
            similarity_threshold: Umbral de similaridad (0.0-1.0)
            max_results: Número máximo de resultados
            include_inactive: Incluir sources inactivas

        Returns:
            Lista de sources similares ordenadas por score
        """
        ...

    @abstractmethod
    def calculate_source_similarity(
        self,
        source1: "Source",
        source2: "Source",
    ) -> float:
        """
        Calcula score de similaridad entre dos sources RSS.

        Args:
            source1: Primera source
            source2: Segunda source

        Returns:
            Score de similaridad (0.0-1.0)
        """
        ...

    @abstractmethod
    def calculate_source_similarity_by_url(
        self,
        url1: RssFeedUrl,
        url2: RssFeedUrl,
    ) -> float:
        """
        Calcula score de similaridad entre URLs RSS.

        Args:
            url1: Primera URL
            url2: Segunda URL

        Returns:
            Score de similaridad (0.0-1.0)
        """
        ...

    @abstractmethod
    def are_sources_similar(
        self,
        source1: "Source",
        source2: "Source",
        threshold: float = 0.8,
    ) -> bool:
        """
        Determina si dos sources son similares según threshold.

        Args:
            source1: Primera source
            source2: Segunda source
            threshold: Umbral de similaridad

        Returns:
            True si son similares, False en caso contrario
        """
        ...
