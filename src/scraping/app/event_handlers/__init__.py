"""Event Handlers del bounded context Scraping.

Los Event Handlers conectan Domain Events con Process Managers
y otros componentes que necesitan reaccionar a eventos.

Handlers:
- OnScrapingStartedHandler: Inicia el ScrapingPipeline
- OnSourceScrapedHandler: Actualiza progreso del pipeline
"""

from src.scraping.app.event_handlers.on_scraping_started import (
    OnScrapingStartedHandler,
)
from src.scraping.app.event_handlers.on_source_scraped import (
    OnSourceScrapedHandler,
)

__all__ = [
    "OnScrapingStartedHandler",
    "OnSourceScrapedHandler",
]
