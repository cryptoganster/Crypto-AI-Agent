"""Command para convertir contenido HTML de artículo a formato Markdown."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ConvertArticleToMarkdownCommand:
    """
    Command para convertir contenido HTML procesado a formato Markdown.

    DTO puro - solo primitivos (CQRS).

    Event-Driven Architecture:
    - Recibe datos del evento ArticlePlaintextExtracted
    - No requiere lectura del aggregate (CQRS puro)
    """

    article_id: str  # UUID del artículo a convertir

    # Event-Driven: Datos del evento anterior
    html_content: Optional[str] = None  # Del evento ArticlePlaintextExtracted
    plaintext: Optional[str] = None  # Del evento ArticlePlaintextExtracted
    article_url: Optional[str] = None  # Para logging
    article_title: Optional[str] = None  # Para logging
