"""ArticleSummaryGenerated domain event."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ArticleSummaryGenerated(IDomainEvent):
    """
    Evento emitido cuando el resumen del artículo es generado.

    Este evento indica que un resumen automático ha sido
    generado para el artículo.

    Event-Driven Architecture:
    - Incluye plaintext y summary para que ExtractArticleKeywordsHandler
      no necesite leer el aggregate.
    - Sigue el patrón de eventos enriquecidos para desacoplar lectura/escritura.

    Attributes:
        article_id: ID del artículo procesado
        success: Si la generación fue exitosa
        summary_length: Longitud del resumen generado
        error_message: Mensaje de error si falló
        summary: Resumen generado (para siguiente paso)
        plaintext: Texto plano (para extracción de keywords)
        article_url: URL del artículo (para logging)
        article_title: Título del artículo (para logging)
        occurred_at: Timestamp del evento
    """

    article_id: str
    success: bool
    summary_length: Optional[int] = None
    error_message: Optional[str] = None
    summary: Optional[str] = None  # ← NUEVO: Para siguiente handler
    plaintext: Optional[str] = None  # ← NUEVO: Para extracción keywords
    article_url: Optional[str] = None  # ← NUEVO: Para logging
    article_title: Optional[str] = None  # ← NUEVO: Para logging
    occurred_at: datetime = None

    def __post_init__(self):
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
