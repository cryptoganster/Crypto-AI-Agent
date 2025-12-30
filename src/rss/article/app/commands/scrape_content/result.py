"""Result para ScrapeArticleContent command."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ScrapeArticleContentResult:
    """
    Resultado inmutable del comando ScrapeArticleContent.

    Atributos:
        success: Si el scraping fue exitoso
        article_id: ID del artículo procesado
        content_length: Tamaño del contenido scrapeado (caracteres)
        scraper_used: Nombre del scraper utilizado
        was_cached: Si ya tenía content_scrapped y no se rescrapeó
        error_message: Mensaje de error si falló
    """

    success: bool
    article_id: str
    content_length: Optional[int] = None
    scraper_used: Optional[str] = None
    was_cached: bool = False
    error_message: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        article_id: str,
        content_length: int,
        scraper_used: str,
        was_cached: bool = False,
    ) -> "ScrapeArticleContentResult":
        """Factory para resultado exitoso."""
        return cls(
            success=True,
            article_id=article_id,
            content_length=content_length,
            scraper_used=scraper_used,
            was_cached=was_cached,
        )

    @classmethod
    def failure_result(
        cls, article_id: str, error_message: str
    ) -> "ScrapeArticleContentResult":
        """Factory para resultado fallido."""
        return cls(success=False, article_id=article_id, error_message=error_message)
