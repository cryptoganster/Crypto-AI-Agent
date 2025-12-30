"""Smart Scraper Service - Auto-selector de scraper óptimo.

Domain Service del bounded context Article.
Migrado desde src/domain/services/articles/smart_scraper_service.py
"""

from typing import Optional

from src.rss.article.domain.interfaces.external import IArticleScrapingService
from src.rss.article.domain.interfaces.services import ISmartScraperService
from src.rss.article.domain.value_objects import (
    ArticleUrl,
    JavaScriptDomainRegistry,
    MinimumContentLength,
    ScrapingDecision,
    ScrappedHtml,
    UrlPatternCollection,
)
from src.shared.domain.value_objects import ScrapingConfiguration


class SmartScraperService(ISmartScraperService):
    """
    Servicio inteligente que auto-selecciona el mejor scraper.

    Domain Service del bounded context Article.
    Implementa ISmartScraperService.

    Responsabilidades:
    - Detecta si el sitio requiere JavaScript
    - Usa Playwright para sitios dinámicos (SPAs)
    - Usa trafilatura para sitios estáticos (más rápido)
    - Fallback automático si uno falla

    Estrategia de decisión:
    1. Dominio en registry de JS-heavy sites → Playwright
    2. URL patterns que indican JavaScript → Playwright
    3. Default: Trafilatura con fallback a Playwright
    """

    def __init__(
        self,
        playwright_scraper: IArticleScrapingService,
        trafilatura_scraper: IArticleScrapingService,
        js_domain_registry: Optional[JavaScriptDomainRegistry] = None,
        url_pattern_collection: Optional[UrlPatternCollection] = None,
        min_content_length: Optional[MinimumContentLength] = None,
    ):
        """
        Inicializa smart scraper con Value Objects.

        Args:
            playwright_scraper: Scraper con JavaScript support
            trafilatura_scraper: Scraper para HTML estático
            js_domain_registry: Registry de dominios JS (usa default si None)
            url_pattern_collection: Patrones URL JS (usa default si None)
            min_content_length: Longitud mínima contenido (usa standard si None)
        """
        self._playwright = playwright_scraper
        self._trafilatura = trafilatura_scraper

        # VOs para detección de JavaScript
        self._js_domains = js_domain_registry or JavaScriptDomainRegistry.default()
        self._url_patterns = url_pattern_collection or UrlPatternCollection.default()
        self._min_content_length = min_content_length or MinimumContentLength.standard()

    async def scrape_article_from_url(
        self,
        url: str,
        timeout: int = 30,
        config: Optional[ScrapingConfiguration] = None,
    ) -> Optional[str]:
        """
        Scrapea contenido de artículo eligiendo estrategia inteligentemente.

        Args:
            url: URL del artículo
            timeout: Timeout en segundos
            config: Configuración especializada (si None, usa decisión automática)

        Returns:
            HTML scrapeado o None si ambos fallan
        """
        # Convertir URL a string si es ArticleUrl VO
        url_str = str(url) if not isinstance(url, str) else url

        # 1. Tomar decisión de scraping usando VOs
        decision = self._make_scraping_decision(url_str)

        # Logging básico de decisión (sin dependencia de ILogger)
        url_preview = url_str[:80] + "..." if len(url_str) > 80 else url_str
        print(
            f"🧠 SmartScraper Decision | URL: {url_preview} | Strategy: {decision.strategy} | Fallback: {decision.has_fallback()}"
        )

        # 2. Ejecutar estrategia según decisión
        return await self._execute_scraping_strategy(decision, url_str, timeout, config)

    def _extract_domain(self, url: str) -> str:
        """Extrae dominio de URL usando ArticleUrl VO."""
        try:
            # Usar ArticleUrl VO que encapsula validación y parsing
            article_url = ArticleUrl.try_create(url)
            if article_url:
                domain = article_url.get_domain()
                # Remover www. y convertir a minúsculas
                domain = domain.replace("www.", "")
                return domain.lower()
        except Exception:
            pass
        return ""

    def _make_scraping_decision(self, url: str) -> ScrapingDecision:
        """
        Toma decisión de estrategia de scraping usando Value Objects.

        Criterios (en orden de prioridad):
        1. Dominio en registry de JS-heavy sites
        2. URL patterns que indican JavaScript
        3. Default: sitio estático con fallback

        Args:
            url: URL a analizar

        Returns:
            ScrapingDecision con estrategia seleccionada
        """
        domain = self._extract_domain(url)

        # 1. Check dominio JS-heavy conocido
        if self._js_domains.contains(domain):
            return ScrapingDecision.for_javascript_heavy_site(domain)

        # 2. Check patrones de URL que indican JavaScript
        url_matches = self._url_patterns.find_matches(url)
        if url_matches:
            first_match = list(url_matches)[0]
            return ScrapingDecision.for_url_pattern_match(first_match)

        # 3. Default: asumir sitio estático con fallback a Playwright
        return ScrapingDecision.for_static_site(domain)

    async def _execute_scraping_strategy(
        self,
        decision: ScrapingDecision,
        url: str,
        timeout: int,
        config: Optional[ScrapingConfiguration] = None,
    ) -> Optional[str]:
        """
        Ejecuta la estrategia de scraping según decisión.

        Args:
            decision: Decisión de scraping con estrategia y fallback
            url: URL a scrapear
            timeout: Timeout en segundos
            config: Configuración especializada (opcional)

        Returns:
            HTML scrapeado o None si falla
        """
        from src.rss.article.domain.value_objects.scraper_type import ScraperStrategy

        # Ejecutar estrategia principal
        if decision.strategy == ScraperStrategy.PLAYWRIGHT:
            try:
                return await self._playwright.scrape_article_from_url(
                    url, timeout, config
                )
            except Exception as e:
                print(f"❌ Playwright failed | Error: {type(e).__name__}: {str(e)}")
                # Si Playwright falla y hay fallback, intentar trafilatura
                if decision.has_fallback():
                    print(f"🔄 Falling back to Trafilatura after Playwright error")
                    try:
                        return await self._trafilatura.scrape_article_from_url(
                            url, timeout, config
                        )
                    except Exception as fallback_error:
                        print(
                            f"❌ Trafilatura fallback also failed | Error: {str(fallback_error)}"
                        )
                        return None
                return None

        elif decision.strategy == ScraperStrategy.TRAFILATURA:
            content = await self._trafilatura.scrape_article_from_url(
                url, timeout, config
            )

            if content:
                # Validar con VO de contenido
                scrapped = ScrappedHtml.create(content)
                content_length = len(content)
                is_sufficient = self._min_content_length.is_sufficient(content)

                print(
                    f"📊 Trafilatura Result | Length: {content_length} | Sufficient: {is_sufficient} | Min Required: {self._min_content_length.value}"
                )

                if is_sufficient:
                    return content
                else:
                    print(f"⚠️ Content too short, attempting fallback to Playwright")

            # Intentar fallback si está configurado
            if decision.has_fallback():
                print(f"🔄 Falling back to Playwright")
                return await self._playwright.scrape_article_from_url(
                    url, timeout, config
                )

            return content

        # Estrategia desconocida
        return None
