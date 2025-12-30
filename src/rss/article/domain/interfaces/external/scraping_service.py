"""Interface para Article Scraping Service."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class IArticleScrapingService(ABC):
    """
    Interface para servicios de web scraping de artículos.

    Responsabilidades:
    - Scrapear contenido completo desde URL del artículo
    - Manejar sitios con JavaScript dinámico
    - Extraer HTML completo renderizado
    """

    @abstractmethod
    async def scrape_article_from_url(
        self, url: str, timeout: int = 30, config: Optional[Any] = None
    ) -> Optional[str]:
        """
        Scrapea contenido completo de un artículo desde su URL.

        Args:
            url: URL del artículo a scrapear
            timeout: Timeout en segundos
            config: Configuración opcional de scraping específica

        Returns:
            HTML completo scrapeado o None si falla
        """
        pass
