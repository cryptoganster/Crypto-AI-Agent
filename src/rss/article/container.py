"""Article Bounded Context Container.

Container de inversión de dependencias para el bounded context Article.
Sigue Clean Architecture + DDD + CQRS.
"""

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from src.rss.article.domain.interfaces.services import (
        IArticlePlaintextExtractionService,
    )
    from src.shared.container import SharedContainer


class ProcessManagerMethodWrapper:
    """
    Wrapper para métodos de Process Managers.

    Hace que métodos de Process Managers sean compatibles con Event Handler Registry.
    """

    def __init__(self, method: Callable, name: str):
        """
        Inicializa wrapper.

        Args:
            method: Método del Process Manager a wrappear
            name: Nombre descriptivo para logging
        """
        self._method = method
        self._name = name

    async def handle(self, event: Any) -> None:
        """
        Delega al método del Process Manager.

        Args:
            event: Evento de dominio a procesar
        """
        await self._method(event)

    def __repr__(self) -> str:
        return f"ProcessManagerMethodWrapper({self._name})"


class RssArticleContainer:
    """
    Container del bounded context RSS Article.

    Responsabilidades:
    - Factory: ArticleFactory
    - Repository: ArticleWriteRepository, ArticleReadRepository
    - Services: Quality, Deduplication, Language, Metrics, etc.
    - Process Managers: ContentExtractorPipeline, ContentAnalysisPipeline
    - Event Handlers: OnScrapingCompletedHandler, OnContentExtractorPipelineCompletedHandler
    - Commands: ExtractKeywords, DetectLanguage, CalculateQuality, etc.
    - Queries: ArticleQueries (CQRS Read Side)
    """

    def __init__(self, shared: "SharedContainer"):
        self._shared = shared

        # Lazy loading
        self._article_factory = None
        self._article_write_repository = None
        self._article_read_repository = None
        self._article_queries = None

        # Domain Services
        self._quality_service = None
        self._deduplication_service = None
        self._semantic_deduplication_service = None
        self._language_detector = None
        self._language_detection_service = None
        self._metrics_calculation_service = None
        self._summary_extraction_service = None
        self._plaintext_extraction_service = None

        # External Services
        self._scraping_service = None
        self._html_to_markdown_converter = None
        self._html_to_plaintext_converter = None
        self._keyword_service = None

        # Process Managers (Singleton)
        self._content_extraction_initiator = None
        self._content_extraction_pipeline = None
        self._content_analysis_pipeline = None

        # Command Handlers (Lazy)
        self._start_processing_handler = None
        self._scrape_content_handler = None
        self._extract_plaintext_handler = None
        self._convert_to_markdown_handler = None
        self._calculate_article_metrics_handler = None
        self._detect_language_handler = None
        self._generate_summary_handler = None
        self._extract_keywords_handler = None
        self._calculate_quality_handler = None
        self._detect_duplicate_handler = None

        # Query Handlers (Lazy) - CQRS Read Side
        self._get_article_by_id_handler = None
        self._get_pending_articles_handler = None

    # === FACTORY ===

    def get_article_factory(self):
        """ArticleFactory para crear Article aggregates."""
        if self._article_factory is None:
            from src.rss.article.domain.factories import ArticleFactory

            self._article_factory = ArticleFactory()
        return self._article_factory

    # === REPOSITORIES ===

    def get_article_repository(self):
        """
        ArticleWriteRepository para persistir Article aggregates.

        IMPORTANTE: Crea una NUEVA instancia cada vez para evitar compartir
        sesiones entre handlers. Cada handler debe tener su propia sesión.
        """
        from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
            RssArticleWriteRepository,
        )

        return RssArticleWriteRepository(
            session=self._shared.session_factory(),
            logger=self._shared.logger,
        )

    def get_article_write_repository(self):
        """Alias para get_article_repository() - CQRS naming."""
        return self.get_article_repository()

    def get_article_read_repository(self):
        """
        ArticleReadRepository para queries de lectura.

        IMPORTANTE: Crea una NUEVA instancia cada vez para evitar compartir
        sesiones entre queries. Cada query debe tener su propia sesión.
        """
        from src.rss.article.infra.persistence.repositories import (
            ArticleReadRepository,
        )

        return ArticleReadRepository(
            session=self._shared.session_factory(),
            logger=self._shared.logger,
        )

    # === UNIT OF WORK ===

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

    # === QUERIES (CQRS Read Side) ===

    def get_article_queries(self):
        """
        ArticleQueries - CQRS Read Side.

        NOTA: En Clean Architecture + CQRS, las queries usan directamente
        el read repository. No hay una clase ArticleQueries separada.
        """
        # Retornar el read repository directamente
        return self.get_article_read_repository()

    # === DOMAIN SERVICES ===

    def get_quality_service(self):
        """ArticleQualityService - Evalúa calidad de artículos."""
        if self._quality_service is None:
            from src.rss.article.infra.services import ArticleQualityService

            self._quality_service = ArticleQualityService()
        return self._quality_service

    def get_deduplication_service(self):
        """ArticleDeduplicationService - Detecta duplicados (legacy)."""
        if self._deduplication_service is None:
            from src.rss.article.infra.services import ArticleDeduplicationService

            self._deduplication_service = ArticleDeduplicationService(
                similarity_threshold=0.85,
                article_queries=self.get_article_queries(),
            )
        return self._deduplication_service

    def get_semantic_deduplication_service(self):
        """
        SemanticDeduplicationService - Detecta duplicados usando embeddings.

        NOTA: Este servicio usa ContentChunkReadRepository del Chunking BC.
        La dependencia cross-BC se inyecta desde SharedContainer.
        """
        if self._semantic_deduplication_service is None:
            from src.rss.article.domain.services import SemanticDeduplicationService
            from src.shared.config.deduplication_config import DeduplicationConfig

            # Cargar configuración
            config = DeduplicationConfig()

            # Obtener repository de chunks (cross-BC)
            chunk_repo = self._get_article_embedding_read_repository()

            self._semantic_deduplication_service = SemanticDeduplicationService(
                chunk_read_repository=chunk_repo,
                similarity_threshold=config.similarity_threshold,
                logger=self._shared.logger,
            )
        return self._semantic_deduplication_service

    def _get_article_embedding_read_repository(self):
        """
        Helper para obtener ContentChunkReadRepository.

        NOTA: Dependencia cross-BC (Chunking BC).
        Usamos ContentChunkReadRepository porque los embeddings están en los chunks.

        TODO: Refactorizar para inyectar desde ApplicationContainer.
        """
        from src.chunking.infra.persistence.repositories.content_chunk_read_repository import (
            SqlAlchemyContentChunkReadRepository,
        )

        return SqlAlchemyContentChunkReadRepository(
            session=self._shared.session_factory(),
        )

    def get_language_detector(self):
        """Language detector (FastText adapter)."""
        if self._language_detector is None:
            from src.rss.article.infra.external import LanguageDetector

            self._language_detector = LanguageDetector()
        return self._language_detector

    def get_language_detection_service(self):
        """ArticleLanguageDetectionService - Detecta idioma."""
        if self._language_detection_service is None:
            from src.rss.article.domain.services import ArticleLanguageDetectionService

            self._language_detection_service = ArticleLanguageDetectionService(
                language_detector=self.get_language_detector()
            )
        return self._language_detection_service

    def get_metrics_calculation_service(self):
        """ArticleMetricsCalculationService - Calcula métricas."""
        if self._metrics_calculation_service is None:
            from src.rss.article.domain.services import ArticleMetricsCalculationService

            self._metrics_calculation_service = ArticleMetricsCalculationService()
        return self._metrics_calculation_service

    def get_summary_extraction_service(self):
        """ArticleSummaryExtractionService - Genera summaries de artículos."""
        if self._summary_extraction_service is None:
            from src.rss.article.domain.services import ArticleSummaryExtractionService

            self._summary_extraction_service = ArticleSummaryExtractionService()
        return self._summary_extraction_service

    def get_plaintext_extraction_service(self) -> "IArticlePlaintextExtractionService":
        """ArticlePlaintextExtractionService - Extrae texto plano."""
        if self._plaintext_extraction_service is None:
            from src.rss.article.domain.services import (
                ArticlePlaintextExtractionService,
            )

            self._plaintext_extraction_service = ArticlePlaintextExtractionService(
                html_converter=self.get_html_to_plaintext_converter()
            )
        return self._plaintext_extraction_service

    # === EXTERNAL SERVICES ===

    def get_scraping_service(self):
        """SmartScraperService - Servicio inteligente de scraping."""
        if self._scraping_service is None:
            from src.rss.article.domain.services import SmartScraperService
            from src.rss.article.infra.external import (
                PlaywrightScraperService,
                TrafilaturaScraperService,
            )

            # Crear scrapers individuales
            playwright_scraper = PlaywrightScraperService(logger=self._shared.logger)
            trafilatura_scraper = TrafilaturaScraperService(logger=self._shared.logger)

            # Crear smart scraper que auto-selecciona
            self._scraping_service = SmartScraperService(
                playwright_scraper=playwright_scraper,
                trafilatura_scraper=trafilatura_scraper,
            )
        return self._scraping_service

    def get_html_to_markdown_converter(self):
        """HTML to Markdown converter."""
        if self._html_to_markdown_converter is None:
            from src.rss.article.infra.external import HtmlToMarkdownConverter

            self._html_to_markdown_converter = HtmlToMarkdownConverter()
        return self._html_to_markdown_converter

    def get_html_to_plaintext_converter(self):
        """HTML to Plaintext converter."""
        if self._html_to_plaintext_converter is None:
            from src.rss.article.infra.external import HtmlToPlaintextConverter

            self._html_to_plaintext_converter = HtmlToPlaintextConverter()
        return self._html_to_plaintext_converter

    def get_keyword_service(self):
        """ArticleKeywordService - Extrae keywords."""
        if self._keyword_service is None:
            from src.rss.article.infra.services.keyword import ArticleKeywordService

            self._keyword_service = ArticleKeywordService()
        return self._keyword_service

    # === PROCESS MANAGERS ===

    def get_content_extraction_initiator(self):
        """
        ContentExtractionInitiator - Process Manager para iniciar extracción.

        Responsabilidad: Maneja ScrapingCompleted (cross-BC) e inicia procesamiento.

        CQRS Estricto:
        - Usa Mediator para Queries (GetPendingArticlesQuery)
        - Usa Mediator para Commands (ScrapeArticleContentCommand)
        - NO accede directamente a ReadRepository

        SINGLETON: Debe ser singleton para mantener estado entre eventos.
        """
        if self._content_extraction_initiator is None:
            from src.rss.article.app.process_managers import ContentExtractionInitiator

            self._content_extraction_initiator = ContentExtractionInitiator(
                mediator=self._shared.mediator,
                logger=self._shared.logger,
            )
        return self._content_extraction_initiator

    def get_content_extraction_pipeline(self):
        """
        ArticleContentExtractionPipeline - Process Manager para extracción de contenido.

        Responsabilidad: Coordina HTML → Plaintext → Markdown.

        SINGLETON: Debe ser singleton para mantener estado entre eventos.
        """
        if self._content_extraction_pipeline is None:
            from src.rss.article.app.process_managers import (
                ArticleContentExtractionPipeline,
            )

            self._content_extraction_pipeline = ArticleContentExtractionPipeline(
                command_bus=self._shared.mediator,
                logger=self._shared.logger,
            )
        return self._content_extraction_pipeline

    def get_content_analysis_pipeline(self):
        """
        ArticleContentAnalysisPipeline - Process Manager para análisis NLP.

        Responsabilidad: Coordina Metrics → Language → Summary → Keywords → Quality.

        SINGLETON: Debe ser singleton para mantener estado entre eventos.
        """
        if self._content_analysis_pipeline is None:
            from src.rss.article.app.process_managers import (
                ArticleContentAnalysisPipeline,
            )

            self._content_analysis_pipeline = ArticleContentAnalysisPipeline(
                command_bus=self._shared.mediator,
                logger=self._shared.logger,
            )
        return self._content_analysis_pipeline

    # === COMMAND HANDLERS ===

    def get_start_processing_handler(self):
        """StartArticleProcessingHandler - Punto de entrada único para procesamiento.

        CQRS Estricto: Usa WriteRepository.
        Unit of Work: session_factory inyectado por patrón consistente.
        """
        if self._start_processing_handler is None:
            from src.rss.article.app.commands.start_processing import (
                StartArticleProcessingHandler,
            )

            self._start_processing_handler = StartArticleProcessingHandler(
                article_repository=self.get_article_write_repository(),
                session_factory=self._shared.session_factory,
                event_bus=self._shared.event_publisher,
                logger=self._shared.logger,
            )
        return self._start_processing_handler

    def get_scrape_content_handler(self):
        """
        ScrapeArticleContentHandler - Scrapea contenido HTML.

        CRÍTICO: El handler recibe session_factory y crea una NUEVA sesión
        en cada invocación de handle() para evitar sesiones stale.
        """
        from src.rss.article.app.commands.scrape_content import (
            ScrapeArticleContentHandler,
        )

        # NOTA: Dependencia cross-BC - idealmente debería inyectarse desde fuera
        # Por ahora, acceder vía shared container si está disponible
        source_read_repository = self._get_source_read_repository()

        return ScrapeArticleContentHandler(
            session_factory=self._shared.session_factory,  # ← Factory, no sesión
            source_read_repository=source_read_repository,
            scraper_service=self.get_scraping_service(),
            event_bus=self._shared.event_publisher,
            logger=self._shared.logger,
        )

    def _get_source_read_repository(self):
        """
        Helper para obtener SourceReadRepository.

        NOTA: Dependencia cross-BC. Idealmente debería inyectarse desde fuera
        del container, pero por ahora lo creamos aquí para mantener funcionando.

        TODO: Refactorizar para inyectar desde ApplicationContainer.
        """
        from src.rss.feed.infra.persistence.repositories import SourceReadRepository

        return SourceReadRepository(
            session=self._shared.session_factory(),
            logger=self._shared.logger,
        )

    def get_extract_plaintext_handler(self):
        """
        ExtractArticlePlaintextHandler - Extrae plaintext del HTML.

        CQRS Estricto: Solo inyecta WriteRepository.
        Unit of Work: Maneja transacciones atómicas.
        Los datos vienen del evento ArticleContentScraped.

        CRÍTICO: Pasa session_factory para que el handler cree una NUEVA sesión
        en cada invocación de handle(), evitando problemas de concurrencia.
        """
        from src.rss.article.app.commands.extract_plaintext import (
            ExtractArticlePlaintextHandler,
        )

        return ExtractArticlePlaintextHandler(
            session_factory=self._shared.session_factory,
            plaintext_service=self.get_plaintext_extraction_service(),
            event_bus=self._shared.event_publisher,
            logger=self._shared.logger,
        )

    def get_convert_to_markdown_handler(self):
        """
        ConvertArticleToMarkdownHandler - Convierte HTML a Markdown.

        CRÍTICO: Pasa session_factory para crear nueva sesión en cada invocación.
        """
        from src.rss.article.app.commands.convert_to_markdown import (
            ConvertArticleToMarkdownHandler,
        )

        return ConvertArticleToMarkdownHandler(
            session_factory=self._shared.session_factory,
            html_to_markdown_converter=self.get_html_to_markdown_converter(),
            event_bus=self._shared.event_publisher,
            logger=self._shared.logger,
        )

    def get_calculate_article_metrics_validator(self):
        """Validator para CalculateArticleMetrics command."""
        from src.rss.article.app.commands.calculate_metrics.validator import (
            CalculateArticleMetricsValidator,
        )

        return CalculateArticleMetricsValidator()

    def get_calculate_article_metrics_handler(self):
        """
        CalculateArticleMetricsHandler - Calcula métricas del artículo.

        CQRS Estricto: Solo inyecta WriteRepository.
        Unit of Work: Maneja transacciones atómicas.
        Los datos vienen del evento ArticleMarkdownConverted.

        CRÍTICO: Repositorio y UoW comparten la MISMA sesión.
        """
        from src.rss.article.app.commands.calculate_metrics import (
            CalculateArticleMetricsHandler,
        )
        from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
            RssArticleWriteRepository,
        )
        from src.shared.kernel.uow import SqlAlchemyUnitOfWork

        return CalculateArticleMetricsHandler(
            session_factory=self._shared.session_factory,
            metrics_service=self.get_metrics_calculation_service(),
            validator=self.get_calculate_article_metrics_validator(),
            event_bus=self._shared.event_publisher,
            logger=self._shared.logger,
        )

    def get_detect_language_handler(self):
        """
        DetectArticleLanguageHandler - Detecta idioma del artículo.

        CRÍTICO: Pasa session_factory para crear nueva sesión en cada invocación.
        """
        from src.rss.article.app.commands.detect_language import (
            DetectArticleLanguageHandler,
        )

        return DetectArticleLanguageHandler(
            session_factory=self._shared.session_factory,
            language_detection_service=self.get_language_detection_service(),
            logger=self._shared.logger,
        )

    def get_generate_summary_validator(self):
        """Validator para GenerateArticleSummary command."""
        from src.rss.article.app.commands.generate_summary.validator import (
            GenerateArticleSummaryValidator,
        )

        return GenerateArticleSummaryValidator()

    def get_generate_summary_handler(self):
        """
        GenerateArticleSummaryHandler - Genera resumen del artículo.

        CRÍTICO: Repositorio y UoW comparten la MISMA sesión.
        """
        from src.rss.article.app.commands.generate_summary import (
            GenerateArticleSummaryHandler,
        )
        from src.rss.article.infra.persistence.repositories.rss_article_write_repository import (
            RssArticleWriteRepository,
        )
        from src.shared.kernel.uow import SqlAlchemyUnitOfWork

        return GenerateArticleSummaryHandler(
            session_factory=self._shared.session_factory,
            summary_service=self.get_summary_extraction_service(),
            validator=self.get_generate_summary_validator(),
            event_bus=self._shared.event_publisher,
            logger=self._shared.logger,
        )

    def get_extract_keywords_validator(self):
        """Validator para ExtractArticleKeywords command."""
        from src.rss.article.app.commands.extract_keywords.validator import (
            ExtractArticleKeywordsValidator,
        )

        return ExtractArticleKeywordsValidator()

    def get_extract_keywords_handler(self):
        """
        ExtractArticleKeywordsHandler - Extrae keywords del artículo.

        CRÍTICO: Pasa session_factory para crear nueva sesión en cada invocación.
        """
        from src.rss.article.app.commands.extract_keywords import (
            ExtractArticleKeywordsHandler,
        )

        return ExtractArticleKeywordsHandler(
            session_factory=self._shared.session_factory,
            keyword_service=self.get_keyword_service(),
            validator=self.get_extract_keywords_validator(),
            logger=self._shared.logger,
        )

    def get_calculate_quality_handler(self):
        """
        CalculateArticleQualityHandler - Calcula calidad del artículo.

        CRÍTICO: Pasa session_factory para crear nueva sesión en cada invocación.
        """
        from src.rss.article.app.commands.calculate_quality import (
            CalculateArticleQualityHandler,
        )

        return CalculateArticleQualityHandler(
            session_factory=self._shared.session_factory,
            quality_service=self.get_quality_service(),
            event_bus=self._shared.event_publisher,
            logger=self._shared.logger,
        )

    def get_detect_duplicate_handler(self):
        """
        DetectDuplicateArticleHandler - Detecta duplicados usando embeddings.

        NOTA: Este handler es read-only (no modifica estado).
        NO necesita UoW ni WriteRepository.
        """
        if self._detect_duplicate_handler is None:
            from src.rss.article.app.commands.detect_duplicate import (
                DetectDuplicateArticleHandler,
            )

            self._detect_duplicate_handler = DetectDuplicateArticleHandler(
                deduplication_service=self.get_semantic_deduplication_service(),
                logger=self._shared.logger,
            )
        return self._detect_duplicate_handler

    # === QUERY HANDLERS (CQRS Read Side) ===

    def get_get_article_by_id_handler(self):
        """GetArticleByIdHandler - Query para obtener artículo por ID."""
        if self._get_article_by_id_handler is None:
            from src.rss.article.app.queries.get_by_id import (
                GetArticleByIdHandler,
            )

            self._get_article_by_id_handler = GetArticleByIdHandler(
                read_repository=self.get_article_read_repository(),
                logger=self._shared.logger,
            )
        return self._get_article_by_id_handler

    def get_get_pending_articles_handler(self):
        """GetPendingArticlesHandler - Query para obtener artículos pendientes."""
        if self._get_pending_articles_handler is None:
            from src.rss.article.app.queries.get_pending import (
                GetPendingArticlesHandler,
            )

            self._get_pending_articles_handler = GetPendingArticlesHandler(
                read_repository=self.get_article_read_repository(),
                logger=self._shared.logger,
            )
        return self._get_pending_articles_handler

    def get_get_article_stats_handler(self):
        """GetArticleStatsHandler - Query para obtener estadísticas de artículos."""
        if not hasattr(self, "_get_article_stats_handler"):
            self._get_article_stats_handler = None

        if self._get_article_stats_handler is None:
            from src.rss.article.app.queries.get_stats import (
                GetArticleStatsHandler,
            )

            self._get_article_stats_handler = GetArticleStatsHandler(
                article_queries=self.get_article_queries(),
            )
        return self._get_article_stats_handler

    # === HANDLER REGISTRATION ===

    def register_handlers(self) -> None:
        """
        Registra todos los handlers del bounded context Article.

        Arquitectura event-driven con Event Handlers Granulares (Opción 1):

        Flujo de Extracción:
        1. ArticleContentScraped → ExtractPlaintext
        2. ArticlePlaintextExtracted → ConvertMarkdown
        3. ArticleMarkdownConverted → CalculateMetrics

        Flujo de Análisis NLP:
        4. ArticleMetricsCalculated → DetectLanguage
        5. ArticleLanguageDetected → GenerateSummary
        6. ArticleSummaryGenerated → ExtractKeywords
        7. ArticleKeywordsExtracted → CalculateQuality
        8. ArticleQualityCalculated → Completado ✅

        Ventajas:
        - Handlers pequeños y simples (30-50 líneas)
        - Desacoplados entre sí
        - Fácil de testear
        - Fácil de extender (agregar pasos)

        Incluye:
        - Command handlers en Mediator
        - Query handlers en Mediator (CQRS Read Side)
        - Event handlers granulares en EventHandlerRegistry
        """
        self._register_command_handlers()
        self._register_query_handlers()
        self._register_event_handlers()

        self._shared.logger.info(
            "ArticleContainer: handlers registrados (event-driven architecture)",
        )

    def _register_command_handlers(self) -> None:
        """Registra command handlers en el Mediator."""
        from src.rss.article.app.commands.calculate_metrics import (
            CalculateArticleMetricsCommand,
        )
        from src.rss.article.app.commands.calculate_quality import (
            CalculateArticleQualityCommand,
        )
        from src.rss.article.app.commands.convert_to_markdown import (
            ConvertArticleToMarkdownCommand,
        )
        from src.rss.article.app.commands.detect_language import (
            DetectArticleLanguageCommand,
        )
        from src.rss.article.app.commands.detect_duplicate import (
            DetectDuplicateArticleCommand,
        )
        from src.rss.article.app.commands.extract_keywords import (
            ExtractArticleKeywordsCommand,
        )
        from src.rss.article.app.commands.extract_plaintext import (
            ExtractArticlePlaintextCommand,
        )
        from src.rss.article.app.commands.generate_summary import (
            GenerateArticleSummaryCommand,
        )
        from src.rss.article.app.commands.scrape_content import (
            ScrapeArticleContentCommand,
        )
        from src.rss.article.app.commands.start_processing import (
            StartArticleProcessingCommand,
        )

        handlers_registered = []

        # StartArticleProcessingHandler - Punto de entrada único para procesamiento
        self._shared.register_handler(
            StartArticleProcessingCommand,
            self.get_start_processing_handler(),
        )
        handlers_registered.append("StartArticleProcessingHandler")

        # Pipeline de Extracción
        self._shared.register_handler(
            ScrapeArticleContentCommand,
            self.get_scrape_content_handler(),
        )
        handlers_registered.append("ScrapeArticleContentHandler")

        self._shared.register_handler(
            ExtractArticlePlaintextCommand,
            self.get_extract_plaintext_handler(),
        )
        handlers_registered.append("ExtractArticlePlaintextHandler")

        self._shared.register_handler(
            ConvertArticleToMarkdownCommand,
            self.get_convert_to_markdown_handler(),
        )
        handlers_registered.append("ConvertArticleToMarkdownHandler")

        self._shared.register_handler(
            CalculateArticleMetricsCommand,
            self.get_calculate_article_metrics_handler(),
        )
        handlers_registered.append("CalculateArticleMetricsHandler")

        # Pipeline de Análisis NLP
        self._shared.register_handler(
            DetectArticleLanguageCommand,
            self.get_detect_language_handler(),
        )
        handlers_registered.append("DetectArticleLanguageHandler")

        self._shared.register_handler(
            GenerateArticleSummaryCommand,
            self.get_generate_summary_handler(),
        )
        handlers_registered.append("GenerateArticleSummaryHandler")

        self._shared.register_handler(
            ExtractArticleKeywordsCommand,
            self.get_extract_keywords_handler(),
        )
        handlers_registered.append("ExtractArticleKeywordsHandler")

        self._shared.register_handler(
            CalculateArticleQualityCommand,
            self.get_calculate_quality_handler(),
        )
        handlers_registered.append("CalculateArticleQualityHandler")

        # Deduplication (Semantic)
        self._shared.register_handler(
            DetectDuplicateArticleCommand,
            self.get_detect_duplicate_handler(),
        )
        handlers_registered.append("DetectDuplicateArticleHandler")

        self._shared.logger.info(
            "Command handlers registrados en Mediator",
            handlers=handlers_registered,
            count=len(handlers_registered),
        )

    def _register_process_manager_method(
        self,
        event_type: type,
        method: Callable,
        method_name: str,
        handlers_list: list[str],
    ) -> None:
        """
        Helper para registrar método de Process Manager como event handler.

        Args:
            event_type: Tipo de evento a escuchar
            method: Método del Process Manager
            method_name: Nombre descriptivo para logging
            handlers_list: Lista para trackear handlers registrados
        """
        self._shared.event_handler_registry.register_handler(
            event_type,
            ProcessManagerMethodWrapper(method, method_name),
        )
        handlers_list.append(method_name)

    def _register_query_handlers(self) -> None:
        """
        Registra query handlers en el Mediator (CQRS Read Side).

        Query Handlers:
        - GetArticleByIdQuery → GetArticleByIdHandler
        - GetPendingArticlesQuery → GetPendingArticlesHandler
        - GetArticleStatsQuery → GetArticleStatsHandler

        CQRS Estricto:
        - Queries solo leen (no modifican estado)
        - Devuelven DTOs (sin comportamiento)
        - Registrados en Mediator (como Commands)
        """
        from src.rss.article.app.queries.get_by_id import GetArticleByIdQuery
        from src.rss.article.app.queries.get_pending import (
            GetPendingArticlesQuery,
        )
        from src.rss.article.app.queries.get_stats import GetArticleStatsQuery

        queries_registered = []

        # GetArticleByIdQuery
        self._shared.register_handler(
            GetArticleByIdQuery,
            self.get_get_article_by_id_handler(),
        )
        queries_registered.append("GetArticleByIdHandler")

        # GetPendingArticlesQuery
        self._shared.register_handler(
            GetPendingArticlesQuery,
            self.get_get_pending_articles_handler(),
        )
        queries_registered.append("GetPendingArticlesHandler")

        # GetArticleStatsQuery
        self._shared.register_handler(
            GetArticleStatsQuery,
            self.get_get_article_stats_handler(),
        )
        queries_registered.append("GetArticleStatsHandler")

        self._shared.logger.info(
            "Query handlers registrados en Mediator (CQRS Read Side)",
            queries=queries_registered,
            count=len(queries_registered),
        )

    def _register_event_handlers(self) -> None:
        """
        Registra event handlers y process managers en Event Bus.

        ARQUITECTURA: Process Manager (Escuela 2)

        Event Handlers (solo 2):
        - OnScrapingCompletedHandler: Cross-BC, delega a ContentExtractionInitiator
        - OnArticleQualityCalculatedHandler: Fin del pipeline (solo log)

        Process Managers (registrados directamente):
        - ContentExtractionInitiator: Inicia procesamiento después de scraping
        - ArticleContentExtractionPipeline: HTML → Plaintext → Markdown
        - ArticleContentAnalysisPipeline: Metrics → Language → Summary → Keywords → Quality

        Flujo completo:
        1. ScrapingCompleted → ContentExtractionInitiator → ScrapeArticleContentCommand
        2. ArticleContentScraped → ArticleContentExtractionPipeline.on_content_scraped()
        3. ArticlePlaintextExtracted → ArticleContentExtractionPipeline.on_plaintext_extracted()
        4. ArticleMarkdownConverted → ArticleContentAnalysisPipeline.on_markdown_converted()
        5. ArticleMetricsCalculated → ArticleContentAnalysisPipeline.on_metrics_calculated()
        6. ArticleLanguageDetected → ArticleContentAnalysisPipeline.on_language_detected()
        7. ArticleSummaryGenerated → ArticleContentAnalysisPipeline.on_summary_generated()
        8. ArticleKeywordsExtracted → ArticleContentAnalysisPipeline.on_keywords_extracted()
        9. ArticleQualityCalculated → ArticleContentAnalysisPipeline.on_quality_calculated()
        10. ArticleQualityCalculated → OnArticleQualityCalculatedHandler (fin)
        """
        from src.rss.article.app.event_handlers import (
            OnArticleQualityCalculatedHandler,
            OnScrapingCompletedHandler,
        )
        from src.rss.article.domain.events import (
            ArticleContentScraped,
            ArticleKeywordsExtracted,
            ArticleLanguageDetected,
            ArticleMarkdownConverted,
            ArticleMetricsCalculated,
            ArticlePlaintextExtracted,
            ArticleQualityCalculated,
            ArticleSummaryGenerated,
        )

        handlers_registered = []

        # === EVENT HANDLERS (Solo 3) ===

        # 1. Cross-BC: ScrapingCompleted → ContentExtractionInitiator
        from src.scraping.domain.events import ScrapingCompleted

        self._shared.event_handler_registry.register_handler(
            ScrapingCompleted,
            OnScrapingCompletedHandler(
                content_extraction_initiator=self.get_content_extraction_initiator(),
                logger=self._shared.logger,
            ),
        )
        handlers_registered.append("OnScrapingCompletedHandler (cross-BC)")

        # 2. Fin del pipeline: ArticleQualityCalculated → Log éxito (mantener para observabilidad)
        self._shared.event_handler_registry.register_handler(
            ArticleQualityCalculated,
            OnArticleQualityCalculatedHandler(
                logger=self._shared.logger,
            ),
        )
        handlers_registered.append("OnArticleQualityCalculatedHandler (fin)")

        # === PROCESS MANAGERS (Registrados con wrappers) ===

        # Process Manager: ArticleContentExtractionPipeline
        extraction_pipeline = self.get_content_extraction_pipeline()

        self._register_process_manager_method(
            ArticleContentScraped,
            extraction_pipeline.on_content_scraped,
            "ArticleContentExtractionPipeline.on_content_scraped",
            handlers_registered,
        )

        self._register_process_manager_method(
            ArticlePlaintextExtracted,
            extraction_pipeline.on_plaintext_extracted,
            "ArticleContentExtractionPipeline.on_plaintext_extracted",
            handlers_registered,
        )

        self._register_process_manager_method(
            ArticleMarkdownConverted,
            extraction_pipeline.on_markdown_converted,
            "ArticleContentExtractionPipeline.on_markdown_converted",
            handlers_registered,
        )

        # Process Manager: ArticleContentAnalysisPipeline
        analysis_pipeline = self.get_content_analysis_pipeline()

        self._register_process_manager_method(
            ArticleMarkdownConverted,
            analysis_pipeline.on_markdown_converted,
            "ArticleContentAnalysisPipeline.on_markdown_converted",
            handlers_registered,
        )

        self._register_process_manager_method(
            ArticleMetricsCalculated,
            analysis_pipeline.on_metrics_calculated,
            "ArticleContentAnalysisPipeline.on_metrics_calculated",
            handlers_registered,
        )

        self._register_process_manager_method(
            ArticleLanguageDetected,
            analysis_pipeline.on_language_detected,
            "ArticleContentAnalysisPipeline.on_language_detected",
            handlers_registered,
        )

        self._register_process_manager_method(
            ArticleSummaryGenerated,
            analysis_pipeline.on_summary_generated,
            "ArticleContentAnalysisPipeline.on_summary_generated",
            handlers_registered,
        )

        self._register_process_manager_method(
            ArticleKeywordsExtracted,
            analysis_pipeline.on_keywords_extracted,
            "ArticleContentAnalysisPipeline.on_keywords_extracted",
            handlers_registered,
        )

        self._register_process_manager_method(
            ArticleQualityCalculated,
            analysis_pipeline.on_quality_calculated,
            "ArticleContentAnalysisPipeline.on_quality_calculated",
            handlers_registered,
        )

        self._shared.logger.info(
            "ArticleContainer: Process Managers y Event Handlers registrados",
            handlers=handlers_registered,
            count=len(handlers_registered),
        )


# Alias para compatibilidad
ArticleContainer = RssArticleContainer
