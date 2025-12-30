"""Integration tests for EmbeddingContainer.

Tests de integración para verificar que el container de Embedding
resuelve correctamente todas las dependencias y registra handlers.

Requirements: 10.2.6
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.embedding.container import EmbeddingContainer
from src.shared.container import SharedContainer


class TestEmbeddingContainer:
    """Tests de integración para EmbeddingContainer."""

    @pytest.fixture
    def mock_shared_container(self):
        """Mock del SharedContainer."""
        shared = Mock(spec=SharedContainer)
        shared.logger = Mock()
        shared.logger.info = Mock()
        shared.logger.bind = Mock(return_value=shared.logger)
        shared.mediator = Mock()
        shared.event_publisher = Mock()
        shared.event_handler_registry = Mock()
        shared.session_factory = Mock()
        shared.register_handler = Mock()

        return shared

    @pytest.fixture
    def container(self, mock_shared_container):
        """Container de Embedding con dependencias mockeadas."""
        return EmbeddingContainer(shared=mock_shared_container)

    # === SERVICE RESOLUTION TESTS ===

    def test_get_embedding_service_resolves_correctly(self, container):
        """Debería resolver EmbeddingService correctamente."""
        # Act
        service = container.get_embedding_service()

        # Assert
        assert service is not None
        from src.embedding.domain.services.embedding import EmbeddingService

        assert isinstance(service, EmbeddingService)

    def test_get_nomic_embed_adapter_resolves_correctly(self, container, monkeypatch):
        """Debería resolver NomicEmbedAdapter correctamente."""
        # Arrange - Mock environment variables
        monkeypatch.setenv("NOMIC_API_KEY", "test-api-key")
        monkeypatch.setenv("EMBEDDING_MODEL", "nomic-embed-text-v1.5")

        # Act
        adapter = container.get_nomic_embed_adapter()

        # Assert
        assert adapter is not None
        from src.embedding.infra.external.nomic_embed_adapter import NomicEmbedAdapter

        assert isinstance(adapter, NomicEmbedAdapter)

    def test_get_article_embedding_factory_resolves_correctly(self, container):
        """Debería resolver ArticleEmbeddingFactory correctamente."""
        # Act
        factory = container.get_article_embedding_factory()

        # Assert
        assert factory is not None
        from src.embedding.domain.factories.article_embedding_factory import (
            ArticleEmbeddingFactory,
        )

        assert isinstance(factory, ArticleEmbeddingFactory)

    # === REPOSITORY RESOLUTION TESTS ===

    def test_get_article_embedding_read_repository_resolves_correctly(self, container):
        """Debería resolver ArticleEmbeddingReadRepository correctamente."""
        # Act
        repository = container.get_article_embedding_read_repository()

        # Assert
        assert repository is not None
        from src.embedding.infra.persistence.repositories.article_embedding_read_repository import (
            SqlAlchemyArticleEmbeddingReadRepository,
        )

        assert isinstance(repository, SqlAlchemyArticleEmbeddingReadRepository)

    def test_get_article_embedding_write_repository_resolves_correctly(self, container):
        """Debería resolver ArticleEmbeddingWriteRepository correctamente."""
        # Act
        repository = container.get_article_embedding_write_repository()

        # Assert
        assert repository is not None
        from src.embedding.infra.persistence.repositories.article_embedding_write_repository import (
            SqlAlchemyArticleEmbeddingWriteRepository,
        )

        assert isinstance(repository, SqlAlchemyArticleEmbeddingWriteRepository)

    # === HANDLER RESOLUTION TESTS ===

    def test_get_generate_article_embedding_handler_resolves_correctly(self, container):
        """Debería resolver GenerateArticleEmbeddingHandler correctamente."""
        # Act
        handler = container.get_generate_article_embedding_handler()

        # Assert
        assert handler is not None
        from src.embedding.app.commands.generate_article_embedding.handler import (
            GenerateArticleEmbeddingHandler,
        )

        assert isinstance(handler, GenerateArticleEmbeddingHandler)

    def test_get_search_similar_chunks_handler_resolves_correctly(self, container):
        """Debería resolver SearchSimilarChunksHandler correctamente."""
        # Act
        handler = container.get_search_similar_chunks_handler()

        # Assert
        assert handler is not None
        from src.embedding.app.queries.search_similar_chunks.handler import (
            SearchSimilarChunksHandler,
        )

        assert isinstance(handler, SearchSimilarChunksHandler)

    def test_get_on_article_chunked_handler_resolves_correctly(self, container):
        """Debería resolver OnArticleChunkedHandler correctamente."""
        # Act
        handler = container.get_on_article_chunked_handler()

        # Assert
        assert handler is not None
        from src.embedding.app.event_handlers import OnArticleChunkedHandler

        assert isinstance(handler, OnArticleChunkedHandler)

    # === HANDLER REGISTRATION TESTS ===

    def test_register_handlers_registers_command_handlers(
        self,
        container,
        mock_shared_container,
    ):
        """Debería registrar command handlers en Mediator."""
        # Act
        container.register_handlers()

        # Assert
        from src.embedding.app.commands.generate_article_embedding.command import (
            GenerateArticleEmbeddingCommand,
        )

        # Verificar que se llamó register_handler
        assert mock_shared_container.register_handler.called

        # Verificar que se registró GenerateArticleEmbeddingCommand
        calls = mock_shared_container.register_handler.call_args_list
        command_types = [call[0][0] for call in calls]
        assert GenerateArticleEmbeddingCommand in command_types

    def test_register_handlers_registers_query_handlers(
        self,
        container,
        mock_shared_container,
    ):
        """Debería registrar query handlers en Mediator."""
        # Act
        container.register_handlers()

        # Assert
        from src.embedding.app.queries.search_similar_chunks.query import (
            SearchSimilarChunksQuery,
        )

        # Verificar que se registró SearchSimilarChunksQuery
        calls = mock_shared_container.register_handler.call_args_list
        query_types = [call[0][0] for call in calls]
        assert SearchSimilarChunksQuery in query_types

    def test_register_handlers_registers_event_handlers(
        self,
        container,
        mock_shared_container,
    ):
        """Debería registrar event handlers en Event Bus."""
        # Act
        container.register_handlers()

        # Assert
        from src.chunking.domain.events import ArticleChunked

        # Verificar que se llamó register_handler en event_handler_registry
        assert mock_shared_container.event_handler_registry.register_handler.called

        # Verificar que se registró ArticleChunked
        calls = (
            mock_shared_container.event_handler_registry.register_handler.call_args_list
        )
        event_types = [call[0][0] for call in calls]
        assert ArticleChunked in event_types

    def test_register_handlers_logs_registration(
        self,
        container,
        mock_shared_container,
    ):
        """Debería loggear el registro de handlers."""
        # Act
        container.register_handlers()

        # Assert
        assert mock_shared_container.logger.info.called

        # Verificar que se loggeó el mensaje principal
        calls = [
            call[0][0] for call in mock_shared_container.logger.info.call_args_list
        ]
        assert any("EmbeddingContainer: handlers registrados" in call for call in calls)

    # === CONFIGURATION TESTS ===

    def test_embedding_config_loads_from_env(self, monkeypatch):
        """Debería cargar configuración desde environment variables."""
        # Arrange
        monkeypatch.setenv("NOMIC_API_KEY", "test-key-123")
        monkeypatch.setenv("EMBEDDING_MODEL", "nomic-embed-text-v1.5")
        monkeypatch.setenv("EMBEDDING_DIMENSION", "768")
        monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "32")

        # Act
        from src.shared.config.embedding_config import EmbeddingConfig

        config = EmbeddingConfig.from_env()

        # Assert
        assert config.nomic_api_key == "test-key-123"
        assert config.embedding_model == "nomic-embed-text-v1.5"
        assert config.embedding_dimension == 768
        assert config.batch_size == 32

    def test_embedding_config_raises_without_api_key(self, monkeypatch):
        """Debería lanzar error si NOMIC_API_KEY no está configurado."""
        # Arrange
        monkeypatch.delenv("NOMIC_API_KEY", raising=False)

        # Act & Assert
        from src.shared.config.embedding_config import EmbeddingConfig

        with pytest.raises(ValueError) as exc_info:
            EmbeddingConfig.from_env()

        assert "NOMIC_API_KEY" in str(exc_info.value)

    def test_embedding_config_validates_correctly(self):
        """Debería validar configuración correctamente."""
        # Arrange
        from src.shared.config.embedding_config import EmbeddingConfig

        config = EmbeddingConfig(
            nomic_api_key="test-key",
            embedding_model="nomic-embed-text-v1.5",
            embedding_dimension=768,
            batch_size=32,
        )

        # Act & Assert - No debería lanzar excepción
        config.validate()

    def test_embedding_config_validation_fails_with_invalid_dimension(self):
        """Debería fallar validación con dimensión inválida."""
        # Arrange
        from src.shared.config.embedding_config import EmbeddingConfig

        config = EmbeddingConfig(
            nomic_api_key="test-key",
            embedding_model="nomic-embed-text-v1.5",
            embedding_dimension=0,  # Inválido
            batch_size=32,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            config.validate()

        assert "embedding_dimension must be positive" in str(exc_info.value)

    # === LAZY LOADING TESTS ===

    def test_services_are_lazy_loaded(self, container):
        """Debería cargar servicios de forma lazy."""
        # Assert - Servicios no están inicializados
        assert container._embedding_service is None
        assert container._nomic_embed_adapter is None

        # Act - Acceder al servicio
        service = container.get_embedding_service()

        # Assert - Servicio ahora está inicializado
        assert container._embedding_service is not None
        assert service is container._embedding_service

    def test_repositories_are_lazy_loaded(self, container):
        """Debería cargar repositorios de forma lazy."""
        # Assert - Repositorios no están inicializados
        assert container._article_embedding_read_repository is None
        assert container._article_embedding_write_repository is None

        # Act - Acceder a repositorios
        read_repo = container.get_article_embedding_read_repository()
        write_repo = container.get_article_embedding_write_repository()

        # Assert - Repositorios ahora están inicializados
        assert container._article_embedding_read_repository is not None
        assert container._article_embedding_write_repository is not None
        assert read_repo is container._article_embedding_read_repository
        assert write_repo is container._article_embedding_write_repository

    def test_handlers_are_lazy_loaded(self, container):
        """Debería cargar handlers de forma lazy."""
        # Assert - Handlers no están inicializados
        assert container._generate_article_embedding_handler is None
        assert container._search_similar_chunks_handler is None
        assert container._on_article_chunked_handler is None

        # Act - Acceder a handlers
        command_handler = container.get_generate_article_embedding_handler()
        query_handler = container.get_search_similar_chunks_handler()
        event_handler = container.get_on_article_chunked_handler()

        # Assert - Handlers ahora están inicializados
        assert container._generate_article_embedding_handler is not None
        assert container._search_similar_chunks_handler is not None
        assert container._on_article_chunked_handler is not None
        assert command_handler is container._generate_article_embedding_handler
        assert query_handler is container._search_similar_chunks_handler
        assert event_handler is container._on_article_chunked_handler
