"""Command para detectar idioma de un artículo."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class DetectArticleLanguageCommand:
    """
    Command CQRS para detectar idioma de artículo.

    RESPONSABILIDAD ÚNICA: Detectar idioma usando ArticleLanguageDetectionService
    y persistir en article.metadata.language.code.

    Event-Driven Architecture:
    - Recibe datos del evento ArticleMetricsCalculated
    - No requiere lectura del aggregate (CQRS puro)
    """

    article_id: UUID
    override_existing: bool = False  # Si True, detecta aunque ya tenga language
    correlation_id: str = ""
    triggered_by: str = "system"

    # Event-Driven: Datos del evento anterior
    plaintext: Optional[str] = None
    """Texto plano del evento ArticleMetricsCalculated."""

    article_url: Optional[str] = None
    """URL para logging."""

    article_title: Optional[str] = None
    """Título para logging."""
