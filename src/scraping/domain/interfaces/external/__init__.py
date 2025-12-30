"""External interfaces para Scraping bounded context.

Interfaces para servicios de infraestructura externos al dominio.
"""

from src.scraping.domain.interfaces.external.rss_feed_fetcher import (
    ArticleData,
    FetchResult,
    IRssFeedFetcherService,
)

__all__ = [
    "ArticleData",
    "FetchResult",
    "IRssFeedFetcherService",
]
