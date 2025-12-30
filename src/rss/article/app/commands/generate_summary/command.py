"""Command para generar summary de artículo."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GenerateArticleSummaryCommand:
    """
    Command para generar summary de artículo RSS.

    Extrae fragmentos relevantes del contenido usando extractive summarization.

    CQRS: Solo primitivos, sin lógica de negocio.

    Event-Driven Architecture:
    - Recibe datos del evento ArticleLanguageDetected
    - No requiere lectura del aggregate (CQRS puro)
    """

    article_id: str
    """ID del artículo a procesar."""

    summary_length: int = 500
    """Longitud máxima del summary en caracteres."""

    force_regenerate: bool = False
    """Si True, regenera aunque ya exista summary."""

    update_article: bool = True
    """Si True, actualiza los campos en el repositorio."""

    correlation_id: Optional[str] = None
    """ID de correlación para trazabilidad."""

    # Event-Driven: Datos del evento anterior
    plaintext: Optional[str] = None
    """Texto plano del evento anterior."""

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

        if self.summary_length <= 0:
            raise ValueError("summary_length debe ser positivo")
