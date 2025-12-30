"""Comando ScrapeSource - Scrapea una única source RSS.

Este es un comando simple que sigue CQRS estricto:
- Un agregado (Source)
- Una operación (scrape)
- Emite evento al completar
"""

from src.scraping.app.commands.scrape_source.command import ScrapeSourceCommand
from src.scraping.app.commands.scrape_source.handler import ScrapeSourceHandler
from src.scraping.app.commands.scrape_source.result import ScrapeSourceResult

__all__ = [
    "ScrapeSourceCommand",
    "ScrapeSourceHandler",
    "ScrapeSourceResult",
]
