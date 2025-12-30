"""Interface para ContextPack write repository (CQRS Write Side)."""

from typing import Protocol

from src.rag.domain.aggregates.context_pack import ContextPack
from src.rag.domain.value_objects.context_pack_id import ContextPackId


class IContextPackWriteRepository(Protocol):
    """
    Interface para operaciones de escritura de ContextPack.

    Sigue CQRS pattern - solo operaciones de escritura.
    NO hace commit (usa Unit of Work pattern).

    Requirements: 10.5.1
    """

    async def save(self, context_pack: ContextPack) -> None:
        """
        Guarda context pack (insert o update).

        NO hace commit - usa Unit of Work pattern.

        Args:
            context_pack: Context pack a guardar

        Examples:
            >>> pack = ContextPack.create(...)
            >>> await repository.save(pack)
            >>> await uow.commit()  # Commit explícito
        """
        ...

    async def delete(self, context_pack_id: ContextPackId) -> None:
        """
        Elimina context pack por ID.

        NO hace commit - usa Unit of Work pattern.

        Args:
            context_pack_id: ID del context pack a eliminar

        Examples:
            >>> await repository.delete(ContextPackId("pack-123"))
            >>> await uow.commit()  # Commit explícito
        """
        ...
