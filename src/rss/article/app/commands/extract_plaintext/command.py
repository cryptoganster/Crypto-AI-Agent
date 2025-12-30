"""Command para extraer texto plano de artículos."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExtractArticlePlaintextCommand:
    """
    Command para extraer texto plano desde HTML scrapeado.

    CQRS Command Pattern: Inmutable, solo primitivos.

    Event-Driven Architecture:
    - Recibe datos del evento ArticleContentScraped
    - No requiere lectura del aggregate (CQRS puro)

    Pipeline: Fase 2 (después de Scraping, antes de Markdown)
    Input: content_scrapped (HTML)
    Output: content_plaintext (texto puro para NLP)
    """

    article_id: str
    override_existing: bool = False  # Si True, re-extrae aunque ya exista

    # Event-Driven: Datos del evento anterior
    html_content: Optional[str] = None  # Del evento ArticleContentScraped
    article_url: Optional[str] = None  # Para logging
    article_title: Optional[str] = None  # Para logging
