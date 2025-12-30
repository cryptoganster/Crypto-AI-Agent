"""Command para calcular métricas de artículo (word_count, reading_time)."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CalculateArticleMetricsCommand:
    """
    Command para calcular métricas de contenido de un artículo RSS.

    DTO inmutable que representa la intención de calcular:
    - word_count (número de palabras)
    - reading_time_minutes (tiempo estimado de lectura)

    CQRS: Solo primitivos, sin lógica de negocio.

    Event-Driven Architecture:
    - Recibe datos del evento ArticleMarkdownConverted
    - No requiere lectura del aggregate (CQRS puro)
    """

    article_id: str
    """ID del artículo a analizar."""

    force_recalculate: bool = False
    """Si True, recalcula aunque ya existan métricas."""

    update_article: bool = True
    """Si True, actualiza los campos del artículo en el repositorio."""

    correlation_id: Optional[str] = None
    """ID de correlación para trazabilidad."""

    # Event-Driven: Datos del evento anterior
    plaintext: Optional[str] = None
    """Texto plano del evento ArticleMarkdownConverted."""

    markdown_content: Optional[str] = None
    """Contenido markdown del evento ArticleMarkdownConverted."""

    article_url: Optional[str] = None
    """URL para logging."""

    article_title: Optional[str] = None
    """Título para logging."""

    def __post_init__(self):
        """Validación básica de primitivos."""
        if not self.article_id:
            raise ValueError("article_id es requerido")

        if not isinstance(self.article_id, str):
            raise TypeError("article_id debe ser string")
