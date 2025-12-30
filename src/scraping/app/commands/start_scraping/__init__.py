"""StartScraping command - Inicia scraping de sources RSS.

Este comando inicia el pipeline de scraping:
1. Handler valida y crea sesión
2. Emite evento ScrapingStarted
3. ScrapingPipeline escucha y coordina el resto

Uso:
    >>> from src.scraping.app.commands.start_scraping import (
    ...     StartScrapingCommand,
    ...     StartScrapingHandler,
    ...     StartScrapingResult,
    ... )
    >>>
    >>> # Scrapear sources específicas
    >>> command = StartScrapingCommand(source_ids=["src-1", "src-2"])
    >>>
    >>> # Scrapear todas las activas
    >>> command = StartScrapingCommand()
    >>>
    >>> result = await handler.handle(command)
"""

from src.scraping.app.commands.start_scraping.command import StartScrapingCommand
from src.scraping.app.commands.start_scraping.exception import (
    NoSourcesAvailableError,
    ScrapingSessionCreationError,
    StartScrapingError,
    StartScrapingValidationError,
)
from src.scraping.app.commands.start_scraping.handler import StartScrapingHandler
from src.scraping.app.commands.start_scraping.result import StartScrapingResult
from src.scraping.app.commands.start_scraping.validator import StartScrapingValidator

__all__ = [
    "StartScrapingCommand",
    "StartScrapingHandler",
    "StartScrapingResult",
    "StartScrapingValidator",
    "StartScrapingError",
    "StartScrapingValidationError",
    "NoSourcesAvailableError",
    "ScrapingSessionCreationError",
]
