"""Service interfaces para Scraping bounded context."""

from .scraping_orchestrator import FetchResult, IScrapingCoordinator

__all__ = [
    "IScrapingCoordinator",
    "FetchResult",
]
