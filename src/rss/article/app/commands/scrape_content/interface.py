"""Interface para el handler de scraping de artículos."""

from typing import Protocol

from .command import ScrapeArticleContentCommand
from .result import ScrapeArticleContentResult


class IScrapeArticleContentHandler(Protocol):
    """Interface para el handler de scraping de contenido de artículos."""

    async def handle(
        self, command: ScrapeArticleContentCommand
    ) -> ScrapeArticleContentResult:
        """Ejecuta el scraping de contenido de un artículo."""
        ...
