"""ArticleMarkdownConverted domain event."""

from dataclasses import dataclass
from datetime import datetime, timezone

from src.shared.kernel.domain_event import IDomainEvent


@dataclass(frozen=True)
class ArticleMarkdownConverted(IDomainEvent):
    """
    Evento emitido cuando el contenido fue convertido exitosamente a Markdown.

    Este evento representa un HECHO que ya ocurrió: el HTML procesado
    ha sido convertido a formato Markdown para presentación en UI.

    Solo se emite cuando la conversión es exitosa.

    Event-Driven Architecture:
    - Incluye markdown y plaintext para que CalculateArticleMetricsHandler
      no necesite leer el aggregate.
    - Sigue el patrón de eventos enriquecidos para desacoplar lectura/escritura.

    Attributes:
        article_id: ID del artículo procesado
        markdown_length: Longitud del markdown generado
        markdown_content: Contenido markdown (para siguiente paso)
        plaintext: Texto plano (para cálculo de métricas)
        article_url: URL del artículo (para logging)
        article_title: Título del artículo (para logging)
        occurred_at: Timestamp del evento
    """

    article_id: str
    markdown_length: int
    markdown_content: str = None  # ← NUEVO: Para siguiente handler
    plaintext: str = None  # ← NUEVO: Para cálculo de métricas
    article_url: str = None  # ← NUEVO: Para logging
    article_title: str = None  # ← NUEVO: Para logging
    occurred_at: datetime = None

    def __post_init__(self):
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now(timezone.utc))
