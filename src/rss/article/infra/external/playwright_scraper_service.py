"""Playwright Scraper Service - Article Bounded Context."""

from typing import Optional

from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

from src.rss.article.domain.interfaces.external import IArticleScrapingService
from src.shared.domain.value_objects import ScrapingConfiguration
from src.shared.kernel.logger import ILogger


class PlaywrightScraperService(IArticleScrapingService):
    """
    Servicio de scraping con Playwright para sitios JavaScript-heavy.

    Características:
    - Browser automation headless
    - Ejecuta JavaScript completo
    - Ideal para SPAs (React, Angular, Vue)
    """

    def __init__(
        self,
        logger: Optional[ILogger] = None,
        headless: bool = True,
        user_agent: str = "Mozilla/5.0 (compatible; FeedsAI/1.0)",
    ):
        self._logger = (
            logger.bind(component="PlaywrightScraperService") if logger else None
        )
        self._headless = headless
        self._user_agent = user_agent

    async def scrape_article_from_url(
        self,
        url: str,
        timeout: int = 60,  # Aumentado de 30s a 60s
        config: Optional[ScrapingConfiguration] = None,
    ) -> Optional[str]:
        """Scrapea contenido usando Playwright."""
        from src.rss.article.domain.value_objects import ArticleUrl

        if isinstance(url, ArticleUrl):
            url = url.value

        scraping_config = config or ScrapingConfiguration.default()
        timeout_ms = timeout * 1000

        if self._logger:
            self._logger.info(
                f"🎭 Playwright: Iniciando scraping | URL: {url} | Timeout: {timeout}s"
            )

        try:
            async with async_playwright() as p:
                if self._logger:
                    self._logger.info(f"🎭 Lanzando browser Chromium")

                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-blink-features=AutomationControlled",  # Evitar detección de bot
                    ],
                )

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    extra_http_headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                    },
                )
                page = await context.new_page()

                # Ocultar webdriver property para evitar detección
                await page.add_init_script(
                    """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """
                )

                if self._logger:
                    self._logger.info(
                        f"🌐 Navegando a URL | Wait strategy: domcontentloaded | Timeout: {timeout_ms}ms"
                    )

                # Usar domcontentloaded en lugar de networkidle (más rápido y confiable)
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

                # Esperar adicional para que JavaScript se ejecute
                additional_wait = max(
                    scraping_config.wait_timeout_ms, 3000
                )  # Mínimo 3s
                if self._logger:
                    self._logger.info(
                        f"⏳ Esperando {additional_wait}ms adicionales para JavaScript"
                    )

                await page.wait_for_timeout(additional_wait)

                # PRIMERO: Eliminar elementos excluidos ANTES de extraer contenido
                if scraping_config.excluded_selectors:
                    if self._logger:
                        self._logger.info(
                            f"🗑️ Eliminando elementos excluidos | Selectores: {len(scraping_config.excluded_selectors)}"
                        )

                    for excluded_selector in scraping_config.excluded_selectors:
                        try:
                            removed_count = await page.evaluate(
                                """(selector) => {
                                    const elements = document.querySelectorAll(selector);
                                    elements.forEach(el => el.remove());
                                    return elements.length;
                                }""",
                                excluded_selector,
                            )

                            if removed_count > 0 and self._logger:
                                self._logger.info(
                                    f"🗑️ Eliminados {removed_count} elementos | Selector: {excluded_selector}"
                                )
                        except Exception as e:
                            if self._logger:
                                self._logger.warning(
                                    f"⚠️ Error eliminando selector | Selector: {excluded_selector} | Error: {str(e)}"
                                )
                            pass

                # SEGUNDO: Eliminar párrafos por patrones de texto (si está configurado)
                if scraping_config.excluded_text_patterns:
                    if self._logger:
                        self._logger.info(
                            f"🗑️ Eliminando párrafos con patrones de texto | Patrones: {len(scraping_config.excluded_text_patterns)}"
                        )

                    try:
                        # Convertir tuple a lista para JavaScript
                        patterns_list = list(scraping_config.excluded_text_patterns)

                        removed_related = await page.evaluate(
                            """(patterns) => {
                                let count = 0;
                                const paragraphs = document.querySelectorAll('p');
                                
                                paragraphs.forEach(p => {
                                    const text = p.textContent || '';
                                    
                                    // Buscar patrones al inicio del texto
                                    for (const pattern of patterns) {
                                        if (text.trim().startsWith(pattern)) {
                                            p.remove();
                                            count++;
                                            return;
                                        }
                                    }
                                    
                                    // Buscar dentro de <em><strong>
                                    const strongs = p.querySelectorAll('em > strong, strong');
                                    for (const strong of strongs) {
                                        const strongText = strong.textContent || '';
                                        for (const pattern of patterns) {
                                            if (strongText.includes(pattern)) {
                                                p.remove();
                                                count++;
                                                return;
                                            }
                                        }
                                    }
                                    
                                    // Buscar enlaces a /magazine/ dentro del párrafo (específico para Magazine:)
                                    if (patterns.includes('Magazine:')) {
                                        const magazineLinks = p.querySelectorAll('a[href*="/magazine/"]');
                                        if (magazineLinks.length > 0) {
                                            const textWithoutLink = p.textContent.replace(magazineLinks[0].textContent, '').trim();
                                            if (textWithoutLink === '' || textWithoutLink === 'Magazine:' || textWithoutLink === 'Related:') {
                                                p.remove();
                                                count++;
                                                return;
                                            }
                                        }
                                    }
                                    
                                    // Buscar párrafos que solo contienen <em> vacío y un enlace
                                    const emptyEms = p.querySelectorAll('em:empty');
                                    const links = p.querySelectorAll('a');
                                    if (emptyEms.length > 0 && links.length > 0) {
                                        const textContent = p.textContent.trim();
                                        const linkText = Array.from(links).map(l => l.textContent).join('').trim();
                                        if (textContent === linkText) {
                                            p.remove();
                                            count++;
                                            return;
                                        }
                                    }
                                });
                                
                                return count;
                            }""",
                            patterns_list,
                        )

                        if removed_related > 0 and self._logger:
                            self._logger.info(
                                f"🗑️ Eliminados {removed_related} párrafos con patrones de texto"
                            )
                    except Exception as e:
                        if self._logger:
                            self._logger.warning(
                                f"⚠️ Error eliminando párrafos por patrones | Error: {str(e)}"
                            )
                        pass

                # TERCERO: Eliminar elementos por texto (si está configurado)
                if scraping_config.excluded_texts:
                    if self._logger:
                        self._logger.info(
                            f"🗑️ Eliminando elementos con textos específicos | Textos: {len(scraping_config.excluded_texts)}"
                        )

                    try:
                        for excluded_text in scraping_config.excluded_texts:
                            removed_count = await page.evaluate(
                                """(searchText) => {
                                    let count = 0;
                                    const allElements = Array.from(document.querySelectorAll('*'));
                                    let smallestElement = null;
                                    let smallestSize = Infinity;
                                    
                                    // Buscar el elemento MÁS PEQUEÑO que contiene el texto
                                    for (const el of allElements) {
                                        const fullText = el.textContent || '';
                                        // Buscar coincidencia exacta o al inicio
                                        if (fullText.trim() === searchText || fullText.trim().startsWith(searchText)) {
                                            const size = fullText.length;
                                            if (size < smallestSize && size < 500) { // Máximo 500 caracteres
                                                smallestSize = size;
                                                smallestElement = el;
                                            }
                                        }
                                    }
                                    
                                    if (smallestElement) {
                                        smallestElement.remove();
                                        count = 1;
                                    }
                                    
                                    return count;
                                }""",
                                excluded_text,
                            )

                            if removed_count > 0 and self._logger:
                                self._logger.info(
                                    f"🗑️ Eliminado elemento con texto: '{excluded_text[:50]}...'"
                                )
                    except Exception as e:
                        if self._logger:
                            self._logger.warning(
                                f"⚠️ Error eliminando elementos por texto | Error: {str(e)}"
                            )
                        pass

                # CUARTO: Buscar selector de contenido
                selector_found = None
                selector_content = None
                html_content = None  # Inicializar para evitar UnboundLocalError

                if self._logger:
                    self._logger.info(
                        f"🔍 Intentando selectores | Selectores: {scraping_config.content_selectors}"
                    )

                for selector in scraping_config.content_selectors:
                    if self._logger:
                        self._logger.info(f"🔍 Probando selector: {selector}")

                    try:
                        element = await page.wait_for_selector(
                            selector,
                            timeout=scraping_config.selector_timeout_ms,
                            state="visible",
                        )

                        if self._logger:
                            self._logger.info(
                                f"✓ Elemento encontrado para selector: {selector}"
                            )

                        if element:
                            # Extraer contenido del selector
                            content = await page.evaluate(
                                """(selector) => {
                                    const el = document.querySelector(selector);
                                    return el ? el.innerHTML : '';
                                }""",
                                selector,
                            )

                            if self._logger:
                                self._logger.info(
                                    f"📄 Contenido extraído | Selector: {selector} | Length: {len(content) if content else 0}"
                                )

                            # Validar que el contenido no esté vacío
                            if content and len(content.strip()) > 100:
                                selector_found = selector
                                selector_content = content
                                if self._logger:
                                    self._logger.info(
                                        f"✅ Selector válido encontrado | Selector: {selector} | Length: {len(content)}"
                                    )
                                break
                            else:
                                if self._logger:
                                    self._logger.warning(
                                        f"⚠️ Selector encontrado pero contenido insuficiente | Selector: {selector} | Length: {len(content) if content else 0}"
                                    )
                    except Exception as e:
                        if self._logger:
                            self._logger.warning(
                                f"❌ Selector falló | Selector: {selector} | Error: {type(e).__name__}: {str(e)}"
                            )
                        continue

                # Extraer contenido (elementos excluidos ya fueron eliminados antes)
                if selector_found and selector_content:
                    html_content = selector_content
                    if self._logger:
                        self._logger.info(
                            f"📝 Usando contenido del selector | Selector: {selector_found} | Length: {len(html_content)}"
                        )

                # Si no se encontró contenido con selectores específicos, intentar fallbacks
                if not html_content or len(html_content.strip()) < 100:
                    # Fallback 1: Intentar selectores genéricos desde configuración
                    if self._logger:
                        self._logger.warning(
                            f"⚠️ Selectores específicos fallaron, intentando selectores de fallback | Fallbacks: {len(scraping_config.fallback_selectors)}"
                        )

                    for generic_selector in scraping_config.fallback_selectors:
                        if self._logger:
                            self._logger.info(
                                f"🔍 Probando selector genérico: {generic_selector}"
                            )

                        try:
                            content = await page.evaluate(
                                """(selector) => {
                                    const el = document.querySelector(selector);
                                    return el ? el.innerHTML : '';
                                }""",
                                generic_selector,
                            )

                            if self._logger:
                                self._logger.info(
                                    f"📄 Contenido genérico extraído | Selector: {generic_selector} | Length: {len(content) if content else 0}"
                                )

                            if content and len(content.strip()) > 100:
                                html_content = content
                                if self._logger:
                                    self._logger.info(
                                        f"✅ Selector genérico funcionó | Selector: {generic_selector} | Length: {len(content)}"
                                    )
                                break
                        except Exception as e:
                            if self._logger:
                                self._logger.warning(
                                    f"❌ Selector genérico falló | Selector: {generic_selector} | Error: {str(e)}"
                                )
                            continue
                    else:
                        # Fallback 2: Extraer body completo
                        if self._logger:
                            self._logger.warning(
                                f"⚠️ Todos los selectores fallaron, extrayendo body completo"
                            )

                        try:
                            html_content = await page.evaluate(
                                """() => {
                                const body = document.querySelector('body');
                                return body ? body.innerHTML : document.documentElement.innerHTML;
                            }"""
                            )

                            if self._logger:
                                self._logger.warning(
                                    f"📄 Usando body completo | Length: {len(html_content) if html_content else 0}"
                                )
                        except Exception as e:
                            if self._logger:
                                self._logger.error(
                                    f"❌ Error extrayendo body | Error: {str(e)}"
                                )

                            # Último recurso: page.content()
                            html_content = await page.content()

                            if self._logger:
                                self._logger.warning(
                                    f"📄 Usando page.content() | Length: {len(html_content) if html_content else 0}"
                                )

                await browser.close()

                # Validar que tenemos contenido
                if not html_content or len(html_content.strip()) < 50:
                    if self._logger:
                        self._logger.error(
                            f"❌ No se pudo extraer contenido válido | URL: {url} | Length: {len(html_content) if html_content else 0}"
                        )
                    return None

                if self._logger:
                    self._logger.info(
                        "✅ Playwright scraping completed",
                        url=url,
                        content_length=len(html_content),
                    )

                return html_content

        except PlaywrightTimeout as e:
            print(f"\n{'='*80}")
            print(f"⏱️ PLAYWRIGHT TIMEOUT EXCEPTION")
            print(f"{'='*80}")
            print(f"URL: {url}")
            print(f"Timeout: {timeout}s")
            print(f"Error: {str(e)}")
            print(f"{'='*80}\n")

            if self._logger:
                self._logger.error(
                    f"⏱️ TIMEOUT scraping | URL: {url} | Timeout: {timeout}s | Error: {str(e)}"
                )
            return None

        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()

            print(f"\n{'='*80}")
            print(f"❌ PLAYWRIGHT EXCEPTION")
            print(f"{'='*80}")
            print(f"URL: {url}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Traceback:")
            print(error_trace)
            print(f"{'='*80}\n")

            if self._logger:
                self._logger.error(
                    f"❌ ERROR scraping | URL: {url} | Error: {type(e).__name__}: {str(e)}\n{error_trace}"
                )

            # Re-raise para que el handler pueda manejarlo
            raise
