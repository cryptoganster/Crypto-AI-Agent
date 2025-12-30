"""ChunkCreatedEvent - Evento cuando se crea un ContentChunk."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ChunkCreatedEvent(IDomainEvent):
    """
    Evento emitido cuando se crea un ContentChunk.

    Attributes:
        chunk_id: ID del chunk creado
        source_id: ID del contenido fuente
        source_type: Tipo de fuente (RSS_ARTICLE, DOCUMENT, etc.)
        position: Posición del chunk en el contenido
        token_count: Número de tokens en el chunk
        occurred_at: Timestamp del evento
    """

    chunk_id: str
    source_id: str
    source_type: str
    position: int
    token_count: int
    occurred_at: datetime = field(default=None)

    def __post_init__(self):
        """Valida el evento y genera timestamp."""
        if not self.chunk_id:
            raise ValueError("chunk_id no puede estar vacío")
        if not self.source_id:
            raise ValueError("source_id no puede estar vacío")
        if not self.source_type:
            raise ValueError("source_type no puede estar vacío")
        if self.position < 0:
            raise ValueError("position debe ser >= 0")
        if self.token_count <= 0:
            raise ValueError("token_count debe ser > 0")

        # Generar timestamp si no se proporciona
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
