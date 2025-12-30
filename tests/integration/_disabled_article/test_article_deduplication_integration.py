"""Tests de integración para deduplicación semántica en Article BC."""

from unittest.mock import AsyncMock, Mock

import pytest

from src.chunking.domain.events import ArticleEmbeddingGenerated
from src.rss.article.app.commands.detect_duplicate_article import (
    DetectDuplicateArticleCommand,
    DetectDuplicateArticleHandler,
)
from src.rss.article.app.event_handlers import OnArticleEmbeddingGeneratedHandler
from src.rss.article.container import RssArticleContainer
from src.rss.article.domain.services import SemanticDeduplicationService
from src.shared.container import SharedContainer


@pytest.fixture
def mock_shared_container():
    """Mock SharedContainer para tests."""
    shared = Mock(spec=SharedContainer)
    shared.logger = Mock()
    shared.logger.bind = Mock(return_value=shared.logger)
    shared.logger.info = Mock()
    shared.logger.warning = Mock()
    shared.logger.error = Mock()
    shared.session_factory = Mock()
    shared.mediator = AsyncMock()
    shared.event_publisher = AsyncMock()
    shared.event_handler_registry = Mock()
    shared.register_handler = Mock()
    return shared


@pytest.fixture
def article_container(mock_shared_container):
    """RssArticleContainer para tests."""
    return RssArticleContainer(shared=mock_shared_container)


class TestSemanticDeduplicationServiceResolution:
    """Tests para resolución de SemanticDeduplicationService."""

    def test_get_semantic_deduplication_service_creates_instance(
        self,
        article_container,
    ):
        """Debería crear instancia de SemanticDeduplicationService."""
        # Act
        service = article_container.get_semantic_deduplication_service()

        # Assert
        assert service is not None
        assert isinstance(service, SemanticDeduplicationService)

    def test_get_semantic_deduplication_service_is_singleton(
        self,
        article_container,
    ):
        """Debería retornar la misma instancia (singleton)."""
        # Act
        service1 = article_container.get_semantic_deduplication_service()
        service2 = article_container.get_semantic_deduplication_service()

        # Assert
        assert service1 is service2

    def test_semantic_deduplication_service_has_correct_threshold(
        self,
        monkeypatch,
    ):
        """Debería usar threshold de configuración."""
        # Arrange - Mock config via environment
        monkeypatch.setenv("DEDUPLICATION_SIMILARITY_THRESHOLD", "0.90")

        from unittest.mock import Mock

        from src.rss.article.container import RssArticleContainer
        from src.shared.config.deduplication_config import DeduplicationConfig

        # Create fresh container with mocked shared
        mock_shared = Mock()
        mock_shared.logger = Mock()
        mock_shared.logger.bind = Mock(return_value=mock_shared.logger)
        mock_shared.session_factory = Mock()

        container = RssArticleContainer(shared=mock_shared)

        # Act
        service = container.get_semantic_deduplication_service()

        # Assert
        assert service._threshold == 0.90


class TestDetectDuplicateArticleHandlerResolution:
    """Tests para resolución de DetectDuplicateArticleHandler."""

    def test_get_detect_duplicate_article_handler_creates_instance(
        self,
        article_container,
    ):
        """Debería crear instancia de DetectDuplicateArticleHandler."""
        # Act
        handler = article_container.get_detect_duplicate_article_handler()

        # Assert
        assert handler is not None
        assert isinstance(handler, DetectDuplicateArticleHandler)

    def test_detect_duplicate_article_handler_is_singleton(
        self,
        article_container,
    ):
        """Debería retornar la misma instancia (singleton)."""
        # Act
        handler1 = article_container.get_detect_duplicate_article_handler()
        handler2 = article_container.get_detect_duplicate_article_handler()

        # Assert
        assert handler1 is handler2

    def test_detect_duplicate_article_handler_has_dependencies(
        self,
        article_container,
    ):
        """Debería tener dependencias inyectadas correctamente."""
        # Act
        handler = article_container.get_detect_duplicate_article_handler()

        # Assert
        assert handler._deduplication_service is not None
        assert handler._logger is not None


