"""Event Handler para ScrapingStarted.

Conecta el evento ScrapingStarted con el ScrapingPipeline.
"""

from src.scraping.app.process_managers.scraping_pipeline import ScrapingPipeline
from src.scraping.domain.events import ScrapingStarted
from src.shared.kernel.logger import ILogger


class OnScrapingStartedHandler:
    """
    Event Handler que reacciona a ScrapingStarted.

    Delega al ScrapingPipeline para iniciar el procesamiento
    de las sources.
    """

    def __init__(
        self,
        scraping_pipeline: ScrapingPipeline,
        logger: ILogger,
    ):
        self._pipeline = scraping_pipeline
        self._logger = logger.bind(
            layer="application",
            component="OnScrapingStartedHandler",
        )

    async def handle(self, event: ScrapingStarted) -> None:
        """
        Maneja el evento ScrapingStarted.

        Args:
            event: Evento de scraping iniciado
        """
        self._logger.info(
            "Evento ScrapingStarted recibido",
            scraping_id=event.scraping_id,
            sources_count=event.sources_count,
        )

        await self._pipeline.on_scraping_started(event)
