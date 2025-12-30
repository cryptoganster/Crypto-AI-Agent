"""ChunkFailedEvent - Evento cuando falla el procesamiento de un ContentChunk."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ChunkFailedEvent(IDomainEvent):
    """
    Evento emitido cuando falla el procesamiento de un ContentChunk.

    Attributes:
        chunk_id: ID del chunk
        source_id: ID del contenido fuente
        source_type: Tipo de fuente (RSS_ARTICLE, DOCUMENT, etc.)
        error_message: Mensaje de error
        occurred_at: Timestamp del evento
    """

    chunk_id: str
    source_id: str
    source_type: str
    error_message: str
    occurred_at: datetime = field(default=None)

    def __post_init__(self):
        """Valida el evento y genera timestamp."""
        if not self.chunk_id:
            raise ValueError("chunk_id no puede estar vacío")
        if not self.source_id:
            raise ValueError("source_id no puede estar vacío")
        if not self.source_type:
            raise ValueError("source_type no puede estar vacío")
        if not self.error_message:
            raise ValueError("error_message no puede estar vacío")

        # Generar timestamp si no se proporciona
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
