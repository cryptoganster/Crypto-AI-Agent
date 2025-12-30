"""Interface para ContentChunk Write Repository."""

from typing import Protocol

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.knowledge.domain.value_objects.source_reference import SourceReference


class IContentChunkWriteRepository(Protocol):
    """
    Interface para operaciones de escritura de ContentChunk.

    Responsabilidades:
    - Guardar chunks
    - Eliminar chunks

    CQRS: Solo escritura, modifica estado.
    Unit of Work: NO hace commit (usa UoW pattern).
    """

    async def save(self, aggregate: ContentChunk) -> None:
        """
        Guarda ContentChunk aggregate.

        Si el aggregate ya existe, actualiza.
        Si no existe, crea nuevo.

        NO hace commit - usa Unit of Work pattern.

        Args:
            aggregate: ContentChunk aggregate a guardar
        """
        ...

    async def delete(self, chunk_id: str) -> None:
        """
        Elimina ContentChunk por ID.

        NO hace commit - usa Unit of Work pattern.

        Args:
            chunk_id: ID del ContentChunk a eliminar
        """
        ...

    async def delete_by_source(self, source: SourceReference) -> None:
        """
        Elimina todos los chunks de una fuente.

        NO hace commit - usa Unit of Work pattern.

        Args:
            source: SourceReference (source_id + source_type)
        """
        ...

    async def delete_by_article_id(self, article_id: str) -> None:
        """
        DEPRECATED: Usar delete_by_source() en su lugar.

        Elimina todos los chunks de un artículo.

        NO hace commit - usa Unit of Work pattern.

        Args:
            article_id: ID del artículo
        """
        ...
