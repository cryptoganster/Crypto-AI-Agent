"""ChunkEmbeddedEvent - Evento cuando se agrega embedding a un ContentChunk."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ChunkEmbeddedEvent(IDomainEvent):
    """
    Evento emitido cuando se agrega embedding a un ContentChunk.

    Attributes:
        chunk_id: ID del chunk
        source_id: ID del contenido fuente
        source_type: Tipo de fuente (RSS_ARTICLE, DOCUMENT, etc.)
        embedding_model: Modelo usado para generar el embedding
        embedding_dimension: Dimensión del embedding
        occurred_at: Timestamp del evento
    """

    chunk_id: str
    source_id: str
    source_type: str
    embedding_model: str
    embedding_dimension: int
    occurred_at: datetime = field(default=None)

    def __post_init__(self):
        """Valida el evento y genera timestamp."""
        if not self.chunk_id:
            raise ValueError("chunk_id no puede estar vacío")
        if not self.source_id:
            raise ValueError("source_id no puede estar vacío")
        if not self.source_type:
            raise ValueError("source_type no puede estar vacío")
        if not self.embedding_model:
            raise ValueError("embedding_model no puede estar vacío")
        if self.embedding_dimension <= 0:
            raise ValueError("embedding_dimension debe ser > 0")

        # Generar timestamp si no se proporciona
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
