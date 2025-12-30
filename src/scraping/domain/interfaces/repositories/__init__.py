"""Repository interfaces - Scraping Bounded Context."""

from .scraping_read_repository import IScrapingReadRepository
from .scraping_write_repository import IScrapingWriteRepository

__all__ = [
    "IScrapingReadRepository",
    "IScrapingWriteRepository",
]
