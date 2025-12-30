"""ArticlePlaintextExtracted domain event."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ArticlePlaintextExtracted(IDomainEvent):
    """
    Evento emitido cuando el texto plano es extraído del HTML.

    Este evento indica que el contenido HTML ha sido procesado
    y convertido a texto plano para análisis NLP.

    Event-Driven Architecture:
    - Incluye plaintext y HTML para que ConvertArticleToMarkdownHandler
      no necesite leer el aggregate.
    - Sigue el patrón de eventos enriquecidos para desacoplar lectura/escritura.

    Attributes:
        article_id: ID del artículo procesado
        success: Si la extracción fue exitosa
        plaintext_length: Longitud del texto plano extraído
        error_message: Mensaje de error si falló
        plaintext: Texto plano extraído (para siguiente paso)
        html_content: HTML procesado (para conversión a markdown)
        article_url: URL del artículo (para logging)
        article_title: Título del artículo (para logging)
        occurred_at: Timestamp del evento
    """

    article_id: str
    success: bool
    plaintext_length: Optional[int] = None
    error_message: Optional[str] = None
    plaintext: Optional[str] = None  # ← NUEVO: Para siguiente handler
    html_content: Optional[str] = None  # ← NUEVO: Para conversión markdown
    article_url: Optional[str] = None  # ← NUEVO: Para logging
    article_title: Optional[str] = None  # ← NUEVO: Para logging
    occurred_at: datetime = None

    def __post_init__(self):
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
