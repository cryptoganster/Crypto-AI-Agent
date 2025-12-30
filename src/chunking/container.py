"""Chunking Bounded Context Container.

Container de inversión de dependencias para el bounded context Chunking.
Sigue Clean Architecture + DDD + CQRS.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.rss.article.container import ArticleContainer
    from src.shared.container import SharedContainer


class ChunkingContainer:
    """
    Container del bounded context Chunking.

    Responsabilidades:
    - Event Handlers: OnArticleQualityCalculatedHandler
    - Commands: ChunkArticleCommand, GenerateChunkEmbeddingsCommand, etc.
    - Queries: GetProcessingStatusQuery, GetArticleChunksQuery, etc.
    - Services: ChunkingService, EmbeddingService, SummarizationService
    - Process Managers: ArticleAIProcessingPipeline
    - Repositories: ContentChunkReadRepository, ContentChunkWriteRepository

    Requirements: 10.1
    """

    def __init__(self, shared: "SharedContainer", article: "ArticleContainer"):
        self._shared = shared
        self._article = article

        # Configuration (Lazy)
        self._ai_processing_config = None

        # Command Handlers (Lazy)
        self._chunk_article_handler = None
        self._generate_chunk_embeddings_handler = None
        self._generate_chunk_summaries_handler = None
        self._persist_chunks_handler = None
        self._generate_global_summary_handler = None
        self._generate_tldr_handler = None

        # Query Handlers (Lazy)
        self._get_processing_status_handler = None
        self._get_article_chunks_handler = None
        self._get_processing_metrics_handler = None

        # Process Managers (Lazy)
        self._article_ai_processing_pipeline = None

        # Domain Services (Lazy)
        self._chunking_service = None
        self._chunk_validation_service = None
        self._summarization_service = None

        # Repositories (Lazy)
        self._content_chunk_read_repository = None
        self._content_chunk_write_repository = None

        # External Services (Lazy)
        self._token_encoder = None
        self._text_splitter = None
        self._embedding_service = None
        self._vector_store = None

    # === CONFIGURATION ===

    def get_ai_processing_config(self):
        """
        Factory para AIProcessingConfig (singleton).

        Requirements: 3.1
        """
        if self._ai_processing_config is None:
            from src.shared.config.ai_processing_config import AIProcessingConfig

            self._ai_processing_config = AIProcessingConfig.from_env()

        return self._ai_processing_config

    # === DOMAIN SERVICES ===

    def get_chunking_service(self):
        """
        Factory para ChunkingService.

        Requirements: 10.1.1, 10.1.4, 2.1
        """
        if self._chunking_service is None:
            from src.chunking.domain.services.chunking import ChunkingService
            from src.shared.config.chunking_config import ChunkingConfig

            # Usar ChunkingConfig para parámetros de chunking
            config = ChunkingConfig.from_env()

            self._chunking_service = ChunkingService(
                token_encoder=self.get_token_encoder(),
                text_splitter=self.get_text_splitter(),
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
            )

        return self._chunking_service

    def get_chunk_validation_service(self):
        """
        Factory para ChunkValidationService.

        Requirements: 2.1, 2.2
        """
        if self._chunk_validation_service is None:
            from src.chunking.domain.services.chunk_validation import (
                ChunkValidationService,
            )

            self._chunk_validation_service = ChunkValidationService()

        return self._chunk_validation_service

    def get_summarization_service(self):
        """
        Factory para SummarizationService.

        Requirements: 2.1, 2.2
        """
        if self._summarization_service is None:
            from src.rag.domain.services.summarization import SummarizationService

            # TODO: Inyectar LLM service real cuando esté configurado
            # Por ahora usamos None - el servicio debe manejar este caso
            self._summarization_service = SummarizationService(
                llm_service=None,  # type: ignore
            )

        return self._summarization_service

    def get_token_encoder(self):
        """
        Factory para ITokenEncoder.

        Requirements: 10.1.1
        """
        if self._token_encoder is None:
            from src.chunking.infra.external import LangChainTokenEncoder

            self._token_encoder = LangChainTokenEncoder()

        return self._token_encoder

    def get_text_splitter(self):
        """
        Factory para ITextSplitter.

        Requirements: 10.1.1
        """
        if self._text_splitter is None:
            from src.chunking.infra.external import LangChainMarkdownSplitter

            self._text_splitter = LangChainMarkdownSplitter(
                token_encoder=self.get_token_encoder()
            )

        return self._text_splitter

    def get_embedding_service(self):
        """
        Factory para IEmbeddingService (migrado desde EmbeddingContainer).

        Usa OllamaEmbeddingAdapter para generar embeddings localmente.

        Requirements: 10.2.1, 10.2.5
        """
        if not hasattr(self, "_embedding_service"):
            self._embedding_service = None

        if self._embedding_service is None:
            from src.chunking.infra.external.ollama_embedding_adapter import (
                OllamaEmbeddingAdapter,
            )
            from src.shared.config.embedding_config import EmbeddingConfig

            # Obtener configuración de embedding desde environment
            embedding_config = EmbeddingConfig.from_env()

            self._embedding_service = OllamaEmbeddingAdapter(
                model_name=embedding_config.embedding_model,
                base_url=embedding_config.ollama_base_url,
                dimension=embedding_config.embedding_dimension,
                batch_size=embedding_config.batch_size,
            )

        return self._embedding_service

    def get_vector_store(self):
        """
        Factory para IVectorStore (migrado desde EmbeddingContainer).

        Usa PgVectorStoreAdapter para almacenar embeddings en PostgreSQL.

        Requirements: 10.2.1
        """
        if not hasattr(self, "_vector_store"):
            self._vector_store = None

        if self._vector_store is None:
            from src.chunking.infra.persistence.pg_vector_store_adapter import (
                PgVectorStoreAdapter,
            )

            # Crear nueva sesión para cada request
            session = self._shared.session_factory()

            self._vector_store = PgVectorStoreAdapter(
                session=session,
                logger=self._shared.logger,
            )

        return self._vector_store

    # === REPOSITORIES ===

    def get_content_chunk_read_repository(self):
        """
        Factory para ContentChunkReadRepository.

        Requirements: 10.1.1
        """
        if self._content_chunk_read_repository is None:
            from src.chunking.infra.persistence.repositories.content_chunk_read_repository import (
                SqlAlchemyContentChunkReadRepository,
            )

            # Crear nueva sesión para cada request
            session = self._shared.session_factory()

            self._content_chunk_read_repository = SqlAlchemyContentChunkReadRepository(
                session=session
            )

        return self._content_chunk_read_repository

    def get_content_chunk_write_repository(self):
        """
        Factory para ContentChunkWriteRepository.

        Requirements: 10.1.1
        """
        if self._content_chunk_write_repository is None:
            from src.chunking.infra.persistence.repositories.content_chunk_write_repository import (
                SqlAlchemyContentChunkWriteRepository,
            )

            # Crear nueva sesión para cada request
            session = self._shared.session_factory()

            self._content_chunk_write_repository = (
                SqlAlchemyContentChunkWriteRepository(session=session)
            )

        return self._content_chunk_write_repository

    # === COMMAND HANDLERS ===

    def get_chunk_article_handler(self):
        """
        Factory para ChunkArticleHandler.

        Requirements: 5.1
        """
        if self._chunk_article_handler is None:
            from src.chunking.app.commands.chunk_article.handler import (
                ChunkArticleHandler,
            )
            from src.shared.kernel.uow import SqlAlchemyUnitOfWork

            # Crear UoW
            session = self._shared.session_factory()
            uow = SqlAlchemyUnitOfWork(session, self._shared.logger)

            self._chunk_article_handler = ChunkArticleHandler(
                chunking_service=self.get_chunking_service(),
                chunk_repository=self.get_content_chunk_write_repository(),
                uow=uow,
                config=self.get_ai_processing_config(),
                logger=self._shared.logger,
            )

        return self._chunk_article_handler

    def get_generate_chunk_embeddings_handler(self):
        """
        Factory para GenerateChunkEmbeddingsHandler.

        Requirements: 5.2
        """
        if self._generate_chunk_embeddings_handler is None:
            from src.chunking.app.commands.generate_chunk_embeddings.handler import (
                GenerateChunkEmbeddingsHandler,
            )

            self._generate_chunk_embeddings_handler = GenerateChunkEmbeddingsHandler(
                embedding_service=self.get_embedding_service(),
                chunk_read_repository=self.get_content_chunk_read_repository(),
                chunk_write_repository=self.get_content_chunk_write_repository(),
                config=self.get_ai_processing_config(),
                logger=self._shared.logger,
            )

        return self._generate_chunk_embeddings_handler

    def get_generate_chunk_summaries_handler(self):
        """
        Factory para GenerateChunkSummariesHandler.

        Requirements: 5.3
        """
        if self._generate_chunk_summaries_handler is None:
            from src.chunking.app.commands.generate_chunk_summaries.handler import (
                GenerateChunkSummariesHandler,
            )

            self._generate_chunk_summaries_handler = GenerateChunkSummariesHandler(
                summarization_service=self.get_summarization_service(),
                chunk_read_repository=self.get_content_chunk_read_repository(),
                chunk_write_repository=self.get_content_chunk_write_repository(),
                config=self._shared.ai_processing_config,
                logger=self._shared.logger,
            )

        return self._generate_chunk_summaries_handler

    def get_persist_chunks_handler(self):
        """
        Factory para PersistChunksHandler.

        Requirements: 5.4
        """
        if self._persist_chunks_handler is None:
            from src.chunking.app.commands.persist_chunks.handler import (
                PersistChunksHandler,
            )
            from src.shared.kernel.uow import SqlAlchemyUnitOfWork

            session = self._shared.session_factory()
            uow = SqlAlchemyUnitOfWork(session, self._shared.logger)

            self._persist_chunks_handler = PersistChunksHandler(
                chunk_repository=self.get_content_chunk_write_repository(),
                vector_store=self.get_vector_store(),
                validation_service=self.get_chunk_validation_service(),
                uow=uow,
                logger=self._shared.logger,
            )

        return self._persist_chunks_handler

    def get_generate_global_summary_handler(self):
        """
        Factory para GenerateGlobalSummaryHandler.

        Requirements: 5.5
        """
        if self._generate_global_summary_handler is None:
            from src.chunking.app.commands.generate_global_summary.handler import (
                GenerateGlobalSummaryHandler,
            )

            self._generate_global_summary_handler = GenerateGlobalSummaryHandler(
                summarization_service=self.get_summarization_service(),
                chunk_repository=self.get_content_chunk_read_repository(),
                article_repository=self._article.get_article_write_repository(),
                config=self.get_ai_processing_config(),
                logger=self._shared.logger,
            )

        return self._generate_global_summary_handler

    def get_generate_tldr_handler(self):
        """
        Factory para GenerateTLDRHandler.

        Requirements: 5.6
        """
        if self._generate_tldr_handler is None:
            from src.chunking.app.commands.generate_tldr.handler import (
                GenerateTLDRHandler,
            )

            self._generate_tldr_handler = GenerateTLDRHandler(
                summarization_service=self.get_summarization_service(),
                chunk_repository=self.get_content_chunk_read_repository(),
                article_repository=self._article.get_article_write_repository(),
                logger=self._shared.logger,
            )

        return self._generate_tldr_handler

    # === QUERY HANDLERS ===

    def get_get_article_processing_status_handler(self):
        """
        Factory para GetArticleProcessingStatusHandler.

        Requirements: 9.1
        """
        if self._get_processing_status_handler is None:
            from src.chunking.app.queries.get_article_processing_status.handler import (
                GetArticleProcessingStatusHandler,
            )

            self._get_processing_status_handler = GetArticleProcessingStatusHandler(
                pipeline_manager=self.get_article_ai_processing_pipeline(),
                logger=self._shared.logger,
            )

        return self._get_processing_status_handler

    def get_get_article_chunks_handler(self):
        """
        Factory para GetArticleChunksHandler.

        Requirements: 9.2
        """
        if self._get_article_chunks_handler is None:
            from src.chunking.app.queries.get_article_chunks.handler import (
                GetArticleChunksHandler,
            )

            self._get_article_chunks_handler = GetArticleChunksHandler(
                chunk_repository=self.get_content_chunk_read_repository(),
                logger=self._shared.logger,
            )

        return self._get_article_chunks_handler

    def get_get_processing_metrics_handler(self):
        """
        Factory para GetProcessingMetricsHandler.

        Requirements: 9.3
        """
        if self._get_processing_metrics_handler is None:
            from src.chunking.app.queries.get_processing_metrics.handler import (
                GetProcessingMetricsHandler,
            )

            self._get_processing_metrics_handler = GetProcessingMetricsHandler(
                pipeline=self.get_article_ai_processing_pipeline(),
                logger=self._shared.logger,
            )

        return self._get_processing_metrics_handler

    # === PROCESS MANAGERS ===

    def get_article_ai_processing_pipeline(self):
        """
        Factory para ArticleAIProcessingPipeline.

        Requirements: 4.1
        """
        if self._article_ai_processing_pipeline is None:
            from src.chunking.app.process_managers.article_ai_processing_pipeline import (
                ArticleAIProcessingPipeline,
            )

            config = self.get_ai_processing_config()

            self._article_ai_processing_pipeline = ArticleAIProcessingPipeline(
                command_bus=self._shared.mediator,
                event_bus=self._shared.mediator,
                logger=self._shared.logger,
                enable_global_summary=config.enable_global_summary,
                enable_tldr=config.enable_tldr,
                max_chunk_failures=3,
                abort_on_failure=False,
            )

        return self._article_ai_processing_pipeline

    # === HANDLER REGISTRATION ===

    def register_handlers(self) -> None:
        """
        Registra todos los handlers del bounded context Chunking.

        Event-Driven Architecture:
        - ArticleQualityCalculated → ArticleAIProcessingPipeline → Commands

        Incluye:
        - Command handlers en Mediator
        - Query handlers en Mediator
        - Event handlers en EventHandlerRegistry
        - Process Manager subscriptions

        Requirements: 10.1.2, 10.1.3, 16.3, 16.4, 16.6
        """
        self._register_command_handlers()
        self._register_query_handlers()
        self._register_event_handlers()

        self._shared.logger.info(
            "ChunkingContainer: handlers registrados (event-driven architecture)",
        )

    def _register_command_handlers(self) -> None:
        """
        Registra command handlers en Mediator.

        Command Handlers:
        - ChunkArticleHandler: Crea chunks de artículo
        - GenerateChunkEmbeddingsHandler: Genera embeddings de chunks
        - GenerateChunkSummariesHandler: Genera summaries de chunks
        - PersistChunksHandler: Persiste chunks en vector store
        - GenerateGlobalSummaryHandler: Genera summary global del artículo
        - GenerateTLDRHandler: Genera TLDR del artículo

        Requirements: 10.1.2, 5.1-5.6, 16.3
        """
        from src.chunking.app.commands.chunk_article.command import (
            ChunkArticleCommand,
        )
        from src.chunking.app.commands.generate_chunk_embeddings.command import (
            GenerateChunkEmbeddingsCommand,
        )
        from src.chunking.app.commands.generate_chunk_summaries.command import (
            GenerateChunkSummariesCommand,
        )
        from src.chunking.app.commands.generate_global_summary.command import (
            GenerateGlobalSummaryCommand,
        )
        from src.chunking.app.commands.generate_tldr.command import (
            GenerateTLDRCommand,
        )
        from src.chunking.app.commands.persist_chunks.command import (
            PersistChunksCommand,
        )

        handlers_registered = []

        # ChunkArticleHandler
        self._shared.register_handler(
            ChunkArticleCommand,
            self.get_chunk_article_handler(),
        )
        handlers_registered.append("CreateArticleChunksHandler")

        # GenerateChunkEmbeddingsHandler
        self._shared.register_handler(
            GenerateChunkEmbeddingsCommand,
            self.get_generate_chunk_embeddings_handler(),
        )
        handlers_registered.append("GenerateChunkEmbeddingsHandler")

        # GenerateChunkSummariesHandler
        self._shared.register_handler(
            GenerateChunkSummariesCommand,
            self.get_generate_chunk_summaries_handler(),
        )
        handlers_registered.append("GenerateChunkSummariesHandler")

        # PersistChunksHandler
        self._shared.register_handler(
            PersistChunksCommand,
            self.get_persist_chunks_handler(),
        )
        handlers_registered.append("PersistChunksHandler")

        # GenerateGlobalSummaryHandler
        self._shared.register_handler(
            GenerateGlobalSummaryCommand,
            self.get_generate_global_summary_handler(),
        )
        handlers_registered.append("GenerateGlobalSummaryHandler")

        # GenerateTLDRHandler
        self._shared.register_handler(
            GenerateTLDRCommand,
            self.get_generate_tldr_handler(),
        )
        handlers_registered.append("GenerateTLDRHandler")

        self._shared.logger.info(
            "Command handlers registrados en Mediator",
            handlers=handlers_registered,
            count=len(handlers_registered),
        )

    def _register_query_handlers(self) -> None:
        """
        Registra query handlers en Mediator.

        Query Handlers:
        - GetArticleProcessingStatusHandler: Obtiene estado de procesamiento
        - GetArticleChunksHandler: Obtiene chunks de artículo
        - GetProcessingMetricsHandler: Obtiene métricas de procesamiento

        Requirements: 9.1-9.3, 16.6
        """
        from src.chunking.app.queries.get_article_chunks.query import (
            GetArticleChunksQuery,
        )
        from src.chunking.app.queries.get_article_processing_status.query import (
            GetArticleProcessingStatusQuery,
        )
        from src.chunking.app.queries.get_processing_metrics.query import (
            GetProcessingMetricsQuery,
        )

        handlers_registered = []

        # GetArticleProcessingStatusHandler
        self._shared.register_handler(
            GetArticleProcessingStatusQuery,
            self.get_get_article_processing_status_handler(),
        )
        handlers_registered.append("GetArticleProcessingStatusHandler")

        # GetArticleChunksHandler
        self._shared.register_handler(
            GetArticleChunksQuery,
            self.get_get_article_chunks_handler(),
        )
        handlers_registered.append("GetArticleChunksHandler")

        # GetProcessingMetricsHandler
        self._shared.register_handler(
            GetProcessingMetricsQuery,
            self.get_get_processing_metrics_handler(),
        )
        handlers_registered.append("GetProcessingMetricsHandler")

        self._shared.logger.info(
            "Query handlers registrados en Mediator",
            handlers=handlers_registered,
            count=len(handlers_registered),
        )

    def _register_event_handlers(self) -> None:
        """
        Registra event handlers en Event Bus.

        Event Handlers:
        - OnArticleQualityCalculatedHandler: Escucha ArticleQualityCalculated del Article BC

        Process Manager Subscriptions:
        - ArticleQualityCalculated: Inicia pipeline de procesamiento
        - ChunkCreatedEvent: Trackea progreso de creación de chunks
        - ChunkEmbeddedEvent: Trackea progreso de embeddings
        - ChunkSummarizedEvent: Trackea progreso de summaries
        - ChunkCompletedEvent: Trackea progreso de persistencia
        - ChunkFailedEvent: Maneja errores en chunks

        Requirements: 10.1.3, 4.1, 7.1-7.5, 16.4
        """
        from src.chunking.domain.events import (
            ChunkCompletedEvent,
            ChunkCreatedEvent,
            ChunkEmbeddedEvent,
            ChunkFailedEvent,
            ChunkSummarizedEvent,
        )
        from src.rss.article.domain.events import ArticleQualityCalculated

        handlers_registered = []

        # Process Manager - ArticleAIProcessingPipeline
        # NOTA: El Process Manager reemplazó al OnArticleQualityCalculatedHandler
        pipeline = self.get_article_ai_processing_pipeline()

        # Registrar Process Manager para ArticleQualityCalculated (iniciar pipeline)
        self._shared.event_handler_registry.register_handler(
            ArticleQualityCalculated,
            pipeline,
        )
        handlers_registered.append(
            "ArticleAIProcessingPipeline (ArticleQualityCalculated)"
        )

        # Registrar Process Manager para eventos de aggregate (trackear progreso)
        self._shared.event_handler_registry.register_handler(
            ChunkCreatedEvent,
            pipeline,
        )
        handlers_registered.append("ArticleAIProcessingPipeline (ChunkCreatedEvent)")

        self._shared.event_handler_registry.register_handler(
            ChunkEmbeddedEvent,
            pipeline,
        )
        handlers_registered.append("ArticleAIProcessingPipeline (ChunkEmbeddedEvent)")

        self._shared.event_handler_registry.register_handler(
            ChunkSummarizedEvent,
            pipeline,
        )
        handlers_registered.append("ArticleAIProcessingPipeline (ChunkSummarizedEvent)")

        self._shared.event_handler_registry.register_handler(
            ChunkCompletedEvent,
            pipeline,
        )
        handlers_registered.append("ArticleAIProcessingPipeline (ChunkCompletedEvent)")

        self._shared.event_handler_registry.register_handler(
            ChunkFailedEvent,
            pipeline,
        )
        handlers_registered.append("ArticleAIProcessingPipeline (ChunkFailedEvent)")

        self._shared.logger.info(
            "Event handlers registrados en Event Bus",
            handlers=handlers_registered,
            count=len(handlers_registered),
        )
