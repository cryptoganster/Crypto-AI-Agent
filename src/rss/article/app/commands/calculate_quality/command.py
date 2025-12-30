"""CalculateArticleQuality command - Application Layer."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class CalculateArticleQualityCommand:
    """
    Command para calcular quality (score + level) de un artículo RSS.

    DTO inmutable con solo primitivos (CQRS puro).

    Event-Driven Architecture:
    - Recibe datos del evento ArticleKeywordsExtracted
    - No requiere lectura del aggregate (CQRS puro)
    """

    article_id: str
    force_recalculate: bool = False
    update_article: bool = True
    correlation_id: Optional[str] = None

    # Event-Driven: Datos del evento anterior
    plaintext: Optional[str] = None
    """Texto plano para cálculo de calidad."""

    keywords: Optional[List[str]] = None
    """Keywords extraídos del evento ArticleKeywordsExtracted."""

    word_count: Optional[int] = None
    """Word count del evento anterior."""

    article_url: Optional[str] = None
    """URL para logging."""

    article_title: Optional[str] = None
    """Título para logging."""
