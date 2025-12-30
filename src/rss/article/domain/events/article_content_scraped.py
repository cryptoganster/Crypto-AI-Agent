"""ArticleContentScraped domain event."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ArticleContentScraped(IDomainEvent):
    """
    Evento emitido cuando el contenido de un artículo es scrapeado.

    Este evento indica que el HTML del artículo ha sido descargado
    desde su URL original.

    Event-Driven Architecture:
    - Incluye el contenido HTML completo para que el siguiente handler
      (ExtractArticlePlaintextHandler) no necesite leer el aggregate.
    - Sigue el patrón de eventos enriquecidos para desacoplar lectura/escritura.

    Attributes:
        article_id: ID del artículo scrapeado
        success: Si el scraping fue exitoso
        content_length: Longitud del contenido scrapeado (si exitoso)
        scraper_used: Tipo de scraper utilizado
        error_message: Mensaje de error si falló
        html_content: Contenido HTML scrapeado (para siguiente paso)
        article_url: URL del artículo (para logging)
        article_title: Título del artículo (para logging)
        occurred_at: Timestamp del evento
    """

    article_id: str
    success: bool
    content_length: Optional[int] = None
    scraper_used: Optional[str] = None
    error_message: Optional[str] = None
    html_content: Optional[str] = None  # ← NUEVO: Para siguiente handler
    article_url: Optional[str] = None  # ← NUEVO: Para logging
    article_title: Optional[str] = None  # ← NUEVO: Para logging
    occurred_at: datetime = None

    def __post_init__(self):
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
