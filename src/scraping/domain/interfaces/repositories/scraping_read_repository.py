"""Interface de repositorio de lectura para Scraping aggregate."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.scraping.domain.aggregates import Scraping


class IScrapingReadRepository(ABC):
    """
    Repository interface para operaciones de lectura de Scraping.

    Operaciones básicas de DB sin lógica de negocio.
    Implementa el patrón Repository para el lado de lectura (CQRS).
    """

    # ========================================================================
    # Búsqueda por ID
    # ========================================================================

    @abstractmethod
    async def find_by_id(self, scraping_id: UUID) -> Optional[Scraping]:
        """
        Busca scraping por ID.

        Args:
            scraping_id: ID del scraping

        Returns:
            Scraping aggregate o None si no existe
        """
        pass

    @abstractmethod
    async def exists(self, scraping_id: UUID) -> bool:
        """
        Verifica si existe un scraping.

        Args:
            scraping_id: ID del scraping

        Returns:
            True si existe, False si no
        """
        pass

    # ========================================================================
    # Búsqueda por Source
    # ========================================================================

    @abstractmethod
    async def find_by_source(
        self,
        source_id: UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Scraping]:
        """
        Busca scrapings por source_id.

        Args:
            source_id: ID de la source
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de scrapings de esa source
        """
        pass

    @abstractmethod
    async def count_by_source(self, source_id: UUID) -> int:
        """
        Cuenta scrapings de una source.

        Args:
            source_id: ID de la source

        Returns:
            Número de scrapings de esa source
        """
        pass

    # ========================================================================
    # Búsqueda por Status
    # ========================================================================

    @abstractmethod
    async def find_by_status(
        self,
        status: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Scraping]:
        """
        Busca scrapings por status.

        Args:
            status: Status a buscar
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de scrapings con ese status
        """
        pass

    # ========================================================================
    # Listado y paginación
    # ========================================================================

    @abstractmethod
    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Scraping]:
        """
        Obtiene todos los scrapings con paginación.

        Args:
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de scrapings
        """
        pass

    @abstractmethod
    async def find_active(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Scraping]:
        """
        Obtiene scrapings activos.

        Args:
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de scrapings activos
        """
        pass

    # ========================================================================
    # Conteo
    # ========================================================================

    @abstractmethod
    async def count(self) -> int:
        """
        Cuenta total de scrapings.

        Returns:
            Número total de scrapings
        """
        pass

    @abstractmethod
    async def count_active(self) -> int:
        """
        Cuenta scrapings activos.

        Returns:
            Número de scrapings activos
        """
        pass
