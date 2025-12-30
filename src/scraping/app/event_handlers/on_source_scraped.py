"""Event Handler para SourceScraped.

Conecta el evento SourceScraped con el ScrapingPipeline.
"""

from src.scraping.app.process_managers.scraping_pipeline import ScrapingPipeline
from src.scraping.domain.events import SourceScraped
from src.shared.kernel.logger import ILogger


class OnSourceScrapedHandler:
    """
    Event Handler que reacciona a SourceScraped.

    Delega al ScrapingPipeline para actualizar el estado
    y verificar si el pipeline está completo.
    """

    def __init__(
        self,
        scraping_pipeline: ScrapingPipeline,
        logger: ILogger,
    ):
        self._pipeline = scraping_pipeline
        self._logger = logger.bind(
            layer="application",
            component="OnSourceScrapedHandler",
        )

    async def handle(self, event: SourceScraped) -> None:
        """
        Maneja el evento SourceScraped.

        Args:
            event: Evento de source scrapeada
        """
        self._logger.debug(
            "Evento SourceScraped recibido",
            scraping_id=event.scraping_id,
            source_id=event.source_id,
            success=event.success,
        )

        await self._pipeline.on_source_scraped(event)
