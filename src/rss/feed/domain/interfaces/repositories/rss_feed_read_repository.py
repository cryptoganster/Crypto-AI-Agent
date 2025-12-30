"""Interface de repositorio de lectura para Source aggregate."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.rss.feed.domain.aggregates.rss_feed import RssFeed as Source


class IRssFeedReadRepository(ABC):
    """
    Repository interface para operaciones de lectura de Source.

    Operaciones básicas de DB sin lógica de negocio.
    Implementa el patrón Repository para el lado de lectura (CQRS).
    """

    # ========================================================================
    # Búsqueda por ID
    # ========================================================================

    @abstractmethod
    async def find_by_id(self, source_id: UUID) -> Optional[Source]:
        """
        Busca source por ID.

        Args:
            source_id: ID del source

        Returns:
            Source aggregate o None si no existe
        """
        pass

    @abstractmethod
    async def exists(self, source_id: UUID) -> bool:
        """
        Verifica si existe un source.

        Args:
            source_id: ID del source

        Returns:
            True si existe, False si no
        """
        pass

    # ========================================================================
    # Búsqueda por URL
    # ========================================================================

    @abstractmethod
    async def find_by_url(self, url: str) -> Optional[Source]:
        """
        Busca source por URL.

        Args:
            url: URL del source

        Returns:
            Source aggregate o None si no existe
        """
        pass

    @abstractmethod
    async def get_id_by_url(self, url: str) -> Optional[UUID]:
        """
        Obtiene solo el ID de un source por URL (optimizado).

        Args:
            url: URL del source

        Returns:
            UUID del source o None si no existe
        """
        pass

    # ========================================================================
    # Búsqueda por nombre
    # ========================================================================

    @abstractmethod
    async def find_by_name(
        self,
        name: str,
        exclude_source_id: Optional[UUID] = None,
    ) -> List[Source]:
        """
        Busca sources por nombre exacto.

        Args:
            name: Nombre a buscar
            exclude_source_id: ID de source a excluir de resultados

        Returns:
            Lista de sources con ese nombre
        """
        pass

    # ========================================================================
    # Búsqueda por dominio
    # ========================================================================

    @abstractmethod
    async def find_by_domain(
        self,
        domain: str,
        exclude_source_id: Optional[UUID] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Source]:
        """
        Busca sources por dominio.

        Args:
            domain: Dominio a buscar (ej: "example.com")
            exclude_source_id: ID de source a excluir
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de sources del dominio
        """
        pass

    @abstractmethod
    async def count_by_domain(self, domain: str) -> int:
        """
        Cuenta sources de un dominio.

        Args:
            domain: Dominio a contar

        Returns:
            Número de sources del dominio
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
    ) -> List[Source]:
        """
        Obtiene todas las sources con paginación.

        Args:
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de sources
        """
        pass

    @abstractmethod
    async def find_active(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Source]:
        """
        Obtiene sources activas.

        Args:
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de sources activas
        """
        pass

    @abstractmethod
    async def find_by_status(
        self,
        status: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Source]:
        """
        Busca sources por status.

        Args:
            status: Status a buscar
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de sources con ese status
        """
        pass

    # ========================================================================
    # Conteo
    # ========================================================================

    @abstractmethod
    async def count(self) -> int:
        """
        Cuenta total de sources.

        Returns:
            Número total de sources
        """
        pass

    @abstractmethod
    async def count_active(self) -> int:
        """
        Cuenta sources activas.

        Returns:
            Número de sources activas
        """
        pass

    # ========================================================================
    # Búsqueda de duplicados
    # ========================================================================

    @abstractmethod
    async def find_duplicates_by_url(
        self,
        url: str,
        exclude_source_id: Optional[UUID] = None,
    ) -> List[Source]:
        """
        Encuentra duplicados por URL exacta.

        Args:
            url: URL a buscar
            exclude_source_id: ID de source a excluir

        Returns:
            Lista de sources duplicados
        """
        pass

    @abstractmethod
    async def find_similar_by_url(
        self,
        url: str,
        threshold: float = 0.8,
        exclude_source_id: Optional[UUID] = None,
    ) -> List[Source]:
        """
        Encuentra sources similares por URL.

        Usa algoritmo de similitud de strings para encontrar URLs parecidas.

        Args:
            url: URL a comparar
            threshold: Umbral de similitud (0.0-1.0)
            exclude_source_id: ID de source a excluir

        Returns:
            Lista de sources similares
        """
        pass
