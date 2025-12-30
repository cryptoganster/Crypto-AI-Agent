"""ChunkSummarizedEvent - Evento cuando se agrega summary a un ContentChunk."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ChunkSummarizedEvent(IDomainEvent):
    """
    Evento emitido cuando se agrega summary a un ContentChunk.

    Attributes:
        chunk_id: ID del chunk
        source_id: ID del contenido fuente
        source_type: Tipo de fuente (RSS_ARTICLE, DOCUMENT, etc.)
        sentence_count: Número de frases en el summary
        occurred_at: Timestamp del evento
    """

    chunk_id: str
    source_id: str
    source_type: str
    sentence_count: int
    occurred_at: datetime = field(default=None)

    def __post_init__(self):
        """Valida el evento y genera timestamp."""
        if not self.chunk_id:
            raise ValueError("chunk_id no puede estar vacío")
        if not self.source_id:
            raise ValueError("source_id no puede estar vacío")
        if not self.source_type:
            raise ValueError("source_type no puede estar vacío")
        if not 3 <= self.sentence_count <= 5:
            raise ValueError("sentence_count debe estar entre 3 y 5")

        # Generar timestamp si no se proporciona
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