class TestHandlerRegistration:
    """Tests para registro de handlers."""

    def test_detect_duplicate_article_handler_registered(
        self,
        article_container,
        mock_shared_container,
    ):
        """Debería registrar DetectDuplicateArticleHandler en Mediator."""
        # Act
        article_container._register_command_handlers()

        # Assert
        # Verificar que register_handler fue llamado con el comando correcto
        calls = mock_shared_container.register_handler.call_args_list
        command_types = [call[0][0] for call in calls]

        assert DetectDuplicateArticleCommand in command_types

    def test_on_article_embedding_generated_handler_registered(
        self,
        article_container,
        mock_shared_container,
    ):
        """Debería registrar OnArticleEmbeddingGeneratedHandler en Event Bus."""
        # Act
        article_container._register_event_handlers()

        # Assert
        # Verificar que register_handler fue llamado con el evento correcto
        calls = (
            mock_shared_container.event_handler_registry.register_handler.call_args_list
        )
        event_types = [call[0][0] for call in calls]

        assert ArticleEmbeddingGenerated in event_types


class TestEventFlow:
    """Tests para flujo de eventos cross-BC."""

    @pytest.mark.asyncio
    async def test_article_embedding_generated_triggers_detect_duplicate(
        self,
        mock_shared_container,
    ):
        """
        Debería emitir DetectDuplicateArticleCommand cuando se genera embedding.

        Flujo:
        ArticleEmbeddingGenerated → OnArticleEmbeddingGeneratedHandler
        → DetectDuplicateArticleCommand
        """
        # Arrange
        handler = OnArticleEmbeddingGeneratedHandler(
            command_bus=mock_shared_container.mediator,
            logger=mock_shared_container.logger,
        )

        event = ArticleEmbeddingGenerated(
            article_id="test-article-123",
            num_chunks=5,
            model="nomic-embed-text",
            dimension=768,
        )

        # Act
        await handler.handle(event)

        # Assert
        mock_shared_container.mediator.send.assert_called_once()
        command = mock_shared_container.mediator.send.call_args[0][0]

        assert isinstance(command, DetectDuplicateArticleCommand)
        assert command.article_id == "test-article-123"


class TestConfiguration:
    """Tests para configuración de deduplicación."""

    def test_deduplication_config_default_values(self):
        """Debería tener valores por defecto correctos."""
        from src.shared.config.deduplication_config import DeduplicationConfig

        # Act
        config = DeduplicationConfig()

        # Assert
        assert config.similarity_threshold == 0.85
        assert config.max_results == 10
        assert config.enabled is True

    def test_deduplication_config_validates_threshold_range(self):
        """Debería validar que threshold esté en rango [0.0, 1.0]."""
        from pydantic import ValidationError

        from src.shared.config.deduplication_config import DeduplicationConfig

        # Act & Assert - Threshold válido
        config = DeduplicationConfig(similarity_threshold=0.5)
        assert config.similarity_threshold == 0.5

        # Act & Assert - Threshold inválido (> 1.0)
        with pytest.raises(ValidationError):
            DeduplicationConfig(similarity_threshold=1.5)

        # Act & Assert - Threshold inválido (< 0.0)
        with pytest.raises(ValidationError):
            DeduplicationConfig(similarity_threshold=-0.1)

    def test_deduplication_config_from_environment(self, monkeypatch):
        """Debería cargar configuración desde variables de entorno."""
        from src.shared.config.deduplication_config import DeduplicationConfig

        # Arrange
        monkeypatch.setenv("DEDUPLICATION_SIMILARITY_THRESHOLD", "0.90")
        monkeypatch.setenv("DEDUPLICATION_MAX_RESULTS", "20")
        monkeypatch.setenv("DEDUPLICATION_ENABLED", "false")

        # Act
        config = DeduplicationConfig()

        # Assert
        assert config.similarity_threshold == 0.90
        assert config.max_results == 20
        assert config.enabled is False
