"""Trafilatura Scraper Service - Article Bounded Context."""

import asyncio
from typing import Any, Optional

import aiohttp
import trafilatura

from src.rss.article.domain.interfaces.external import IArticleScrapingService
from src.shared.kernel.logger import ILogger


class TrafilaturaScraperService(IArticleScrapingService):
    """
    Servicio de scraping con trafilatura para sitios HTML estáticos.

    Características:
    - Muy rápido (10x más que Playwright)
    - Ideal para noticias tradicionales
    - NO ejecuta JavaScript
    """

    def __init__(
        self,
        logger: Optional[ILogger] = None,
        user_agent: str = "Mozilla/5.0 (compatible; FeedsAI/1.0)",
    ):
        self._logger = (
            logger.bind(component="TrafilaturaScraperService") if logger else None
        )
        self._user_agent = user_agent

    async def scrape_article_from_url(
        self, url: str, timeout: int = 30, config: Optional[Any] = None
    ) -> Optional[str]:
        """Scrapea contenido usando trafilatura."""
        from src.rss.article.domain.value_objects import ArticleUrl

        if isinstance(url, ArticleUrl):
            url = url.value

        if self._logger:
            self._logger.info(
                f"📄 Trafilatura: Iniciando scraping | URL: {url} | Timeout: {timeout}s"
            )

        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            url_str = str(url) if not isinstance(url, str) else url

            async with aiohttp.ClientSession(
                timeout=timeout_obj, headers=headers
            ) as session:
                async with session.get(url_str) as response:
                    response.raise_for_status()
                    html = await response.text()

            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_images=True,
                output_format="html",
                target_language="es",
                favor_precision=True,
            )

            if not extracted:
                if self._logger:
                    self._logger.warning(
                        "⚠️ Trafilatura returned EMPTY content", url=url
                    )
                return None

            if self._logger:
                self._logger.info(
                    "✅ Trafilatura extraction successful",
                    url=url,
                    extracted_length=len(extracted),
                )

            return extracted

        except aiohttp.ClientError as e:
            if self._logger:
                self._logger.exception("HTTP error scraping", url=url, error=str(e))
            return None

        except asyncio.TimeoutError:
            if self._logger:
                self._logger.exception("Timeout scraping", url=url, timeout=timeout)
            return None

        except Exception as e:
            if self._logger:
                self._logger.error(f"❌ ERROR scraping | URL: {url} | Error: {e}")
            return None
