"""Scraping commands.

Comandos CQRS para el bounded context de Scraping.

ARQUITECTURA EVENT-DRIVEN:
1. StartScrapingCommand → StartScrapingHandler → ScrapingStarted event
2. ScrapingPipeline escucha → emite ScrapeSourceCommand por cada source
3. ScrapeSourceHandler → SourceScraped event
4. ScrapingPipeline escucha → cuando todas completan → ScrapingCompleted event

COMANDOS PRINCIPALES:
- StartScrapingCommand: Inicia scraping (emite evento, no hace scraping)
- ScrapeSourceCommand: Scrapea 1 source (comando simple CQRS)
- UpdateScrapingConfigCommand: Actualiza configuración de scraping

Uso:
    >>> from src.scraping.app.commands import (
    ...     StartScrapingCommand,
    ...     ScrapeSourceCommand,
    ... )
    >>>
    >>> # Scrapear sources específicas
    >>> command = StartScrapingCommand(source_ids=["src-1", "src-2"])
    >>>
    >>> # Scrapear todas las activas con opciones
    >>> command = StartScrapingCommand(
    ...     quality_threshold=0.7,
    ...     enable_deduplication=True,
    ... )
"""

from src.scraping.app.commands.scrape_source.command import ScrapeSourceCommand
from src.scraping.app.commands.scrape_source.handler import ScrapeSourceHandler
from src.scraping.app.commands.scrape_source.result import ScrapeSourceResult

# =============================================================================
# COMANDOS PRINCIPALES (EVENT-DRIVEN)
# =============================================================================
from src.scraping.app.commands.start_scraping import (
    StartScrapingCommand,
    StartScrapingHandler,
    StartScrapingResult,
    StartScrapingValidator,
)

# UpdateScrapingConfig (activo)
from src.scraping.app.commands.update_scraping_config.command import (
    UpdateScrapingConfigCommand,
)
from src.scraping.app.commands.update_scraping_config.handler import (
    UpdateScrapingConfigHandler,
)
from src.scraping.app.commands.update_scraping_config.result import (
    UpdateScrapingConfigResult,
)
from src.scraping.app.commands.update_scraping_config.validator import (
    UpdateScrapingConfigValidator,
)

__all__ = [
    # Comandos principales (event-driven)
    "StartScrapingCommand",
    "StartScrapingHandler",
    "StartScrapingResult",
    "StartScrapingValidator",
    "ScrapeSourceCommand",
    "ScrapeSourceHandler",
    "ScrapeSourceResult",
    # Update Scraping Config
    "UpdateScrapingConfigCommand",
    "UpdateScrapingConfigHandler",
    "UpdateScrapingConfigValidator",
    "UpdateScrapingConfigResult",
]
