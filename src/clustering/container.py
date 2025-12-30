"""Clustering Bounded Context Container.

Container de inversión de dependencias para el bounded context Clustering.
Sigue Clean Architecture + DDD + CQRS.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.container import SharedContainer


class ClusteringContainer:
    """
    Container del bounded context Clustering.

    Responsabilidades:
    - Event Handlers: OnArticleEmbeddingGeneratedHandler
    - Commands: ClusterArticlesCommand
    - Queries: GetArticleClustersQuery
    - Services: ClusteringService
    - Repositories: SemanticClusterReadRepository, SemanticClusterWriteRepository
    - Factories: SemanticClusterFactory

    Requirements: 10.3
    """

    def __init__(self, shared: "SharedContainer"):
        self._shared = shared

        # Event Handlers (Lazy)
        self._on_article_embedding_generated_handler = None

        # Command Handlers (Lazy)
        self._cluster_articles_handler = None

        # Query Handlers (Lazy)
        self._get_article_clusters_handler = None

        # Domain Services (Lazy)
        self._clustering_service = None

        # Repositories (Lazy)
        self._semantic_cluster_read_repository = None
        self._semantic_cluster_write_repository = None

        # Factories (Lazy)
        self._semantic_cluster_factory = None

    # === DOMAIN SERVICES ===

    def get_clustering_service(self):
        """
        Factory para ClusteringService.

        Requirements: 10.3.1
        """
        if self._clustering_service is None:
            from src.clustering.domain.services.clustering import ClusteringService
            from src.shared.config.clustering_config import ClusteringConfig

            # Obtener configuración de clustering desde environment
            clustering_config = ClusteringConfig.from_env()

            self._clustering_service = ClusteringService(
                algorithm=clustering_config.algorithm,
                n_clusters=clustering_config.n_clusters,
                dbscan_eps=clustering_config.dbscan_eps,
                dbscan_min_samples=clustering_config.dbscan_min_samples,
                random_state=clustering_config.random_state,
            )

        return self._clustering_service

    # === FACTORIES ===

    def get_semantic_cluster_factory(self):
        """
        Factory para SemanticClusterFactory.

        Requirements: 10.3.1
        """
        if self._semantic_cluster_factory is None:
            from src.clustering.domain.factories.semantic_cluster_factory import (
                SemanticClusterFactory,
            )

            self._semantic_cluster_factory = SemanticClusterFactory()

        return self._semantic_cluster_factory

    # === REPOSITORIES ===

    def get_semantic_cluster_read_repository(self):
        """
        Factory para SemanticClusterReadRepository.

        Requirements: 10.3.1
        """
        if self._semantic_cluster_read_repository is None:
            from src.clustering.infra.persistence.repositories.semantic_cluster_read_repository import (
                SqlAlchemySemanticClusterReadRepository,
            )

            # Crear nueva sesión para cada request
            session = self._shared.session_factory()

            self._semantic_cluster_read_repository = (
                SqlAlchemySemanticClusterReadRepository(session=session)
            )

        return self._semantic_cluster_read_repository

    def get_semantic_cluster_write_repository(self):
        """
        Factory para SemanticClusterWriteRepository.

        Requirements: 10.3.1
        """
        if self._semantic_cluster_write_repository is None:
            from src.clustering.infra.persistence.repositories.semantic_cluster_write_repository import (
                SqlAlchemySemanticClusterWriteRepository,
            )

            # Crear nueva sesión para cada request
            session = self._shared.session_factory()

            self._semantic_cluster_write_repository = (
                SqlAlchemySemanticClusterWriteRepository(session=session)
            )

        return self._semantic_cluster_write_repository

    # === COMMAND HANDLERS ===

    def get_cluster_articles_handler(self):
        """
        Factory para ClusterArticlesHandler.

        Requirements: 10.3.2
        """
        if self._cluster_articles_handler is None:
            from src.clustering.app.commands.cluster_articles.handler import (
                ClusterArticlesHandler,
            )

            # TODO: Necesitamos IVectorStore para recuperar embeddings
            # Por ahora, pasamos None y el handler retornará error
            # indicando que falta implementación

            self._cluster_articles_handler = ClusterArticlesHandler(
                vector_store=None,  # TODO: Implementar cuando tengamos vector store
                logger=self._shared.logger,
            )

        return self._cluster_articles_handler

    # === QUERY HANDLERS ===

    def get_get_article_clusters_handler(self):
        """
        Factory para GetArticleClustersHandler.

        Requirements: 10.3.3
        """
        if self._get_article_clusters_handler is None:
            from src.clustering.app.queries.get_article_clusters.handler import (
                GetArticleClustersHandler,
            )

            self._get_article_clusters_handler = GetArticleClustersHandler(
                cluster_repository=self.get_semantic_cluster_read_repository(),
                logger=self._shared.logger,
            )

        return self._get_article_clusters_handler

    # === EVENT HANDLERS ===

    def get_on_article_embedding_generated_handler(self):
        """
        Factory para OnArticleAIProcessedHandler.

        Requirements: 10.3.4
        """
        if self._on_article_embedding_generated_handler is None:
            from src.clustering.app.event_handlers import (
                OnArticleAIProcessedHandler,
            )

            self._on_article_embedding_generated_handler = OnArticleAIProcessedHandler(
                command_bus=self._shared.mediator,
                logger=self._shared.logger,
            )

        return self._on_article_embedding_generated_handler

    # === HANDLER REGISTRATION ===

    def register_handlers(self) -> None:
        """
        Registra todos los handlers del bounded context Clustering.

        Event-Driven Architecture:
        - ArticleEmbeddingGenerated → ClusterArticlesCommand

        Incluye:
        - Command handlers en Mediator
        - Query handlers en Mediator
        - Event handlers en EventHandlerRegistry

        Requirements: 10.3.2, 10.3.3, 10.3.4
        """
        self._register_command_handlers()
        self._register_query_handlers()
        self._register_event_handlers()

        self._shared.logger.info(
            "ClusteringContainer: handlers registrados (event-driven architecture)",
        )

    def _register_command_handlers(self) -> None:
        """
        Registra command handlers en Mediator.

        Command Handlers:
        - ClusterArticlesHandler: Agrupa artículos en clusters semánticos

        Requirements: 10.3.2
        """
        from src.clustering.app.commands.cluster_articles.command import (
            ClusterArticlesCommand,
        )

        handlers_registered = []

        # ClusterArticlesHandler
        self._shared.register_handler(
            ClusterArticlesCommand,
            self.get_cluster_articles_handler(),
        )
        handlers_registered.append("ClusterArticlesHandler")

        self._shared.logger.info(
            "Command handlers registrados en Mediator",
            handlers=handlers_registered,
            count=len(handlers_registered),
        )

    def _register_query_handlers(self) -> None:
        """
        Registra query handlers en Mediator.

        Query Handlers:
        - GetArticleClustersHandler: Obtiene clusters de artículos

        Requirements: 10.3.3
        """
        from src.clustering.app.queries.get_article_clusters.query import (
            GetArticleClustersQuery,
        )

        handlers_registered = []

        # GetArticleClustersHandler
        self._shared.register_handler(
            GetArticleClustersQuery,
            self.get_get_article_clusters_handler(),
        )
        handlers_registered.append("GetArticleClustersHandler")

        self._shared.logger.info(
            "Query handlers registrados en Mediator",
            handlers=handlers_registered,
            count=len(handlers_registered),
        )

    def _register_event_handlers(self) -> None:
        """
        Registra event handlers en Event Bus.

        Event Handlers:
        - OnArticleAIProcessedHandler: Escucha ArticleAIProcessedEvent del Chunking BC

        Requirements: 10.3.4
        """
        from src.chunking.domain.events import ArticleAIProcessedEvent

        handlers_registered = []

        # OnArticleAIProcessedHandler (antes OnArticleEmbeddingGeneratedHandler)
        self._shared.event_handler_registry.register_handler(
            ArticleAIProcessedEvent,
            self.get_on_article_embedding_generated_handler(),
        )
        handlers_registered.append("OnArticleAIProcessedHandler")

        self._shared.logger.info(
            "Event handlers registrados en Event Bus",
            handlers=handlers_registered,
            count=len(handlers_registered),
        )
