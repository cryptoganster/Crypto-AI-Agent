"""ArticleAIProcessedEvent - Evento cuando un artículo completa el procesamiento AI."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ArticleAIProcessedEvent(IDomainEvent):
    """
    Evento emitido cuando un artículo completa el procesamiento AI completo.

    Este evento se emite después de que todos los chunks han sido:
    - Creados
    - Embeddeados
    - Summarizados
    - Persistidos

    Attributes:
        article_id: ID del artículo procesado
        chunks_created: Número de chunks creados
        total_tokens: Total de tokens procesados
        has_global_summary: Si se generó summary global
        has_tldr: Si se generó TLDR
        success: Si el procesamiento fue exitoso
        error_message: Mensaje de error (si falló)
        occurred_at: Timestamp del evento

    Requirements: 10.4
    """

    article_id: str
    chunks_created: int
    total_tokens: int
    has_global_summary: bool = False
    has_tldr: bool = False
    success: bool = True
    error_message: str = None
    occurred_at: datetime = field(default=None)

    def __post_init__(self):
        """Valida el evento y genera timestamp."""
        if not self.article_id:
            raise ValueError("article_id no puede estar vacío")
        if self.chunks_created < 0:
            raise ValueError("chunks_created debe ser >= 0")
        if self.total_tokens < 0:
            raise ValueError("total_tokens debe ser >= 0")

        # Generar timestamp si no se proporciona
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
