"""DTO para chunks de artículos."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ArticleChunkDTO:
    """
    DTO con información de un chunk de artículo.

    Representa un chunk almacenado en el vector store sin exponer
    detalles de implementación del aggregate ContentChunk.

    Attributes:
        chunk_id: ID único del chunk
        article_id: ID del artículo al que pertenece
        position: Posición del chunk en el artículo (0-based)
        text: Texto del chunk
        token_count: Número de tokens en el chunk
        summary: Summary del chunk (si está disponible)
        embedding: Vector embedding del chunk (si se solicitó)
        embedding_dimension: Dimensión del embedding (si está disponible)
        is_completed: Si el chunk completó todo el procesamiento

    Example:
        >>> dto = ArticleChunkDTO(
        ...     chunk_id="chunk-123",
        ...     article_id="art-123",
        ...     position=0,
        ...     text="This is the first chunk...",
        ...     token_count=512,
        ...     summary="Summary of first chunk",
        ...     embedding=None,
        ...     embedding_dimension=768,
        ...     is_completed=True,
        ... )
        >>> dto.has_summary
        True
        >>> dto.has_embedding
        False
    """

    chunk_id: str
    article_id: str
    position: int
    text: str
    token_count: int
    summary: Optional[str]
    embedding: Optional[List[float]]
    embedding_dimension: Optional[int]
    is_completed: bool

    @property
    def has_summary(self) -> bool:
        """Indica si el chunk tiene summary."""
        return self.summary is not None and len(self.summary) > 0

    @property
    def has_embedding(self) -> bool:
        """Indica si el chunk tiene embedding."""
        return self.embedding is not None and len(self.embedding) > 0

    @property
    def text_preview(self) -> str:
        """
        Retorna un preview del texto (primeros 100 caracteres).

        Returns:
            Preview del texto con "..." si es más largo
        """
        if len(self.text) <= 100:
            return self.text
        return self.text[:100] + "..."


@dataclass(frozen=True)
class ArticleChunksResultDTO:
    """
    DTO con el resultado de la query de chunks.

    Incluye los chunks y metadata de paginación.

    Attributes:
        article_id: ID del artículo
        chunks: Lista de chunks
        total_chunks: Número total de chunks del artículo
        returned_chunks: Número de chunks retornados en esta página
        offset: Offset usado en la query
        has_more: Si hay más chunks disponibles

    Example:
        >>> result = ArticleChunksResultDTO(
        ...     article_id="art-123",
        ...     chunks=[chunk1, chunk2, chunk3],
        ...     total_chunks=10,
        ...     returned_chunks=3,
        ...     offset=0,
        ...     has_more=True,
        ... )
        >>> result.has_more
        True
        >>> len(result.chunks)
        3
    """

    article_id: str
    chunks: List[ArticleChunkDTO]
    total_chunks: int
    returned_chunks: int
    offset: int
    has_more: bool

    @property
    def is_empty(self) -> bool:
        """Indica si no hay chunks."""
        return len(self.chunks) == 0

    @property
    def completion_percentage(self) -> float:
        """
        Calcula el porcentaje de chunks completados.

        Returns:
            Porcentaje de 0.0 a 100.0
        """
        if self.total_chunks == 0:
            return 0.0

        completed_count = sum(1 for chunk in self.chunks if chunk.is_completed)
        return (completed_count / len(self.chunks)) * 100.0
