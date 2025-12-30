"""Entities del bounded context de Scraping."""

from .scraping_manager import ScrapingManager
from .scraping_record import ScrapingId, ScrapingRecord, ScrapingRecordStatus

__all__ = [
    "ScrapingId",
    "ScrapingRecord",
    "ScrapingRecordStatus",
    "ScrapingManager",
]
