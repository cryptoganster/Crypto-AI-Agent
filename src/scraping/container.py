"""Scraping Bounded Context Container.

Container de inversión de dependencias para el bounded context Scraping.
Sigue Clean Architecture + DDD + CQRS.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.rss.article.container import ArticleContainer
    from src.rss.feed.container import SourceContainer
    from src.shared.container import SharedContainer


class ScrapingContainer:
    """
    Container del bounded context Scraping.

    Responsabilidades:
    - Factory: ScrapingFactory
    - Repository: ScrapingWriteRepository
    - Commands: StartScrapingHandler, ScrapeSourceHandler
    - Process Managers: ScrapingPipeline
    - Event Handlers: OnScrapingStartedHandler, OnSourceScrapedHandler

    Dependencias externas (inyectadas):
    - SharedContainer: Logger, Mediator, EventBus, Session
    - ArticleContainer: ArticleFactory, ArticleRepository (opcional)
    - SourceContainer: SourceReadRepository (opcional)
    """

    def __init__(
        self,
        shared: "SharedContainer",
        articles: Optional["ArticleContainer"] = None,
        sources: Optional["SourceContainer"] = None,
    ):
        self._shared = shared
        self._articles = articles
        self._sources = sources

        # Lazy loading
        self._scraping_factory = None
        self._scraping_repository = None
        self._scraping_pipeline = None
        self._source_fetching_service = None

    # === UNIT OF WORK ===

    def get_session_factory(self):
        """
        Session factory para crear sesiones de DB.

        Retorna el async_sessionmaker que debe usarse como context manager:

        Uso correcto:
            async with session_factory() as session:
                # ... usar sesión
        """
        return self._shared.session_factory

    def get_uow(self):
        """
        Unit of Work para manejar transacciones.

        Usado por Command Handlers para:
        - Transacciones atómicas
        - Commit explícito
        - Rollback automático en errores

        IMPORTANTE: Cada invocación crea un nuevo UoW con nueva sesión.
        """
        from src.shared.kernel.uow import SqlAlchemyUnitOfWork

        return SqlAlchemyUnitOfWork(
            session=self._shared.session_factory(),
            logger=self._shared.logger,
        )

    # === FACTORY ===

    def get_scraping_factory(self):
        """ScrapingFactory para crear Scraping aggregates."""
        if self._scraping_factory is None:
            from src.scraping.domain.factories import ScrapingFactory

            self._scraping_factory = ScrapingFactory()
        return self._scraping_factory

    # === REPOSITORY ===

    def get_scraping_repository(self):
        """ScrapingWriteRepository para persistir Scraping aggregates."""
        if self._scraping_repository is None:
            from src.scraping.infra.persistence.repositories import (
                ScrapingWriteRepository,
            )

            self._scraping_repository = ScrapingWriteRepository(
                session=self._shared.session_factory(),
                logger=self._shared.logger,
                event_publisher=self._shared.event_publisher,
            )
        return self._scraping_repository

    # === PROCESS MANAGERS ===

    def get_scraping_pipeline(self):
        """ScrapingPipeline - Process Manager event-driven."""
        if self._scraping_pipeline is None:
            from src.scraping.app.process_managers import ScrapingPipeline

            self._scraping_pipeline = ScrapingPipeline(
                command_bus=self._shared.mediator,
                event_bus=self._shared.event_publisher,
                logger=self._shared.logger,
            )
        return self._scraping_pipeline

    # === COMMAND HANDLERS ===

    def get_start_scraping_handler(self):
        """StartScrapingHandler - Inicia scraping de sources."""
        from src.scraping.app.commands.start_scraping import (
            StartScrapingHandler,
            StartScrapingValidator,
        )

        return StartScrapingHandler(
            source_read_repository=self._get_source_read_repository(),
            scraping_repository=self.get_scraping_repository(),
            scraping_factory=self.get_scraping_factory(),
            session_factory=self._shared.session_factory,
            logger=self._shared.logger,
            validator=StartScrapingValidator(),
        )

    def get_scrape_source_handler(self):
        """ScrapeSourceHandler - Scrapea una source individual."""
        from src.scraping.app.commands.scrape_source import ScrapeSourceHandler

        return ScrapeSourceHandler(
            source_repository=self._get_source_read_repository(),
            scraping_repository=self.get_scraping_repository(),
            scraping_service=self._get_source_fetching_service(),
            event_bus=self._shared.event_publisher,
            logger=self._shared.logger,
            session_factory=self._shared.session_factory,
            shared=self._shared,
            articles=self._articles,
        )

    # === HANDLER REGISTRATION ===

    def register_handlers(self) -> None:
        """
        Registra todos los handlers del bounded context Scraping.

        NOTA: El pipeline antiguo (RunFetchPipeline) está siendo reemplazado
        por arquitectura event-driven con ScrapingPipeline.

        Arquitectura actual:
        - StartScrapingCommand → StartScrapingHandler → emite ScrapingStarted
        - ScrapingStarted → OnScrapingStartedHandler → ScrapingPipeline
        - ScrapingPipeline emite ScrapeSourceCommand para cada source
        - SourceScraped → OnSourceScrapedHandler → ScrapingPipeline
        - ScrapingPipeline emite ScrapingCompleted cuando todas terminan

        Incluye:
        - Command handlers en Mediator
        - Event handlers en EventHandlerRegistry
        """
        self._register_command_handlers()
        self._register_event_handlers()

        self._shared.logger.info(
            "ScrapingContainer: handlers registrados (event-driven architecture)",
        )

    def _register_command_handlers(self) -> None:
        """Registra command handlers en el Mediator."""
        from src.scraping.app.commands import (
            ScrapeSourceCommand,
            StartScrapingCommand,
        )

        handlers_registered = []

        self._shared.register_handler(
            StartScrapingCommand,
            self.get_start_scraping_handler(),
        )
        handlers_registered.append("StartScrapingHandler")

        self._shared.register_handler(
            ScrapeSourceCommand,
            self.get_scrape_source_handler(),
        )
        handlers_registered.append("ScrapeSourceHandler")

        self._shared.logger.info(
            "ScrapingContainer: command handlers registrados",
            handlers=handlers_registered,
            count=len(handlers_registered),
        )

    def _register_event_handlers(self) -> None:
        """Registra event handlers para arquitectura event-driven."""
        from src.scraping.app.event_handlers.on_scraping_started import (
            OnScrapingStartedHandler,
        )
        from src.scraping.app.event_handlers.on_source_scraped import (
            OnSourceScrapedHandler,
        )
        from src.scraping.domain.events import ScrapingStarted, SourceScraped

        # ScrapingStarted → ScrapingPipeline
        scraping_started_handler = OnScrapingStartedHandler(
            scraping_pipeline=self.get_scraping_pipeline(),
            logger=self._shared.logger,
        )
        self._shared.event_handler_registry.register_handler(
            ScrapingStarted,
            scraping_started_handler,
        )

        # SourceScraped → ScrapingPipeline
        source_scraped_handler = OnSourceScrapedHandler(
            scraping_pipeline=self.get_scraping_pipeline(),
            logger=self._shared.logger,
        )
        self._shared.event_handler_registry.register_handler(
            SourceScraped,
            source_scraped_handler,
        )

    # === DEPENDENCIES FROM OTHER CONTEXTS ===

    def _get_source_read_repository(self):
        """Obtiene SourceReadRepository (del bounded context Source)."""
        if self._sources:
            return self._sources.get_source_read_repository()

        # Fallback: crear instancia local
        from src.rss.feed.infra.persistence.repositories.source_read_repository import (
            SqlAlchemySourceReadRepository,
        )

        return SqlAlchemySourceReadRepository(
            session=self._shared.session_factory(),
            logger=self._shared.logger,
        )

    def _get_source_fetching_service(self):
        """Obtiene ScrapingCoordinatorService (domain service del BC Scraping)."""
        if self._source_fetching_service is None:
            from src.rss.feed.domain.services import SourceHealthService
            from src.scraping.domain.services import ScrapingCoordinatorService
            from src.scraping.infra.external import RssFeedFetcherService

            rss_fetcher = RssFeedFetcherService(
                logger=self._shared.logger,
                timeout=30,
                max_concurrent=10,
                rate_limit_delay=1.0,
            )

            source_health = SourceHealthService(
                time_provider=self._shared.time_provider,
            )

            # Obtener dependencias de otros contexts
            article_factory = (
                self._articles.get_article_factory() if self._articles else None
            )
            article_repo = (
                self._articles.get_article_repository() if self._articles else None
            )
            dedup_service = (
                self._articles.get_deduplication_service() if self._articles else None
            )
            quality_service = (
                self._articles.get_quality_service() if self._articles else None
            )

            self._source_fetching_service = ScrapingCoordinatorService(
                rss_fetcher=rss_fetcher,
                article_repository=article_repo,
                source_repository=self._get_source_write_repository(),
                scraping_repository=self.get_scraping_repository(),
                source_health_service=source_health,
                article_deduplication_service=dedup_service,
                article_quality_service=quality_service,
                article_factory=article_factory,
                logger=self._shared.logger,
            )

        return self._source_fetching_service

    def _get_source_write_repository(self):
        """Obtiene SourceWriteRepository (del bounded context Source)."""
        if self._sources:
            return self._sources.get_source_write_repository()

        # Fallback: crear instancia local
        from src.rss.feed.domain.factories import SourceFactory
        from src.rss.feed.infra.persistence.repositories.source_write_repository import (
            SourceWriteRepository,
        )

        return SourceWriteRepository(
            session=self._shared.session_factory(),
            logger=self._shared.logger,
        )
