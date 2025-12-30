"""Integration tests para ChunkingContainer.

Tests de integración que verifican:
- Resolución de servicios
- Registro de handlers
- Configuración correcta

Requirements: 10.1.5
"""

import pytest

from src.chunking.app.commands.process_article_for_ai.command import (
    ProcessArticleForAICommand,
)
from src.chunking.container import ChunkingContainer
from src.chunking.domain.services.chunking import ChunkingService
from src.chunking.infra.persistence.repositories.content_chunk_read_repository import (
    SqlAlchemyContentChunkReadRepository,
)
from src.chunking.infra.persistence.repositories.content_chunk_write_repository import (
    SqlAlchemyContentChunkWriteRepository,
)
from src.rss.article.domain.events import ArticleQualityCalculated
from src.shared.config import AppConfig
from src.shared.container import SharedContainer


class TestChunkingContainer:
    """Tests de integración para ChunkingContainer."""

    # === INITIALIZATION ===

    def test_container_initialization(self, chunking_container):
        """Debería inicializar container sin errores."""
        # Assert
        assert chunking_container is not None
        assert isinstance(chunking_container, ChunkingContainer)

    # === SERVICE RESOLUTION ===

    def test_get_chunking_service(self, chunking_container):
        """Debería resolver ChunkingService correctamente."""
        # Act
        service = chunking_container.get_chunking_service()

        # Assert
        assert service is not None
        assert isinstance(service, ChunkingService)
        assert service.chunk_size == 1400  # Default
        assert service.chunk_overlap == 150  # Default

    def test_get_chunking_service_is_singleton(self, chunking_container):
        """Debería retornar la misma instancia (singleton)."""
        # Act
        service1 = chunking_container.get_chunking_service()
        service2 = chunking_container.get_chunking_service()

        # Assert
        assert service1 is service2

    def test_get_token_encoder(self, chunking_container):
        """Debería resolver ITokenEncoder correctamente."""
        # Act
        encoder = chunking_container.get_token_encoder()

        # Assert
        assert encoder is not None
        assert hasattr(encoder, "count_tokens")

    def test_get_text_splitter(self, chunking_container):
        """Debería resolver ITextSplitter correctamente."""
        # Act
        splitter = chunking_container.get_text_splitter()

        # Assert
        assert splitter is not None
        assert hasattr(splitter, "find_split_point")

    def test_get_content_chunk_read_repository(self, chunking_container):
        """Debería crear ContentChunkReadRepository correctamente."""
        # Act
        repository = chunking_container.get_content_chunk_read_repository()

        # Assert
        assert repository is not None
        assert isinstance(repository, SqlAlchemyContentChunkReadRepository)

    def test_get_content_chunk_write_repository(self, chunking_container):
        """Debería crear ContentChunkWriteRepository correctamente."""
        # Act
        repository = chunking_container.get_content_chunk_write_repository()

        # Assert
        assert repository is not None
        assert isinstance(repository, SqlAlchemyContentChunkWriteRepository)

    def test_get_process_article_for_ai_handler(self, chunking_container):
        """Debería resolver ProcessArticleForAIHandler correctamente."""
        # Act
        handler = chunking_container.get_process_article_for_ai_handler()

        # Assert
        assert handler is not None
        assert hasattr(handler, "handle")

    def test_get_on_article_quality_calculated_handler(self, chunking_container):
        """Debería resolver OnArticleQualityCalculatedHandler correctamente."""
        # Act
        handler = chunking_container.get_on_article_quality_calculated_handler()

        # Assert
        assert handler is not None
        assert hasattr(handler, "handle")

    # === HANDLER REGISTRATION ===

    def test_register_handlers(self, chunking_container, shared_container):
        """Debería registrar handlers sin errores."""
        # Act
        chunking_container.register_handlers()

        # Assert - No exceptions
        assert True

    def test_command_handler_registration(self, chunking_container, shared_container):
        """Debería registrar command handlers en Mediator."""
        # Act
        chunking_container.register_handlers()

        # Assert
        assert ProcessArticleForAICommand in shared_container.mediator._handler_registry

        handler = shared_container.mediator._handler_registry[
            ProcessArticleForAICommand
        ]
        assert handler is not None

    def test_event_handler_registration(self, chunking_container, shared_container):
        """Debería registrar event handlers en Event Bus."""
        # Act
        chunking_container.register_handlers()

        # Assert
        registry = shared_container.event_handler_registry
        handlers = registry.get_handlers(ArticleQualityCalculated)

        assert len(handlers) > 0
        assert any(
            handler.__class__.__name__ == "OnArticleQualityCalculatedHandler"
            for handler in handlers
        )

    # === CONFIGURATION ===

    def test_chunking_service_configuration_from_env(
        self, chunking_container, monkeypatch
    ):
        """Debería usar configuración de variables de entorno."""
        # Arrange
        monkeypatch.setenv("CHUNK_SIZE", "1200")
        monkeypatch.setenv("CHUNK_OVERLAP", "100")

        # Resetear servicio para forzar recreación
        chunking_container._chunking_service = None

        # Act
        service = chunking_container.get_chunking_service()

        # Assert
        assert service.chunk_size == 1200
        assert service.chunk_overlap == 100

    def test_chunking_service_validates_configuration(
        self, chunking_container, monkeypatch
    ):
        """Debería validar configuración inválida."""
        # Arrange
        monkeypatch.setenv("CHUNK_SIZE", "50")  # Muy pequeño

        # Resetear servicio
        chunking_container._chunking_service = None

        # Act & Assert
        with pytest.raises(ValueError, match="CHUNK_SIZE debe ser >= 100"):
            chunking_container.get_chunking_service()

    # === INTEGRATION ===

    def test_full_container_initialization(self, shared_container):
        """Debería inicializar container completo sin errores."""
        # Act
        container = ChunkingContainer(shared_container)
        container.register_handlers()

        # Assert - No exceptions
        assert container is not None


class TestChunkingContainerIntegration:
    """Tests de integración más complejos."""

    def test_chunking_service_can_chunk_text(self, chunking_container):
        """Debería poder usar ChunkingService para dividir texto."""
        # Arrange
        service = chunking_container.get_chunking_service()
        text = "Este es un texto de prueba. " * 100  # Texto largo

        # Act
        chunks = service.chunk_text(
            text=text,
            article_id="test-123",
            source_url="https://example.com",
        )

        # Assert
        assert len(chunks) > 0
        assert all(chunk.article_id == "test-123" for chunk in chunks)
        assert all(chunk.token_count.value > 0 for chunk in chunks)
