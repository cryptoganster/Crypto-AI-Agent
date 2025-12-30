"""Handler para ScrapeSourceCommand.

Handler simple que sigue CQRS estricto:
- Obtiene un agregado del repositorio
- Ejecuta una operación
- Persiste cambios
- Emite evento
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.rss.feed.domain.interfaces.repositories import ISourceReadRepository
from src.scraping.app.commands.scrape_source.command import ScrapeSourceCommand
from src.scraping.app.commands.scrape_source.result import ScrapeSourceResult
from src.scraping.domain.events import SourceScraped
from src.shared.kernel.bus import IEventBus
from src.shared.kernel.logger import ILogger


class ScrapeSourceHandler:
    """
    Handler para scrapear una única source RSS.

    Este handler sigue CQRS estricto:
    - Obtiene la source y scraping del repositorio (read)
    - Ejecuta el scraping (operación)
    - Emite evento SourceScraped

    NO hace:
    - Múltiples operaciones en cascada
    - Queries complejas
    - Orquestación de múltiples sources

    Dependencies:
    - source_repository: Para obtener la source
    - scraping_repository: Para obtener el Scraping aggregate
    - scraping_service: Para ejecutar el scraping
    - event_bus: Para emitir eventos
    - logger: Para logging

    Example:
        >>> handler = ScrapeSourceHandler(...)
        >>> result = await handler.handle(command)
    """

    def __init__(
        self,
        source_repository: ISourceReadRepository,
        scraping_repository,  # IScrapingWriteRepository (tiene find_by_id)
        scraping_service,  # SourceFetchingService
        event_bus: IEventBus,
        logger: ILogger,
        session_factory,  # async_sessionmaker para crear sesiones nuevas
        shared=None,  # SharedContainer para time_provider
        articles=None,  # ArticleContainer para servicios
    ):
        """
        Inicializa el handler.

        ARQUITECTURA:
        - Recibe session_factory para crear UoW bajo demanda
        - Cada handle() crea su propio UoW con sesión aislada
        - Garantiza transacciones independientes sin sesiones stale

        Args:
            source_repository: Repository para obtener sources
            scraping_repository: Repository para obtener Scraping aggregate
            scraping_service: Servicio de scraping RSS
            event_bus: Bus para emitir eventos
            logger: Logger para logging
            session_factory: Factory para crear nuevas sesiones de DB
            shared: SharedContainer para acceder a time_provider
            articles: ArticleContainer para acceder a servicios de Article
        """
        self._source_repo = source_repository
        self._scraping_repo = scraping_repository
        self._scraping_service = scraping_service
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._logger = logger
        self._shared = shared
        self._articles = articles

    async def handle(self, command: ScrapeSourceCommand) -> ScrapeSourceResult:
        """
        Ejecuta el scraping de una source.

        Flujo:
        1. Obtener source del repositorio
        2. Ejecutar scraping RSS
        3. Persistir artículos nuevos
        4. Emitir evento SourceScraped
        5. Retornar resultado

        Args:
            command: Comando con datos del scraping

        Returns:
            ScrapeSourceResult con resultado de la operación
        """
        self._logger.info(
            "Iniciando scraping de source",
            source_id=command.source_id,
            pipeline_id=command.pipeline_id,
            correlation_id=command.correlation_id,
        )

        try:
            # 1. Obtener source
            source = await self._source_repo.find_by_id(UUID(command.source_id))

            if not source:
                self._logger.warning(
                    "Source no encontrada",
                    source_id=command.source_id,
                )
                return ScrapeSourceResult.failure_result(
                    source_id=command.source_id,
                    error="Source no encontrada",
                    pipeline_id=command.pipeline_id,
                )

            # 2. Crear Scraping para esta operación
            # El Scraping aggregate es necesario para el servicio de fetching
            from src.rss.feed.domain.value_objects import SourceId
            from src.scraping.domain.factories import ScrapingFactory

            factory = ScrapingFactory()
            scraping = factory.create_multi_source(
                sources=[SourceId(UUID(command.source_id))],
                scraping_id=command.pipeline_id,  # Usar pipeline_id si existe
                triggered_by="scrape_source_handler",
            )

            # Crear sesión y UoW para esta transacción
            # ARQUITECTURA: Cada comando tiene su propia transacción aislada
            async with self._session_factory() as session:
                from src.shared.kernel.uow import SqlAlchemyUnitOfWork

                uow = SqlAlchemyUnitOfWork(session, self._logger)

                async with uow:
                    # Crear repositories con la MISMA sesión del UoW
                    from src.rss.article.infra.persistence.repositories import (
                        ArticleWriteRepository,
                    )
                    from src.rss.feed.infra.persistence.repositories import (
                        SourceWriteRepository,
                    )
                    from src.scraping.infra.persistence.repositories import (
                        ScrapingWriteRepository,
                    )

                    scraping_repo_uow = ScrapingWriteRepository(
                        session=session,
                        logger=self._logger,
                        event_publisher=None,  # No publicar eventos dentro de transacción
                    )

                    article_repo_uow = ArticleWriteRepository(
                        session=session,
                        logger=self._logger,
                        event_publisher=None,  # No publicar eventos dentro de transacción
                    )

                    source_repo_uow = SourceWriteRepository(
                        session=session,
                        logger=self._logger,
                    )

                    # ARQUITECTURA: NO guardar scraping aquí - causa DEADLOCK
                    # El Scraping ya fue guardado por StartScrapingHandler
                    # Este handler solo debe scrapear la source
                    self._logger.info(
                        "💾 Scraping ya guardado por StartScrapingHandler - skip save"
                    )
                    scraping.mark_events_as_committed()  # Limpiar eventos del factory

                    # 3. Crear servicio de scraping con repositories que usan la sesión del UoW
                    from src.rss.feed.domain.services import SourceHealthService
                    from src.scraping.domain.services import ScrapingCoordinatorService
                    from src.scraping.infra.external import RssFeedFetcherService

                    rss_fetcher = RssFeedFetcherService(
                        logger=self._logger,
                        timeout=30,
                        max_concurrent=10,
                        rate_limit_delay=1.0,
                    )

                    source_health = SourceHealthService(
                        time_provider=self._shared.time_provider,
                    )

                    # Obtener servicios de Article context
                    self._logger.info("🔍 Obteniendo servicios de Article context...")
                    article_factory = (
                        self._articles.get_article_factory() if self._articles else None
                    )
                    dedup_service = (
                        self._articles.get_deduplication_service()
                        if self._articles
                        else None
                    )
                    quality_service = (
                        self._articles.get_quality_service() if self._articles else None
                    )

                    scraping_service_uow = ScrapingCoordinatorService(
                        rss_fetcher=rss_fetcher,
                        article_repository=article_repo_uow,  # ← Usar repo con sesión del UoW
                        source_repository=source_repo_uow,  # ← Usar repo con sesión del UoW
                        scraping_repository=scraping_repo_uow,  # ← Usar repo con sesión del UoW
                        source_health_service=source_health,
                        article_deduplication_service=dedup_service,
                        article_quality_service=quality_service,
                        article_factory=article_factory,
                        logger=self._logger,
                    )

                    self._logger.info(
                        f"🚀 Ejecutando fetch_single_source para source_id={command.source_id}..."
                    )
                    # Ejecutar scraping usando fetch_single_source
                    # Esto crea y persiste los artículos dentro de la transacción
                    scraping_result = await scraping_service_uow.fetch_single_source(
                        source=source,
                        scraping=scraping,
                    )
                    self._logger.info(
                        f"✅ fetch_single_source completado | "
                        f"success={scraping_result.get('success')} | "
                        f"articles_created={scraping_result.get('articles_created', 0)}"
                    )

                    self._logger.info("💾 Haciendo commit de la transacción...")
                    # Commit DESPUÉS de crear los artículos para persistirlos
                    await uow.commit()

                    self._logger.info(
                        "✅ Transacción committed - artículos persistidos",
                        source_id=command.source_id,
                        articles_created=scraping_result.get("articles_created", 0),
                    )

            if not scraping_result.get("success", False):
                error_msg = scraping_result.get("error", "Error desconocido")

                # Log detallado del error con todo el contexto
                self._logger.error(
                    f"❌ Scraping falló - Detalles completos\n"
                    f"  Source ID: {command.source_id}\n"
                    f"  Source Name: {source.name.value if hasattr(source, 'name') else 'unknown'}\n"
                    f"  Source URL: {source.url.value if hasattr(source, 'url') else 'unknown'}\n"
                    f"  Error: {error_msg}\n"
                    f"  Articles Discovered: {scraping_result.get('articles_discovered', 0)}\n"
                    f"  Articles Created: {scraping_result.get('articles_created', 0)}\n"
                    f"  Duration: {scraping_result.get('duration', 'unknown')}\n"
                    f"  Full Result: {scraping_result}"
                )

                # Emitir evento SourceScraped (fallo)
                await self._emit_source_scraped_event(
                    command=command,
                    success=False,
                    articles_discovered=0,
                    error=error_msg,
                )

                return ScrapeSourceResult.failure_result(
                    source_id=command.source_id,
                    error=error_msg,
                    pipeline_id=command.pipeline_id,
                )

            # 3. Obtener resultados del scraping
            articles_discovered = scraping_result.get("articles_discovered", 0)
            articles_created = scraping_result.get("articles_created", 0)
            new_article_ids = scraping_result.get("article_ids", [])

            self._logger.info(
                f"🔍 DEBUG: Resultado del scraping | "
                f"source={command.source_id} | "
                f"articles_discovered={articles_discovered} | "
                f"articles_created={articles_created} | "
                f"article_ids_count={len(new_article_ids)}"
            )

            # 4. Emitir evento SourceScraped (éxito)
            await self._emit_source_scraped_event(
                command=command,
                success=True,
                articles_discovered=articles_discovered,
                articles_created=articles_created,
                article_ids=new_article_ids,
            )

            self._logger.info(
                "Scraping completado exitosamente",
                source_id=command.source_id,
                articles_discovered=articles_discovered,
                articles_created=articles_created,
            )

            # 5. Retornar resultado
            return ScrapeSourceResult.success_result(
                source_id=command.source_id,
                articles_count=articles_discovered,
                new_articles_count=articles_created,
                article_ids=new_article_ids,
                pipeline_id=command.pipeline_id,
            )

        except Exception as e:
            self._logger.exception(
                "Error durante scraping",
                source_id=command.source_id,
                error=str(e),
            )

            # Emitir evento SourceScraped (fallo)
            await self._emit_source_scraped_event(
                command=command,
                success=False,
                articles_discovered=0,
                error=str(e),
            )

            return ScrapeSourceResult.failure_result(
                source_id=command.source_id,
                error=str(e),
                pipeline_id=command.pipeline_id,
            )

    async def _emit_source_scraped_event(
        self,
        command: ScrapeSourceCommand,
        success: bool,
        articles_discovered: int,
        articles_created: int = 0,
        article_ids: list = None,
        error: Optional[str] = None,
        duration_seconds: float = 0.0,
    ) -> None:
        """
        Emite evento SourceScraped.

        Este evento es escuchado por ScrapingPipeline para
        trackear el progreso y determinar cuándo todas las
        sources han sido procesadas.

        Args:
            command: Comando original
            success: Si fue exitoso
            articles_discovered: Artículos encontrados
            articles_created: Artículos nuevos creados
            article_ids: IDs de artículos creados
            error: Error si falló
            duration_seconds: Duración del scraping
        """
        if success:
            event = SourceScraped.success_event(
                scraping_id=command.pipeline_id or command.correlation_id,
                source_id=command.source_id,
                articles_discovered=articles_discovered,
                articles_created=articles_created,
                article_ids=article_ids or [],
                duration_seconds=duration_seconds,
            )
        else:
            event = SourceScraped.failure_event(
                scraping_id=command.pipeline_id or command.correlation_id,
                source_id=command.source_id,
                error_message=error or "Unknown error",
                error_type="SCRAPING_ERROR",
                duration_seconds=duration_seconds,
            )

        await self._event_bus.publish(event)

        self._logger.debug(
            "Evento SourceScraped emitido",
            scraping_id=event.scraping_id,
            source_id=command.source_id,
            success=success,
        )
