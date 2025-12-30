"""Integration tests para ClusteringContainer.

Valida que el container registre correctamente todos los handlers
y que las dependencias se resuelvan apropiadamente.

Requirements: 10.3.6
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.chunking.domain.events import ArticleEmbeddingGenerated
from src.clustering.app.commands.cluster_articles.command import ClusterArticlesCommand
from src.clustering.app.queries.get_article_clusters.query import (
    GetArticleClustersQuery,
)
from src.clustering.container import ClusteringContainer


class TestClusteringContainer:
    """Tests de integración para ClusteringContainer."""

    @pytest.fixture
    def mock_shared_container(self):
        """Mock para SharedContainer."""
        shared = Mock()
        shared.logger = Mock()
        shared.logger.bind = Mock(return_value=shared.logger)
        shared.logger.info = Mock()
        shared.mediator = AsyncMock()
        shared.event_handler_registry = Mock()
        shared.event_publisher = AsyncMock()
        shared.session_factory = Mock()
        shared.register_handler = Mock()

        return shared

    @pytest.fixture
    def container(self, mock_shared_container):
        """Container con dependencias mockeadas."""
        return ClusteringContainer(shared=mock_shared_container)

    # === SERVICE RESOLUTION ===

    def test_get_clustering_service_returns_service(self, container):
        """Debería resolver ClusteringService correctamente."""
        # Act
        service = container.get_clustering_service()

        # Assert
        assert service is not None
        from src.clustering.domain.services.clustering import ClusteringService

        assert isinstance(service, ClusteringService)

    def test_get_clustering_service_is_singleton(self, container):
        """Debería retornar la misma instancia (singleton)."""
        # Act
        service1 = container.get_clustering_service()
        service2 = container.get_clustering_service()

        # Assert
        assert service1 is service2

    def test_get_semantic_cluster_factory_returns_factory(self, container):
        """Debería resolver SemanticClusterFactory correctamente."""
        # Act
        factory = container.get_semantic_cluster_factory()

        # Assert
        assert factory is not None
        from src.clustering.domain.factories.semantic_cluster_factory import (
            SemanticClusterFactory,
        )

        assert isinstance(factory, SemanticClusterFactory)

    # === REPOSITORY RESOLUTION ===

    def test_get_semantic_cluster_read_repository_returns_repository(
        self,
        container,
        mock_shared_container,
    ):
        """Debería resolver SemanticClusterReadRepository correctamente."""
        # Arrange
        mock_session = Mock()
        mock_shared_container.session_factory.return_value = mock_session

        # Act
        repository = container.get_semantic_cluster_read_repository()

        # Assert
        assert repository is not None
        from src.clustering.infra.persistence.repositories.semantic_cluster_read_repository import (
            SqlAlchemySemanticClusterReadRepository,
        )

        assert isinstance(repository, SqlAlchemySemanticClusterReadRepository)

    def test_get_semantic_cluster_write_repository_returns_repository(
        self,
        container,
        mock_shared_container,
    ):
        """Debería resolver SemanticClusterWriteRepository correctamente."""
        # Arrange
        mock_session = Mock()
        mock_shared_container.session_factory.return_value = mock_session

        # Act
        repository = container.get_semantic_cluster_write_repository()

        # Assert
        assert repository is not None
        from src.clustering.infra.persistence.repositories.semantic_cluster_write_repository import (
            SqlAlchemySemanticClusterWriteRepository,
        )

        assert isinstance(repository, SqlAlchemySemanticClusterWriteRepository)

    # === COMMAND HANDLER RESOLUTION ===

    def test_get_cluster_articles_handler_returns_handler(self, container):
        """Debería resolver ClusterArticlesHandler correctamente."""
        # Act
        handler = container.get_cluster_articles_handler()

        # Assert
        assert handler is not None
        from src.clustering.app.commands.cluster_articles.handler import (
            ClusterArticlesHandler,
        )

        assert isinstance(handler, ClusterArticlesHandler)

    # === QUERY HANDLER RESOLUTION ===

    def test_get_get_article_clusters_handler_returns_handler(
        self,
        container,
        mock_shared_container,
    ):
        """Debería resolver GetArticleClustersHandler correctamente."""
        # Arrange
        mock_session = Mock()
        mock_shared_container.session_factory.return_value = mock_session

        # Act
        handler = container.get_get_article_clusters_handler()

        # Assert
        assert handler is not None
        from src.clustering.app.queries.get_article_clusters.handler import (
            GetArticleClustersHandler,
        )

        assert isinstance(handler, GetArticleClustersHandler)

    # === EVENT HANDLER RESOLUTION ===

    def test_get_on_article_embedding_generated_handler_returns_handler(
        self,
        container,
    ):
        """Debería resolver OnArticleEmbeddingGeneratedHandler correctamente."""
        # Act
        handler = container.get_on_article_embedding_generated_handler()

        # Assert
        assert handler is not None
        from src.clustering.app.event_handlers import (
            OnArticleEmbeddingGeneratedHandler,
        )

        assert isinstance(handler, OnArticleEmbeddingGeneratedHandler)

    # === HANDLER REGISTRATION ===

    def test_register_handlers_registers_all_handlers(
        self,
        container,
        mock_shared_container,
    ):
        """Debería registrar todos los handlers correctamente."""
        # Arrange
        mock_session = Mock()
        mock_shared_container.session_factory.return_value = mock_session

        # Act
        container.register_handlers()

        # Assert - Verificar que se llamó register_handler
        assert mock_shared_container.register_handler.call_count >= 2

        # Verificar que se registró el command handler
        command_calls = [
            call
            for call in mock_shared_container.register_handler.call_args_list
            if call[0][0] == ClusterArticlesCommand
        ]
        assert len(command_calls) == 1

        # Verificar que se registró el query handler
        query_calls = [
            call
            for call in mock_shared_container.register_handler.call_args_list
            if call[0][0] == GetArticleClustersQuery
        ]
        assert len(query_calls) == 1

    def test_register_handlers_registers_event_handlers(
        self,
        container,
        mock_shared_container,
    ):
        """Debería registrar event handlers en el event bus."""
        # Act
        container.register_handlers()

        # Assert - Verificar que se registró el event handler
        assert (
            mock_shared_container.event_handler_registry.register_handler.call_count
            >= 1
        )

        # Verificar que se registró OnArticleEmbeddingGeneratedHandler
        event_calls = [
            call
            for call in mock_shared_container.event_handler_registry.register_handler.call_args_list
            if call[0][0] == ArticleEmbeddingGenerated
        ]
        assert len(event_calls) == 1

    def test_register_handlers_logs_registration(
        self,
        container,
        mock_shared_container,
    ):
        """Debería loggear el registro de handlers."""
        # Arrange
        mock_session = Mock()
        mock_shared_container.session_factory.return_value = mock_session

        # Act
        container.register_handlers()

        # Assert - Verificar que se loggeó
        assert mock_shared_container.logger.info.call_count >= 3

        # Verificar mensajes de logging
        log_messages = [
            call[0][0] for call in mock_shared_container.logger.info.call_args_list
        ]

        assert any("Command handlers registrados" in msg for msg in log_messages)
        assert any("Query handlers registrados" in msg for msg in log_messages)
        assert any("Event handlers registrados" in msg for msg in log_messages)

    # === CONFIGURATION ===

    def test_clustering_service_uses_config_from_env(self, container, monkeypatch):
        """Debería cargar configuración desde variables de entorno."""
        # Arrange
        monkeypatch.setenv("CLUSTERING_ALGORITHM", "dbscan")
        monkeypatch.setenv("CLUSTERING_N_CLUSTERS", "15")
        monkeypatch.setenv("CLUSTERING_DBSCAN_EPS", "0.4")

        # Act
        service = container.get_clustering_service()

        # Assert
        assert service._algorithm == "dbscan"
        assert service._n_clusters == 15
        assert service._dbscan_eps == 0.4

    def test_clustering_service_uses_defaults_when_no_env(self, container, monkeypatch):
        """Debería usar valores por defecto cuando no hay variables de entorno."""
        # Arrange - Limpiar variables de entorno
        monkeypatch.delenv("CLUSTERING_ALGORITHM", raising=False)
        monkeypatch.delenv("CLUSTERING_N_CLUSTERS", raising=False)

        # Act
        service = container.get_clustering_service()

        # Assert - Verificar defaults
        assert service._algorithm == "kmeans"
        assert service._n_clusters == 10

    # === ERROR HANDLING ===

    def test_clustering_service_validates_config(self, container, monkeypatch):
        """Debería validar configuración inválida."""
        # Arrange - Configuración inválida
        monkeypatch.setenv("CLUSTERING_ALGORITHM", "invalid")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            container.get_clustering_service()

        assert "debe ser 'kmeans' o 'dbscan'" in str(exc_info.value)

    def test_clustering_service_validates_n_clusters(self, container, monkeypatch):
        """Debería validar n_clusters inválido."""
        # Arrange
        monkeypatch.setenv("CLUSTERING_N_CLUSTERS", "0")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            container.get_clustering_service()

        assert "debe ser >= 1" in str(exc_info.value)


@pytest.mark.integration
class TestClusteringContainerIntegration:
    """Tests de integración con dependencias reales (sin DB)."""

    @pytest.fixture
    def real_shared_container(self):
        """SharedContainer con dependencias reales (sin DB)."""
        from src.shared.config.app_config import AppConfig
        from src.shared.container import SharedContainer

        # Crear config mínimo (usa defaults de .env)
        config = AppConfig()

        return SharedContainer(config)

    @pytest.fixture
    def container(self, real_shared_container):
        """Container con SharedContainer real."""
        return ClusteringContainer(shared=real_shared_container)

    def test_full_handler_registration_flow(self, container):
        """Debería registrar todos los handlers sin errores."""
        # Act - No debería lanzar excepciones
        container.register_handlers()

        # Assert - Verificar que los handlers están registrados
        from src.clustering.app.commands.cluster_articles.command import (
            ClusterArticlesCommand,
        )
        from src.clustering.app.queries.get_article_clusters.query import (
            GetArticleClustersQuery,
        )

        # Verificar command handler
        assert ClusterArticlesCommand in container._shared.mediator._handler_registry

        # Verificar query handler
        assert GetArticleClustersQuery in container._shared.mediator._handler_registry

    def test_clustering_service_can_be_instantiated(self, container):
        """Debería poder instanciar ClusteringService con config real."""
        # Act
        service = container.get_clustering_service()

        # Assert
        assert service is not None
        assert service._algorithm in ["kmeans", "dbscan"]
        assert service._n_clusters > 0
