"""Handler para ScrapeArticleContent command."""

import traceback
from uuid import UUID

from src.rss.article.domain.events import ArticleContentScraped
from src.rss.article.domain.interfaces.external import IArticleScrapingService
from src.rss.article.domain.interfaces.repositories import (
    IArticleWriteRepository,
)
from src.rss.article.domain.value_objects import ArticleId, ScraperType, ScrappedHtml
from src.rss.feed.domain.interfaces.repositories import (
    ISourceReadRepository,
)
from src.shared.domain.value_objects import TimeoutDuration
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork

from .command import ScrapeArticleContentCommand
from .result import ScrapeArticleContentResult


class ScrapeArticleContentHandler:
    """
    Handler que ejecuta el scraping de contenido completo de artículos.

    Responsabilidades:
    - Obtener artículo del repositorio
    - Ejecutar scraping con el servicio apropiado
    - Actualizar article.content.scrapped
    - Persistir cambios

    CQRS ESTRICTO:
    - Usa WriteRepository para Article (mismo BC)
    - Usa ReadRepository para Source (cross-BC, caso especial válido)

    UNIT OF WORK:
    - Usa UoW para manejar transacciones
    - Commit explícito después de save
    - Eventos publicados FUERA de transacción
    """

    def __init__(
        self,
        session_factory,  # Callable que crea sesiones
        source_read_repository: ISourceReadRepository,
        scraper_service: IArticleScrapingService,
        event_bus,  # IEventBus
        logger: ILogger,
    ):
        """
        Inicializa el handler.

        Args:
            session_factory: Factory para crear sesiones nuevas en cada invocación
            source_read_repository: Repository de fuentes (read) - cross-BC, caso especial
            scraper_service: Servicio de scraping (puede ser SmartScraperService)
            event_bus: Event bus para publicar eventos de dominio
            logger: Logger para observabilidad
        """
        self._session_factory = session_factory
        self._source_read_repository = source_read_repository
        self._scraper_service = scraper_service
        self._event_bus = event_bus
        self._logger = logger.bind(
            layer="application", component="ScrapeArticleContentHandler"
        )

    async def handle(
        self, command: ScrapeArticleContentCommand
    ) -> ScrapeArticleContentResult:
        """
        Ejecuta el comando de scraping.

        Args:
            command: Comando con parámetros de scraping

        Returns:
            ScrapeArticleContentResult con resultado de la operación
        """
        self._logger.info(
            "Processing ScrapeArticleContentCommand",
            article_id=command.article_id,
            force_rescrape=command.force_rescrape,
            use_smart_scraper=command.use_smart_scraper,
        )

        # Crear NUEVA sesión para esta invocación
        from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
            RssArticleWriteRepository,
        )
        from src.shared.kernel.uow import SqlAlchemyUnitOfWork

        session = self._session_factory()
        article_repository = RssArticleWriteRepository(
            session=session, logger=self._logger
        )
        uow = SqlAlchemyUnitOfWork(session=session, logger=self._logger)

        try:
            # 1. Cargar artículo usando WriteRepository.load() (CQRS Estricto)
            article_id_vo = ArticleId(command.article_id)

            self._logger.info(
                f"🔍 Intentando cargar artículo | ID: {command.article_id} | ID VO: {article_id_vo.value} | Session: {id(session)}"
            )

            article = await article_repository.load(article_id_vo)

            if not article:
                error_msg = f"Article {command.article_id} not found"
                self._logger.error(
                    f"❌ ARTICLE NOT FOUND | "
                    f"ID solicitado: {command.article_id} | "
                    f"ID VO: {article_id_vo.value} | "
                    f"Tipo ID: {type(command.article_id)} | "
                    f"Repository: {type(article_repository).__name__} | "
                    f"Session: {id(session)}"
                )
                self._logger.warning(error_msg)

                # Emitir evento de fallo
                await self._event_bus.publish(
                    ArticleContentScraped(
                        article_id=command.article_id,
                        success=False,
                        error_message=error_msg,
                    )
                )

                return ScrapeArticleContentResult.failure_result(
                    article_id=command.article_id, error_message=error_msg
                )

            # 2. Verificar si ya tiene contenido scrapeado
            if article.content.scraped and not command.force_rescrape:
                self._logger.info(
                    "Article already has scraped content, skipping",
                    article_id=command.article_id,
                    content_length=len(article.content.scraped),
                )

                # Emitir evento ENRIQUECIDO de éxito (cached) con datos para siguiente paso
                await self._event_bus.publish(
                    ArticleContentScraped(
                        article_id=command.article_id,
                        success=True,
                        content_length=len(article.content.scraped),
                        scraper_used="cached",
                        html_content=article.content.scraped,  # ← NUEVO: Para siguiente handler
                        article_url=str(article.metadata.url),  # ← NUEVO: Para logging
                        article_title=str(
                            article.metadata.title
                        ),  # ← NUEVO: Para logging
                    )
                )

                return ScrapeArticleContentResult.success_result(
                    article_id=command.article_id,
                    content_length=len(article.content.scraped),
                    scraper_used="cached",
                    was_cached=True,
                )

            # 3. Obtener Source para usar su scraping_config (si tiene)
            scraping_config = None
            if article.metadata.source_id:
                try:
                    # Extraer UUID del Value Object SourceId
                    source_id_uuid = article.metadata.source_id.value
                    source = await self._source_read_repository.find_by_id(
                        source_id_uuid
                    )
                    if source:
                        self._logger.debug(
                            f"📋 Source found | Source: {source.name} | Has scraping_config: {source.scraping_config is not None}"
                        )
                        if source.scraping_config:
                            scraping_config = source.scraping_config
                            self._logger.info(
                                f"⚙️ Using specialized scraping config | Source: {source.name} | Selectors: {len(scraping_config.content_selectors)} | Wait: {scraping_config.wait_timeout_ms}ms | Strategy: {scraping_config.wait_strategy} | Scroll: {scraping_config.scroll_needed}"
                            )
                        else:
                            self._logger.info(
                                f"ℹ️ Source has NO specialized scraping config, using defaults | Source: {source.name}"
                            )
                    else:
                        self._logger.warning(
                            f"⚠️ Source not found for article | SourceID: {article.source_id}"
                        )
                except Exception as e:
                    self._logger.warning(
                        f"⚠️ Could not get source config, using default | Error: {str(e)}"
                    )
            else:
                self._logger.warning(
                    f"⚠️ Article has no source_id, cannot use specialized config"
                )

            # 4. Ejecutar scraping con manejo de excepciones
            timeout = TimeoutDuration(command.timeout_seconds)

            self._logger.info(
                f"🌐 Starting article scraping | URL: {article.metadata.url} | Timeout: {timeout} | Scraper: {type(self._scraper_service).__name__}",
                article_id=command.article_id,
            )

            try:
                scrapped_html_raw = await self._scraper_service.scrape_article_from_url(
                    url=article.metadata.url,
                    timeout=int(timeout),
                    config=scraping_config,  # Usar config del source si existe
                )

                # Debug detallado: Log del HTML raw recibido
                raw_length = len(scrapped_html_raw) if scrapped_html_raw else 0
                stripped_length = (
                    len(scrapped_html_raw.strip()) if scrapped_html_raw else 0
                )
                has_html_tags = "<" in scrapped_html_raw if scrapped_html_raw else False

                self._logger.info(
                    f"📝 Raw HTML received | Length: {raw_length} | Stripped: {stripped_length} | Has tags: {has_html_tags} | Type: {type(scrapped_html_raw).__name__}"
                )

                # Print directo para debugging
                print(f"\n{'='*80}")
                print(f"🔍 SCRAPING DEBUG - Article: {command.article_id}")
                print(f"{'='*80}")
                print(f"Raw HTML is None: {scrapped_html_raw is None}")
                print(f"Raw HTML type: {type(scrapped_html_raw)}")
                print(f"Raw HTML length: {raw_length}")
                print(f"Raw HTML stripped length: {stripped_length}")
                print(
                    f"Raw HTML == '': {scrapped_html_raw == '' if scrapped_html_raw is not None else 'N/A'}"
                )
                print(f"Has HTML tags: {has_html_tags}")
                if scrapped_html_raw:
                    print(f"\nFirst 500 chars:")
                    print(scrapped_html_raw[:500])
                print(f"{'='*80}\n")

            except TimeoutError as e:
                error_msg = f"Timeout scraping article: {str(e)}"
                self._logger.error(
                    f"⏱️ TIMEOUT scraping article | URL: {article.metadata.url} | Timeout: {timeout} | Error: {str(e)}\n{traceback.format_exc()}"
                )

                # Emitir evento de fallo
                await self._event_bus.publish(
                    ArticleContentScraped(
                        article_id=command.article_id,
                        success=False,
                        error_message=error_msg,
                    )
                )

                return ScrapeArticleContentResult.failure_result(
                    article_id=command.article_id, error_message=error_msg
                )
            except Exception as scrape_error:
                error_msg = f"Error during scraping: {str(scrape_error)}"
                self._logger.error(
                    f"❌ ERROR scraping article | URL: {article.metadata.url} | Error: {type(scrape_error).__name__}: {str(scrape_error)}\n{traceback.format_exc()}"
                )

                # Emitir evento de fallo
                await self._event_bus.publish(
                    ArticleContentScraped(
                        article_id=command.article_id,
                        success=False,
                        error_message=error_msg,
                    )
                )

                return ScrapeArticleContentResult.failure_result(
                    article_id=command.article_id, error_message=error_msg
                )

            # 4. Crear VO de HTML scrapeado con validaciones
            scrapped_html = ScrappedHtml.create(scrapped_html_raw)

            # Debug del VO creado
            print(f"\n{'='*80}")
            print(f"🔍 SCRAPPED HTML VO DEBUG")
            print(f"{'='*80}")
            print(f"VO value is None: {scrapped_html.value is None}")
            print(f"VO value type: {type(scrapped_html.value)}")
            print(f"VO value length: {len(scrapped_html.value)}")
            print(f"VO value stripped length: {len(scrapped_html.value.strip())}")
            print(f"VO is_empty(): {scrapped_html.is_empty()}")
            print(f"VO get_length(): {scrapped_html.get_length()}")
            if scrapped_html.value:
                print(f"\nVO First 500 chars:")
                print(scrapped_html.value[:500])
            print(f"{'='*80}\n")

            if scrapped_html.is_empty():
                error_msg = "Scraping returned empty content"

                # Análisis detallado del contenido vacío
                analysis = {
                    "article_id": command.article_id,
                    "url": article.metadata.url,
                    "source_id": (
                        str(article.metadata.source_id)
                        if article.metadata.source_id
                        else None
                    ),
                    "scraper_service": type(self._scraper_service).__name__,
                    "raw_html_length": (
                        len(scrapped_html_raw) if scrapped_html_raw else 0
                    ),
                    "raw_html_type": str(type(scrapped_html_raw)),
                    "raw_is_none": scrapped_html_raw is None,
                    "raw_is_empty_string": (
                        scrapped_html_raw == ""
                        if scrapped_html_raw is not None
                        else None
                    ),
                    "scraping_config_used": scraping_config is not None,
                }

                if scraping_config:
                    analysis.update(
                        {
                            "config_selectors": scraping_config.content_selectors,
                            "config_selectors_count": len(
                                scraping_config.content_selectors
                            ),
                            "config_excluded_count": (
                                len(scraping_config.excluded_selectors)
                                if scraping_config.excluded_selectors
                                else 0
                            ),
                            "config_wait_ms": scraping_config.wait_timeout_ms,
                            "config_strategy": scraping_config.wait_strategy,
                            "config_scroll": scraping_config.scroll_needed,
                        }
                    )

                if scrapped_html_raw:
                    analysis.update(
                        {
                            "raw_preview_first_500": scrapped_html_raw[:500],
                            "raw_preview_last_200": (
                                scrapped_html_raw[-200:]
                                if len(scrapped_html_raw) > 200
                                else scrapped_html_raw
                            ),
                            "has_html_opening_tag": "<html"
                            in scrapped_html_raw.lower(),
                            "has_body_tag": "<body" in scrapped_html_raw.lower(),
                            "has_article_tag": "<article" in scrapped_html_raw.lower(),
                            "has_main_tag": "<main" in scrapped_html_raw.lower(),
                            "tag_count": scrapped_html_raw.count("<"),
                        }
                    )

                # Capturar stack trace completo para debugging
                stack_trace = "".join(traceback.format_stack())

                self._logger.error(
                    f"⚠️ SCRAPING RETURNED EMPTY CONTENT - ANALYSIS\n\nStack Trace:\n{stack_trace}",
                    **analysis,
                )

                # Emitir evento de fallo
                await self._event_bus.publish(
                    ArticleContentScraped(
                        article_id=command.article_id,
                        success=False,
                        error_message=error_msg,
                    )
                )

                return ScrapeArticleContentResult.failure_result(
                    article_id=command.article_id, error_message=error_msg
                )

            # 5. Actualizar artículo con contenido scrapeado (dentro de transacción)
            if command.update_article:
                async with uow:
                    article.update_scraped(scraped=scrapped_html.value)
                    await article_repository.save(article)
                    await uow.commit()

                self._logger.info(
                    "Article scrapped content saved",
                    article_id=command.article_id,
                    content_length=scrapped_html.get_length(),
                    has_quality=scrapped_html.has_minimum_quality(),
                )

            # 6. Determinar qué scraper se usó con VO
            scraper_type = ScraperType.from_service(
                type(self._scraper_service).__name__
            )

            self._logger.info(
                f"✅ Scraping completed successfully | URL: {article.metadata.url} | Scraper: {scraper_type} | Length: {scrapped_html.get_length()} | Quality: {scrapped_html.has_minimum_quality()}"
            )

            # Emitir evento ENRIQUECIDO de éxito con datos para siguiente paso
            await self._event_bus.publish(
                ArticleContentScraped(
                    article_id=command.article_id,
                    success=True,
                    content_length=scrapped_html.get_length(),
                    scraper_used=scraper_type.display_name(),
                    html_content=scrapped_html.value,  # ← NUEVO: Para siguiente handler
                    article_url=article.metadata.url,  # ← NUEVO: Para logging
                    article_title=str(article.metadata.title),  # ← NUEVO: Para logging
                )
            )

            return ScrapeArticleContentResult.success_result(
                article_id=command.article_id,
                content_length=scrapped_html.get_length(),
                scraper_used=scraper_type.display_name(),
            )

        except Exception as e:
            self._logger.exception(
                "Error scraping article content",
                article_id=command.article_id,
                error=str(e),
            )

            # Emitir evento de fallo
            await self._event_bus.publish(
                ArticleContentScraped(
                    article_id=command.article_id,
                    success=False,
                    error_message=str(e),
                )
            )

            return ScrapeArticleContentResult.failure_result(
                article_id=command.article_id, error_message=str(e)
            )
        finally:
            # Cerrar sesión
            await session.close()
