"""Interface para SmartScraperService - Selector inteligente de scrapers."""

from typing import Optional, Protocol

from src.shared.domain.value_objects import ScrapingConfiguration


class ISmartScraperService(Protocol):
    """
    Interface para SmartScraperService.

    Responsabilidad: Seleccionar inteligentemente el scraper óptimo
    (Playwright vs Trafilatura) basado en características del sitio.

    Este servicio actúa como un Strategy Pattern que decide dinámicamente
    qué scraper usar según:
    - Dominio del sitio (JS-heavy vs estático)
    - Patrones de URL
    - Fallback automático si uno falla
    """

    async def scrape_article_from_url(
        self,
        url: str,
        timeout: int = 30,
        config: Optional[ScrapingConfiguration] = None,
    ) -> Optional[str]:
        """
        Scrapea contenido eligiendo estrategia inteligentemente.

        Args:
            url: URL del artículo
            timeout: Timeout en segundos
            config: Configuración especializada (opcional)

        Returns:
            HTML scrapeado o None si ambos scrapers fallan
        """
        ...
