"""ArticleQualityCalculated domain event."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ArticleQualityCalculated(IDomainEvent):
    """
    Evento emitido cuando la calidad del artículo es calculada.

    Este evento indica que el score de calidad final ha sido
    calculado para el artículo (último paso del análisis).

    Attributes:
        article_id: ID del artículo procesado
        success: Si el cálculo fue exitoso
        quality_score: Score de calidad (0.0 - 1.0)
        error_message: Mensaje de error si falló
        occurred_at: Timestamp del evento
    """

    article_id: str
    success: bool
    quality_score: Optional[float] = None
    error_message: Optional[str] = None
    occurred_at: datetime = None

    def __post_init__(self):
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
