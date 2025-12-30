"""Interface de repositorio de escritura para Source aggregate."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.rss.feed.domain.aggregates.rss_feed import RssFeed as Source


class IRssFeedWriteRepository(ABC):
    """
    Repository interface para operaciones de escritura de Source.

    Operaciones de persistencia (Create, Update, Delete).
    Implementa el patrón Repository para el lado de escritura (CQRS).
    """

    @abstractmethod
    async def save(self, source: Source) -> None:
        """
        Guarda un source (create o update).

        Si el source existe (por ID), lo actualiza.
        Si no existe, lo crea.

        Args:
            source: Source aggregate a guardar

        Raises:
            RepositoryException: Si falla la operación
        """
        pass

    @abstractmethod
    async def delete(self, source_id: UUID) -> None:
        """
        Elimina un source por ID.

        Args:
            source_id: ID del source a eliminar

        Raises:
            RepositoryException: Si falla la operación
            SourceNotFoundException: Si el source no existe
        """
        pass

    @abstractmethod
    async def delete_by_url(self, url: str) -> None:
        """
        Elimina un source por URL.

        Args:
            url: URL del source a eliminar

        Raises:
            RepositoryException: Si falla la operación
            SourceNotFoundException: Si el source no existe
        """
        pass
