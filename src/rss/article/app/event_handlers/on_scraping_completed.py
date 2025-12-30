"""Event Handler para ScrapingCompleted (cross-bounded-context).

Conecta el evento ScrapingCompleted del bounded context Scraping
con el ContentExtractionInitiator del bounded context Article.

ARQUITECTURA: Process Manager (Escuela 2)
- Event Handler liviano (solo delegación)
- Process Manager coordina el inicio del procesamiento
"""

from src.rss.article.app.process_managers.content_extraction_initiator import (
    ContentExtractionInitiator,
)
from src.scraping.domain.events import ScrapingCompleted
from src.shared.kernel.logger import ILogger


class OnScrapingCompletedHandler:
    """
    Event Handler que reacciona a ScrapingCompleted.

    Este es un handler cross-bounded-context liviano:
    - Escucha eventos del bounded context Scraping
    - Delega al ContentExtractionInitiator (Process Manager)

    Sigue Escuela 2: Event Handler solo delega, no coordina.
    """

    def __init__(
        self,
        content_extraction_initiator: ContentExtractionInitiator,
        logger: ILogger,
    ):
        self._initiator = content_extraction_initiator
        self._logger = logger.bind(
            layer="application",
            component="OnScrapingCompletedHandler",
        )

    async def handle(self, event: ScrapingCompleted) -> None:
        """
        Maneja el evento ScrapingCompleted.

        Delega al ContentExtractionInitiator para iniciar procesamiento.

        Args:
            event: Evento de scraping completado
        """
        self._logger.info(
            "Evento ScrapingCompleted recibido (cross-BC)",
            scraping_id=event.scraping_id,
            articles_new=event.articles_new,
        )

        await self._initiator.on_scraping_completed(event)
