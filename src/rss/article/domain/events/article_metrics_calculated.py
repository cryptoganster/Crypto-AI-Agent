"""ArticleMetricsCalculated domain event."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ArticleMetricsCalculated(IDomainEvent):
    """
    Evento emitido cuando las métricas del artículo son calculadas.

    Este evento indica que métricas básicas (word_count, reading_time)
    han sido calculadas para el artículo.

    Event-Driven Architecture:
    - Incluye plaintext para que DetectArticleLanguageHandler
      no necesite leer el aggregate.
    - Sigue el patrón de eventos enriquecidos para desacoplar lectura/escritura.

    Attributes:
        article_id: ID del artículo procesado
        success: Si el cálculo fue exitoso
        word_count: Número de palabras
        reading_time_minutes: Tiempo estimado de lectura
        error_message: Mensaje de error si falló
        plaintext: Texto plano (para detección de idioma)
        article_url: URL del artículo (para logging)
        article_title: Título del artículo (para logging)
        occurred_at: Timestamp del evento
    """

    article_id: str
    success: bool
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    error_message: Optional[str] = None
    plaintext: Optional[str] = None  # ← NUEVO: Para siguiente handler
    article_url: Optional[str] = None  # ← NUEVO: Para logging
    article_title: Optional[str] = None  # ← NUEVO: Para logging
    occurred_at: datetime = None

    def __post_init__(self):
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
