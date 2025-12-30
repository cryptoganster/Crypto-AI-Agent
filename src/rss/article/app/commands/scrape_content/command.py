"""Command para scrapear contenido completo de un artículo."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ScrapeArticleContentCommand:
    """
    Command para scrapear contenido completo desde la URL del artículo.

    Atributos:
        article_id: ID del artículo a scrapear
        force_rescrape: Si True, scrapea aunque ya tenga content_scrapped
        update_article: Si True, actualiza el aggregate y persiste
        timeout_seconds: Timeout para el scraping
        use_smart_scraper: Si True, usa SmartScraperService (auto-selector)
    """

    article_id: str
    force_rescrape: bool = False
    update_article: bool = True
    timeout_seconds: int = 30
    use_smart_scraper: bool = True
