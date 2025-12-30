"""Scraping persistence infrastructure."""

from src.scraping.infra.persistence.models import ScrapingModel
from src.scraping.infra.persistence.repositories import ScrapingWriteRepository

__all__ = ["ScrapingModel", "ScrapingWriteRepository"]
