"""Interface para ContextPack read repository (CQRS Read Side)."""

from datetime import datetime
from typing import List, Optional, Protocol

from src.rag.domain.aggregates.context_pack import ContextPack
from src.rag.domain.value_objects.context_pack_id import ContextPackId


class IContextPackReadRepository(Protocol):
    """
    Interface para operaciones de lectura de ContextPack.

    Sigue CQRS pattern - solo operaciones de lectura.

    Requirements: 10.5.1
    """

    async def find_by_id(self, context_pack_id: ContextPackId) -> Optional[ContextPack]:
        """
        Busca context pack por ID.

        Args:
            context_pack_id: ID del context pack

        Returns:
            ContextPack si existe, None si no

        Examples:
            >>> pack = await repository.find_by_id(ContextPackId("pack-123"))
            >>> pack.id
            ContextPackId("pack-123")
        """
        ...

    async def find_by_query(
        self,
        query: str,
        limit: Optional[int] = None,
    ) -> List[ContextPack]:
        """
        Busca context packs por query.

        Args:
            query: Query de búsqueda
            limit: Límite de resultados (opcional)

        Returns:
            Lista de context packs que coinciden con el query

        Examples:
            >>> packs = await repository.find_by_query("Bitcoin regulation", limit=10)
            >>> len(packs) <= 10
            True
        """
        ...

    async def find_recent(
        self,
        limit: int = 10,
        since: Optional[datetime] = None,
    ) -> List[ContextPack]:
        """
        Busca context packs recientes.

        Args:
            limit: Número máximo de resultados
            since: Fecha desde la cual buscar (opcional)

        Returns:
            Lista de context packs ordenados por fecha descendente

        Examples:
            >>> packs = await repository.find_recent(limit=5)
            >>> len(packs) <= 5
            True
            >>> packs[0].created_at >= packs[1].created_at
            True
        """
        ...

    async def exists(self, context_pack_id: ContextPackId) -> bool:
        """
        Verifica si existe un context pack.

        Args:
            context_pack_id: ID del context pack

        Returns:
            True si existe, False si no

        Examples:
            >>> exists = await repository.exists(ContextPackId("pack-123"))
            >>> exists
            True
        """
        ...

    async def count(self) -> int:
        """
        Cuenta total de context packs.

        Returns:
            Número total de context packs

        Examples:
            >>> count = await repository.count()
            >>> count >= 0
            True
        """
        ...
