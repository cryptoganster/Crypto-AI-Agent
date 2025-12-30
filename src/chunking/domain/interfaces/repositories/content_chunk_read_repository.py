"""Interface para ContentChunk Read Repository."""

from typing import List, Optional, Protocol

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.knowledge.domain.value_objects.source_reference import SourceReference


class IContentChunkReadRepository(Protocol):
    """
    Interface para operaciones de lectura de ContentChunk.

    Responsabilidades:
    - Buscar chunks por ID
    - Buscar chunks por source (article_id + source_type)
    - Buscar chunks por status
    - Contar chunks

    CQRS: Solo lectura, no modifica estado.
    """

    async def find_by_id(self, chunk_id: str) -> Optional[ContentChunk]:
        """
        Busca ContentChunk por ID.

        Args:
            chunk_id: ID del ContentChunk

        Returns:
            ContentChunk si existe, None si no
        """
        ...

    async def find_by_source(
        self,
        source: SourceReference,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ContentChunk]:
        """
        Busca todos los chunks de una fuente.

        Args:
            source: SourceReference (source_id + source_type)
            limit: Límite de resultados (opcional)
            offset: Offset para paginación (opcional)

        Returns:
            Lista de ContentChunks ordenados por position
        """
        ...

    async def find_by_article_id(
        self,
        article_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ContentChunk]:
        """
        DEPRECATED: Usar find_by_source() en su lugar.

        Busca todos los chunks de un artículo.

        Args:
            article_id: ID del artículo
            limit: Límite de resultados (opcional)
            offset: Offset para paginación (opcional)

        Returns:
            Lista de ContentChunks ordenados por position
        """
        ...

    async def find_by_status(
        self,
        status: ChunkStatus,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ContentChunk]:
        """
        Busca chunks por estado.

        Args:
            status: Estado a buscar
            limit: Límite de resultados (opcional)
            offset: Offset para paginación (opcional)

        Returns:
            Lista de ContentChunks con el estado especificado
        """
        ...

    async def exists(self, chunk_id: str) -> bool:
        """
        Verifica si existe ContentChunk por ID.

        Args:
            chunk_id: ID del ContentChunk

        Returns:
            True si existe, False si no
        """
        ...

    async def count_by_source(self, source: SourceReference) -> int:
        """
        Cuenta chunks de una fuente.

        Args:
            source: SourceReference (source_id + source_type)

        Returns:
            Número de chunks
        """
        ...

    async def count_by_article_id(self, article_id: str) -> int:
        """
        DEPRECATED: Usar count_by_source() en su lugar.

        Cuenta chunks de un artículo.

        Args:
            article_id: ID del artículo

        Returns:
            Número de chunks
        """
        ...

    async def count_by_status(self, status: ChunkStatus) -> int:
        """
        Cuenta chunks por estado.

        Args:
            status: Estado a contar

        Returns:
            Número de chunks con ese estado
        """
        ...

    async def find_similar_by_embedding(
        self,
        embedding_vector: List[float],
        threshold: float,
        limit: int = 10,
        exclude_source: Optional[SourceReference] = None,
    ) -> List[tuple[ContentChunk, float]]:
        """
        Busca chunks similares usando búsqueda vectorial.

        Args:
            embedding_vector: Vector de embedding para comparar
            threshold: Threshold de similitud (0.0-1.0)
            limit: Máximo número de resultados
            exclude_source: SourceReference a excluir (opcional)

        Returns:
            Lista de tuplas (ContentChunk, similarity_score) ordenadas por similitud

        Note:
            Requiere extensión pgvector en PostgreSQL.
            Retorna tuplas para mantener immutabilidad del aggregate.
        """
        ...
