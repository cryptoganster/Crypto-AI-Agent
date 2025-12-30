"""Tests para ChunkArticleHandler."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from src.chunking.app.commands.chunk_article.command import ChunkArticleCommand
from src.chunking.app.commands.chunk_article.handler import ChunkArticleHandler
from src.chunking.app.commands.chunk_article.result import ChunkArticleResult
from src.chunking.domain.aggregates import ContentChunk
from src.chunking.domain.events import ChunkCreatedEvent
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.token_count import TokenCount
from src.knowledge.domain.value_objects.source_reference import SourceReference


@pytest.mark.asyncio
class TestChunkArticleHandler:
    """Tests para ChunkArticleHandler."""

    @pytest.fixture
    def mock_chunking_service(self):
        """Mock para IChunkingService."""
        return Mock()

    @pytest.fixture
    def mock_chunk_repository(self):
        """Mock para IContentChunkWriteRepository."""
        mock = AsyncMock()
        mock.save = AsyncMock()
        return mock

    @pytest.fixture
    def mock_uow(self):
        """Mock para IUnitOfWork."""
        mock = AsyncMock()
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock(return_value=None)
        mock.commit = AsyncMock()
        return mock

    @pytest.fixture
    def mock_config(self):
        """Mock para AIProcessingConfig."""
        from src.shared.config.ai_processing_config import AIProcessingConfig

        return AIProcessingConfig.for_testing()

    @pytest.fixture
    def mock_logger(self):
        """Mock para ILogger."""
        logger = Mock()
        logger.bind = Mock(return_value=logger)
        logger.info = Mock()
        logger.warning = Mock()
        logger.error = Mock()
        return logger

    @pytest.fixture
    def handler(
        self,
        mock_chunking_service,
        mock_chunk_repository,
        mock_uow,
        mock_config,
        mock_logger,
    ):
        """Handler con dependencias mockeadas."""
        return ChunkArticleHandler(
            chunking_service=mock_chunking_service,
            chunk_repository=mock_chunk_repository,
            uow=mock_uow,
            config=mock_config,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_command(self):
        """Comando de ejemplo."""
        return ChunkArticleCommand(
            article_id="article-123",
            text="Bitcoin alcanzó $50,000 en el mercado. " * 50,  # Texto largo
            source_type="rss_article",
            source_url="https://example.com/article",
            published_at="2024-01-15T10:30:00Z",
            topics=["crypto", "bitcoin"],
            correlation_id="corr-456",
        )

    @pytest.fixture
    def sample_chunks(self):
        """Chunks de ejemplo."""
        source = SourceReference(
            source_id="article-123",
            source_type="rss_article",
            source_url="https://example.com/article",
        )
        return [
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Bitcoin alcanzó $50,000 en el mercado. " * 10,
                position=0,
                start_char=0,
                end_char=500,
                token_count=TokenCount(value=100, encoding="cl100k_base"),
                status=ChunkStatus.PENDING,
            ),
            ContentChunk(
                id=ChunkId.generate(),
                source=source,
                content="Bitcoin alcanzó $50,000 en el mercado. " * 10,
                position=1,
                start_char=450,
                end_char=950,
                token_count=TokenCount(value=100, encoding="cl100k_base"),
                status=ChunkStatus.PENDING,
            ),
        ]

    async def test_handle_successful_chunking_creates_content_chunks(
        self,
        handler,
        sample_command,
        sample_chunks,
        mock_chunking_service,
        mock_chunk_repository,
        mock_uow,
    ):
        """Debería crear ContentChunk aggregates exitosamente."""
        # Arrange
        mock_chunking_service.chunk_text.return_value = sample_chunks

        # Act
        result = await handler.handle(sample_command)

        # Assert
        assert result.success is True
        assert result.article_id == "article-123"
        assert result.chunks_created == 2
        assert result.error_message is None

        # Verificar que se llamó al servicio de chunking
        mock_chunking_service.chunk_text.assert_called_once()
        call_kwargs = mock_chunking_service.chunk_text.call_args.kwargs
        assert call_kwargs["text"] == sample_command.text
        assert call_kwargs["source"].source_id == sample_command.article_id
        assert call_kwargs["source"].source_type == sample_command.source_type
        assert call_kwargs["source"].source_url == sample_command.source_url

    async def test_handle_persists_chunks_in_repository(
        self,
        handler,
        sample_command,
        sample_chunks,
        mock_chunking_service,
        mock_chunk_repository,
        mock_uow,
    ):
        """Debería persistir chunks en repository."""
        # Arrange
        mock_chunking_service.chunk_text.return_value = sample_chunks

        # Act
        result = await handler.handle(sample_command)

        # Assert
        assert result.success is True

        # Verificar que se guardaron todos los chunks
        assert mock_chunk_repository.save.call_count == 2

        # Verificar que se hizo commit
        mock_uow.commit.assert_called_once()

    async def test_handle_content_chunks_emit_chunk_created_event(
        self,
        handler,
        sample_command,
        sample_chunks,
        mock_chunking_service,
    ):
        """Debería verificar que ContentChunk aggregates emiten ChunkCreatedEvent."""
        # Arrange
        mock_chunking_service.chunk_text.return_value = sample_chunks

        # Act
        result = await handler.handle(sample_command)

        # Assert
        assert result.success is True

        # Verificar que cada chunk tiene eventos
        for chunk in sample_chunks:
            events = chunk.get_uncommitted_events()
            assert len(events) > 0

            # Verificar que hay un ChunkCreatedEvent
            created_events = [e for e in events if isinstance(e, ChunkCreatedEvent)]
            assert len(created_events) == 1

            created_event = created_events[0]
            assert created_event.chunk_id == str(chunk.id)
            assert created_event.source_id == chunk.source.source_id
            assert created_event.source_type == chunk.source.source_type
            assert created_event.position == chunk.position
            assert created_event.token_count == int(chunk.token_count)

    async def test_handle_empty_text_returns_error(
        self,
        handler,
        mock_logger,
    ):
        """Debería retornar error cuando texto está vacío."""
        # Arrange
        command = ChunkArticleCommand(
            article_id="article-123",
            text="",
            source_type="rss_article",
            source_url="https://example.com/article",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.article_id == "article-123"
        assert result.chunks_created == 0
        assert "text es requerido" in result.error_message

        # Verificar logging
        mock_logger.warning.assert_called_once()

    async def test_handle_short_text_returns_error(
        self,
        handler,
        mock_logger,
    ):
        """Debería retornar error cuando texto es muy corto."""
        # Arrange
        command = ChunkArticleCommand(
            article_id="article-123",
            text="Texto corto",  # Menos de 100 caracteres
            source_type="rss_article",
            source_url="https://example.com/article",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "al menos 100 caracteres" in result.error_message

    async def test_handle_invalid_url_returns_error(
        self,
        handler,
    ):
        """Debería retornar error cuando URL es inválida."""
        # Arrange
        command = ChunkArticleCommand(
            article_id="article-123",
            text="Bitcoin alcanzó $50,000 en el mercado. " * 50,
            source_type="rss_article",
            source_url="invalid-url",  # URL inválida
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "URL válida" in result.error_message

    async def test_handle_missing_article_id_returns_error(
        self,
        handler,
    ):
        """Debería retornar error cuando article_id falta."""
        # Arrange
        command = ChunkArticleCommand(
            article_id="",  # Vacío
            text="Bitcoin alcanzó $50,000 en el mercado. " * 50,
            source_type="rss_article",
            source_url="https://example.com/article",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "article_id es requerido" in result.error_message

    async def test_handle_uses_configuration_correctly(
        self,
        handler,
        sample_command,
        sample_chunks,
        mock_chunking_service,
        mock_config,
    ):
        """Debería usar configuración correctamente."""
        # Arrange
        mock_chunking_service.chunk_text.return_value = sample_chunks

        # Act
        result = await handler.handle(sample_command)

        # Assert
        assert result.success is True

        # Verificar que el handler tiene acceso a la configuración
        assert handler._config.max_retries == 3
        assert handler._config.chunking_timeout_seconds == 30.0

    async def test_handle_parses_published_at_correctly(
        self,
        handler,
        sample_chunks,
        mock_chunking_service,
    ):
        """Debería parsear published_at correctamente."""
        # Arrange
        command = ChunkArticleCommand(
            article_id="article-123",
            text="Bitcoin alcanzó $50,000 en el mercado. " * 50,
            source_type="rss_article",
            source_url="https://example.com/article",
            published_at="2024-01-15T10:30:00Z",
        )
        mock_chunking_service.chunk_text.return_value = sample_chunks

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se pasó datetime al servicio
        call_kwargs = mock_chunking_service.chunk_text.call_args.kwargs
        assert isinstance(call_kwargs["published_at"], datetime)
        assert call_kwargs["published_at"].year == 2024
        assert call_kwargs["published_at"].month == 1
        assert call_kwargs["published_at"].day == 15

    async def test_handle_continues_with_invalid_published_at(
        self,
        handler,
        sample_chunks,
        mock_chunking_service,
        mock_logger,
    ):
        """Debería continuar cuando published_at es inválido."""
        # Arrange
        command = ChunkArticleCommand(
            article_id="article-123",
            text="Bitcoin alcanzó $50,000 en el mercado. " * 50,
            source_type="rss_article",
            source_url="https://example.com/article",
            published_at="invalid-date",  # Fecha inválida
        )
        mock_chunking_service.chunk_text.return_value = sample_chunks

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se pasó None al servicio
        call_kwargs = mock_chunking_service.chunk_text.call_args.kwargs
        assert call_kwargs["published_at"] is None

        # Verificar logging de warning
        mock_logger.warning.assert_called()

    async def test_handle_exception_returns_failure(
        self,
        handler,
        sample_command,
        mock_chunking_service,
        mock_logger,
    ):
        """Debería retornar failure cuando ocurre excepción."""
        # Arrange
        mock_chunking_service.chunk_text.side_effect = Exception("Service error")

        # Act
        result = await handler.handle(sample_command)

        # Assert
        assert result.success is False
        assert result.article_id == "article-123"
        assert result.chunks_created == 0
        assert "Service error" in result.error_message

        # Verificar logging de error
        mock_logger.error.assert_called_once()

    async def test_handle_logs_correlation_id(
        self,
        handler,
        sample_command,
        sample_chunks,
        mock_chunking_service,
        mock_logger,
    ):
        """Debería loggear correlation_id."""
        # Arrange
        mock_chunking_service.chunk_text.return_value = sample_chunks

        # Act
        result = await handler.handle(sample_command)

        # Assert
        assert result.success is True

        # Verificar que se loggeó correlation_id
        info_calls = mock_logger.info.call_args_list
        assert any(
            "correlation_id" in str(call) and "corr-456" in str(call)
            for call in info_calls
        )
