"""KnowledgeChunk aggregate root."""

from datetime import datetime, timezone
from typing import Optional

from src.chunking.domain.events import (
    ChunkCompletedEvent,
    ChunkCreatedEvent,
    ChunkEmbeddedEvent,
    ChunkFailedEvent,
    ChunkSummarizedEvent,
)
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.chunking.domain.value_objects.token_count import TokenCount
from src.chunking.domain.value_objects.vector_embedding import VectorEmbedding
from src.knowledge.domain.value_objects.source_reference import SourceReference
from src.shared.kernel.aggregate_root import IAggregateRoot


class KnowledgeChunk(IAggregateRoot[ChunkId]):
    """
    Aggregate root para fragmento de conocimiento.

    Representa una unidad atómica de conocimiento extraída de un artículo.
    Cada chunk es independiente y puede ser consultado/actualizado sin cargar
    el artículo completo. Esto permite búsqueda vectorial eficiente y
    procesamiento paralelo.

    Ciclo de vida:
    1. PENDING: Chunk creado, esperando embedding
    2. EMBEDDED: Embedding generado, esperando summarización
    3. SUMMARIZED: Summary generado, esperando completar
    4. COMPLETED: Procesamiento completo

    Attributes:
        id: Identificador único del chunk
        source: Referencia al contenido fuente (artículo RSS, documento, etc.)
        content: Texto del chunk
        embedding: Embedding vectorial (opcional hasta que se genere)
        summary: Summary del chunk (opcional hasta que se genere)
        position: Posición del chunk en el contenido original (0-indexed)
        start_char: Índice del primer carácter en el contenido original
        end_char: Índice del último carácter en el contenido original
        token_count: Número de tokens en el chunk
        status: Estado del procesamiento
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización

    Examples:
        >>> source = SourceReference.from_article(
        ...     article_id="article-123",
        ...     url="https://example.com/article"
        ... )
        >>> chunk = KnowledgeChunk(
        ...     id=ChunkId.generate(),
        ...     source=source,
        ...     content="Bitcoin alcanzó $50,000...",
        ...     position=0,
        ...     start_char=0,
        ...     end_char=100,
        ...     token_count=TokenCount(value=50, encoding="cl100k_base"),
        ... )
        >>> chunk.status
        <ChunkStatus.PENDING: 'PENDING'>
        >>> chunk.can_embed()
        True
    """

    def __init__(
        self,
        id: ChunkId,
        source: SourceReference,
        content: str,
        position: int,
        start_char: int,
        end_char: int,
        token_count: TokenCount,
        embedding: Optional[VectorEmbedding] = None,
        summary: Optional[ChunkSummary] = None,
        status: ChunkStatus = ChunkStatus.PENDING,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Inicializa KnowledgeChunk aggregate.

        Args:
            id: Identificador único del chunk
            source: Referencia al contenido fuente
            content: Texto del chunk
            position: Posición del chunk en el contenido (0-indexed)
            start_char: Índice del primer carácter en el contenido original
            end_char: Índice del último carácter en el contenido original
            token_count: Número de tokens en el chunk
            embedding: Embedding vectorial (opcional)
            summary: Summary del chunk (opcional)
            status: Estado del procesamiento
            created_at: Timestamp de creación (opcional)
            updated_at: Timestamp de última actualización (opcional)
        """
        super().__init__()

        # Identity
        self._id = id
        self._source = source

        # Contenido
        self._content = content
        self._embedding = embedding
        self._summary = summary

        # Posición en el contenido original
        self._position = position
        self._start_char = start_char
        self._end_char = end_char

        # Metadata
        self._token_count = token_count

        # Estado del procesamiento
        self._status = status

        # Timestamps
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)

        # Validar invariantes
        self._validate_invariants()

        # Emitir evento de creación si es un chunk nuevo
        if self._status == ChunkStatus.PENDING and not self._domain_events:
            self._add_domain_event(
                ChunkCreatedEvent(
                    chunk_id=str(self._id),
                    source_id=self._source.source_id,
                    source_type=self._source.source_type,
                    position=self._position,
                    token_count=int(self._token_count),
                )
            )

    # Properties

    @property
    def id(self) -> ChunkId:
        """ID único del chunk."""
        return self._id

    @property
    def source(self) -> SourceReference:
        """Referencia al contenido fuente."""
        return self._source

    @property
    def content(self) -> str:
        """Texto del chunk."""
        return self._content

    @property
    def embedding(self) -> Optional[VectorEmbedding]:
        """Embedding vectorial (solo lectura)."""
        return self._embedding

    @property
    def summary(self) -> Optional[ChunkSummary]:
        """Summary del chunk (solo lectura)."""
        return self._summary

    @property
    def position(self) -> int:
        """Posición del chunk en el contenido."""
        return self._position

    @property
    def start_char(self) -> int:
        """Índice del primer carácter."""
        return self._start_char

    @property
    def end_char(self) -> int:
        """Índice del último carácter."""
        return self._end_char

    @property
    def token_count(self) -> TokenCount:
        """Número de tokens."""
        return self._token_count

    @property
    def status(self) -> ChunkStatus:
        """Estado del procesamiento (solo lectura)."""
        return self._status

    @property
    def created_at(self) -> datetime:
        """Timestamp de creación."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Timestamp de última actualización (solo lectura)."""
        return self._updated_at

    def _validate_invariants(self) -> None:
        """
        Valida invariantes del aggregate.

        Raises:
            ValueError: Si algún invariante es violado
        """
        if not self._source:
            raise ValueError("source no puede ser None")

        if not self._content or not self._content.strip():
            raise ValueError("content no puede estar vacío")

        if self._position < 0:
            raise ValueError("position debe ser >= 0")

        if self._start_char < 0:
            raise ValueError("start_char debe ser >= 0")

        if self._end_char <= self._start_char:
            raise ValueError("end_char debe ser > start_char")

        if self._token_count.value <= 0:
            raise ValueError("token_count debe ser > 0")

    # Business logic

    def embed(self, embedding: VectorEmbedding) -> None:
        """
        Agrega embedding al chunk.

        Transición de estado: PENDING → EMBEDDED

        Args:
            embedding: VectorEmbedding a agregar

        Raises:
            ValueError: Si el chunk ya tiene embedding o no está en estado PENDING

        Examples:
            >>> chunk = KnowledgeChunk(...)
            >>> embedding = VectorEmbedding(...)
            >>> chunk.embed(embedding)
            >>> chunk.status
            <ChunkStatus.EMBEDDED: 'EMBEDDED'>
        """
        if self._embedding is not None:
            raise ValueError("Chunk already has embedding")

        if self._status != ChunkStatus.PENDING:
            raise ValueError(
                f"Cannot embed chunk in status {self._status}, " f"must be PENDING"
            )

        if embedding.dimension != 768:
            raise ValueError(
                f"Embedding must be 768 dimensions, got {embedding.dimension}"
            )

        self._embedding = embedding
        self._status = ChunkStatus.EMBEDDED
        self._updated_at = datetime.now(timezone.utc)

        self._add_domain_event(
            ChunkEmbeddedEvent(
                chunk_id=str(self._id),
                source_id=self._source.source_id,
                source_type=self._source.source_type.value,
                embedding_model=embedding.model,
                embedding_dimension=embedding.dimension,
            )
        )

    def summarize(self, summary: ChunkSummary) -> None:
        """
        Agrega summary al chunk.

        Transición de estado: EMBEDDED → SUMMARIZED

        Args:
            summary: ChunkSummary a agregar

        Raises:
            ValueError: Si el chunk no tiene embedding o no está en estado EMBEDDED

        Examples:
            >>> chunk = KnowledgeChunk(...)
            >>> chunk.embed(embedding)
            >>> summary = ChunkSummary(...)
            >>> chunk.summarize(summary)
            >>> chunk.status
            <ChunkStatus.SUMMARIZED: 'SUMMARIZED'>
        """
        if self._embedding is None:
            raise ValueError("Chunk must be embedded before summarizing")

        if self._status != ChunkStatus.EMBEDDED:
            raise ValueError(
                f"Cannot summarize chunk in status {self._status}, " f"must be EMBEDDED"
            )

        if not 3 <= summary.sentence_count <= 5:
            raise ValueError(
                f"Summary must have 3-5 sentences, got {summary.sentence_count}"
            )

        self._summary = summary
        self._status = ChunkStatus.SUMMARIZED
        self._updated_at = datetime.now(timezone.utc)

        self._add_domain_event(
            ChunkSummarizedEvent(
                chunk_id=str(self._id),
                source_id=self._source.source_id,
                source_type=self._source.source_type.value,
                sentence_count=summary.sentence_count,
                occurred_at=self._updated_at,
            )
        )

    def mark_as_completed(self) -> None:
        """
        Marca chunk como completamente procesado.

        Transición de estado: SUMMARIZED → COMPLETED

        Raises:
            ValueError: Si el chunk no tiene embedding y summary

        Examples:
            >>> chunk = KnowledgeChunk(...)
            >>> chunk.embed(embedding)
            >>> chunk.summarize(summary)
            >>> chunk.mark_as_completed()
            >>> chunk.status
            <ChunkStatus.COMPLETED: 'COMPLETED'>
        """
        if self._embedding is None or self._summary is None:
            raise ValueError("Chunk must have embedding and summary to complete")

        if self._status != ChunkStatus.SUMMARIZED:
            raise ValueError(
                f"Cannot complete chunk in status {self._status}, "
                f"must be SUMMARIZED"
            )

        self._status = ChunkStatus.COMPLETED
        self._updated_at = datetime.now(timezone.utc)

        self._add_domain_event(
            ChunkCompletedEvent(
                chunk_id=str(self._id),
                source_id=self._source.source_id,
                source_type=self._source.source_type.value,
                occurred_at=self._updated_at,
            )
        )

    def mark_as_failed(self, error_message: str) -> None:
        """
        Marca chunk como fallido.

        Puede ocurrir desde cualquier estado.

        Args:
            error_message: Mensaje de error

        Examples:
            >>> chunk = KnowledgeChunk(...)
            >>> chunk.mark_as_failed("Embedding service unavailable")
            >>> chunk.status
            <ChunkStatus.FAILED: 'FAILED'>
        """
        if not error_message or not error_message.strip():
            raise ValueError("error_message no puede estar vacío")

        self._status = ChunkStatus.FAILED
        self._updated_at = datetime.now(timezone.utc)

        self._add_domain_event(
            ChunkFailedEvent(
                chunk_id=str(self._id),
                source_id=self._source.source_id,
                source_type=self._source.source_type.value,
                error_message=error_message,
                occurred_at=self._updated_at,
            )
        )

    # Query methods

    def can_embed(self) -> bool:
        """Verifica si el chunk puede recibir embedding."""
        return self._status == ChunkStatus.PENDING and self._embedding is None

    def can_summarize(self) -> bool:
        """Verifica si el chunk puede ser summarizado."""
        return self._status == ChunkStatus.EMBEDDED and self._summary is None

    def can_complete(self) -> bool:
        """Verifica si el chunk puede ser marcado como completado."""
        return (
            self._status == ChunkStatus.SUMMARIZED
            and self._embedding is not None
            and self._summary is not None
        )

    def is_completed(self) -> bool:
        """Verifica si el chunk está completamente procesado."""
        return self._status == ChunkStatus.COMPLETED

    def is_failed(self) -> bool:
        """Verifica si el procesamiento falló."""
        return self._status == ChunkStatus.FAILED

    def has_embedding(self) -> bool:
        """Verifica si el chunk tiene embedding."""
        return self._embedding is not None

    def has_summary(self) -> bool:
        """Verifica si el chunk tiene summary."""
        return self._summary is not None

    def get_content_preview(self, max_length: int = 100) -> str:
        """
        Obtiene un preview del contenido.

        Args:
            max_length: Longitud máxima del preview

        Returns:
            Preview del contenido
        """
        if len(self._content) <= max_length:
            return self._content
        return self._content[: max_length - 3] + "..."

    def __str__(self) -> str:
        """Representación en string del chunk."""
        return (
            f"KnowledgeChunk({self._id}, pos={self._position}, status={self._status})"
        )

    def __repr__(self) -> str:
        """Representación para debugging."""
        preview = self.get_content_preview(50)
        return (
            f"KnowledgeChunk(id={self._id}, source={self._source}, "
            f"position={self._position}, status={self._status}, "
            f"has_embedding={self.has_embedding()}, has_summary={self.has_summary()}, "
            f"preview='{preview}')"
        )
