"""Tests para ArticleAIProcessingPipeline."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.chunking.app.commands.chunk_article.command import ChunkArticleCommand
from src.chunking.app.commands.generate_chunk_embeddings.command import (
    GenerateChunkEmbeddingsCommand,
)
from src.chunking.app.commands.generate_chunk_summaries.command import (
    GenerateChunkSummariesCommand,
)
from src.chunking.app.commands.generate_global_summary.command import (
    GenerateGlobalSummaryCommand,
)
from src.chunking.app.commands.generate_tldr.command import GenerateTLDRCommand
from src.chunking.app.commands.persist_chunks.command import PersistChunksCommand
from src.chunking.app.process_managers.article_ai_processing_pipeline import (
    ArticleAIProcessingPipeline,
    PipelineState,
)
from src.chunking.domain.events import (
    ArticleAIProcessedEvent,
    ChunkCompletedEvent,
    ChunkCreatedEvent,
    ChunkEmbeddedEvent,
    ChunkFailedEvent,
    ChunkSummarizedEvent,
)


@pytest.mark.asyncio
class TestRssArticleAIProcessingPipeline:
    """Tests para ArticleAIProcessingPipeline."""

    @pytest.fixture
    def mock_command_bus(self):
        """Mock para command bus."""
        return AsyncMock()

    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        logger = Mock()
        logger.bind.return_value = logger
        return logger

    @pytest.fixture
    def mock_event_bus(self):
        """Mock para event bus."""
        return AsyncMock()

    @pytest.fixture
    def pipeline(self, mock_command_bus, mock_event_bus, mock_logger):
        """Pipeline con dependencias mockeadas."""
        return ArticleAIProcessingPipeline(
            command_bus=mock_command_bus,
            event_bus=mock_event_bus,
            logger=mock_logger,
            enable_global_summary=True,
            enable_tldr=True,
        )

    async def test_start_pipeline_emits_chunk_article_command(
        self, pipeline, mock_command_bus
    ):
        """Debería emitir ChunkArticleCommand al iniciar pipeline."""
        # Arrange
        article_id = "test-123"
        article_text = "Test article content"
        source_url = "https://example.com/article"

        # Act
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text=article_text,
            source_url=source_url,
        )

        # Assert
        mock_command_bus.send.assert_called_once()
        command = mock_command_bus.send.call_args[0][0]
        assert isinstance(command, ChunkArticleCommand)
        assert command.article_id == article_id
        assert command.text == article_text
        assert command.source_url == source_url

    async def test_start_pipeline_creates_pipeline_state(self, pipeline):
        """Debería crear estado del pipeline al iniciar."""
        # Arrange
        article_id = "test-456"
        article_text = "Test content"
        source_url = "https://example.com"

        # Act
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text=article_text,
            source_url=source_url,
        )

        # Assert
        state = pipeline.get_pipeline_state(article_id)
        assert state is not None
        assert state.article_id == article_id
        assert state.state == PipelineState.CHUNKING
        assert state.article_text == article_text
        assert state.source_url == source_url
        assert state.metrics.started_at is not None

    async def test_on_chunk_created_increments_counter(self, pipeline):
        """Debería incrementar contador de chunks creados."""
        # Arrange
        article_id = "test-789"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        # Establecer total_chunks manualmente (normalmente vendría del ChunkArticleResult)
        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 3

        event = ChunkCreatedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
            position=0,
            token_count=100,
        )

        # Act
        await pipeline.on_chunk_created(event)

        # Assert
        assert state.metrics.chunks_created == 1
        assert state.metrics.total_chunks == 3

    async def test_on_chunk_created_emits_embeddings_command_when_complete(
        self, pipeline, mock_command_bus
    ):
        """Debería emitir GenerateChunkEmbeddingsCommand cuando todos los chunks están creados."""
        # Arrange
        article_id = "test-complete"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        # Establecer total_chunks
        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 3

        # Reset mock para ignorar ChunkArticleCommand
        mock_command_bus.reset_mock()

        # Act - Crear 3 chunks
        for i in range(3):
            event = ChunkCreatedEvent(
                chunk_id=f"chunk-{i}",
                article_id=article_id,
                position=i,
                token_count=100,
            )
            await pipeline.on_chunk_created(event)

        # Assert
        assert mock_command_bus.send.call_count == 1
        command = mock_command_bus.send.call_args[0][0]
        assert isinstance(command, GenerateChunkEmbeddingsCommand)
        assert command.article_id == article_id

    async def test_on_chunk_embedded_increments_counter(self, pipeline):
        """Debería incrementar contador de chunks embedded."""
        # Arrange
        article_id = "test-embed"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        # Simular chunking completo
        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 2
        state.metrics.chunks_created = 2

        event = ChunkEmbeddedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
            embedding_model="nomic-embed-text",
            embedding_dimension=768,
        )

        # Act
        await pipeline.on_chunk_embedded(event)

        # Assert
        assert state.metrics.chunks_embedded == 1

    async def test_on_chunk_embedded_emits_summaries_command_when_complete(
        self, pipeline, mock_command_bus
    ):
        """Debería emitir GenerateChunkSummariesCommand cuando todos los chunks están embedded."""
        # Arrange
        article_id = "test-embed-complete"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 2
        state.metrics.chunks_created = 2

        mock_command_bus.reset_mock()

        # Act - Embed 2 chunks
        for i in range(2):
            event = ChunkEmbeddedEvent(
                chunk_id=f"chunk-{i}",
                article_id=article_id,
                embedding_model="nomic-embed-text",
                embedding_dimension=768,
            )
            await pipeline.on_chunk_embedded(event)

        # Assert
        assert mock_command_bus.send.call_count == 1
        command = mock_command_bus.send.call_args[0][0]
        assert isinstance(command, GenerateChunkSummariesCommand)

    async def test_on_chunk_summarized_increments_counter(self, pipeline):
        """Debería incrementar contador de chunks summarized."""
        # Arrange
        article_id = "test-summary"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 2

        event = ChunkSummarizedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
            sentence_count=3,
        )

        # Act
        await pipeline.on_chunk_summarized(event)

        # Assert
        assert state.metrics.chunks_summarized == 1

    async def test_on_chunk_summarized_emits_persist_command_when_complete(
        self, pipeline, mock_command_bus
    ):
        """Debería emitir PersistChunksCommand cuando todos los chunks están summarized."""
        # Arrange
        article_id = "test-summary-complete"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 2
        state.metrics.chunks_created = 2
        state.metrics.chunks_embedded = 2

        mock_command_bus.reset_mock()

        # Act - Summarize 2 chunks
        for i in range(2):
            event = ChunkSummarizedEvent(
                chunk_id=f"chunk-{i}",
                article_id=article_id,
                sentence_count=3,
            )
            await pipeline.on_chunk_summarized(event)

        # Assert
        assert mock_command_bus.send.call_count == 1
        command = mock_command_bus.send.call_args[0][0]
        assert isinstance(command, PersistChunksCommand)

    async def test_on_chunk_completed_increments_counter(self, pipeline):
        """Debería incrementar contador de chunks completed."""
        # Arrange
        article_id = "test-completed"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 2

        event = ChunkCompletedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
        )

        # Act
        await pipeline.on_chunk_completed(event)

        # Assert
        assert state.metrics.chunks_completed == 1

    async def test_on_chunk_completed_emits_global_summary_when_enabled(
        self, pipeline, mock_command_bus
    ):
        """Debería emitir GenerateGlobalSummaryCommand cuando global summary está habilitado."""
        # Arrange
        article_id = "test-global"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
            enable_global_summary=True,
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 1
        state.metrics.chunks_created = 1
        state.metrics.chunks_embedded = 1
        state.metrics.chunks_summarized = 1

        mock_command_bus.reset_mock()

        # Act
        event = ChunkCompletedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
        )
        await pipeline.on_chunk_completed(event)

        # Assert
        assert mock_command_bus.send.call_count == 1
        command = mock_command_bus.send.call_args[0][0]
        assert isinstance(command, GenerateGlobalSummaryCommand)

    async def test_on_chunk_completed_emits_tldr_when_global_summary_disabled(
        self, pipeline, mock_command_bus
    ):
        """Debería emitir GenerateTLDRCommand cuando global summary está deshabilitado pero TLDR habilitado."""
        # Arrange
        article_id = "test-tldr-only"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
            enable_global_summary=False,
            enable_tldr=True,
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 1
        state.metrics.chunks_created = 1
        state.metrics.chunks_embedded = 1
        state.metrics.chunks_summarized = 1

        mock_command_bus.reset_mock()

        # Act
        event = ChunkCompletedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
        )
        await pipeline.on_chunk_completed(event)

        # Assert
        assert mock_command_bus.send.call_count == 1
        command = mock_command_bus.send.call_args[0][0]
        assert isinstance(command, GenerateTLDRCommand)

    async def test_on_chunk_completed_completes_pipeline_when_all_disabled(
        self, pipeline, mock_command_bus
    ):
        """Debería completar pipeline cuando global summary y TLDR están deshabilitados."""
        # Arrange
        article_id = "test-complete-minimal"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
            enable_global_summary=False,
            enable_tldr=False,
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 1
        state.metrics.chunks_created = 1
        state.metrics.chunks_embedded = 1
        state.metrics.chunks_summarized = 1

        mock_command_bus.reset_mock()

        # Act
        event = ChunkCompletedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
        )
        await pipeline.on_chunk_completed(event)

        # Assert
        mock_command_bus.send.assert_not_called()
        assert state.state == PipelineState.COMPLETED
        assert state.metrics.completed_at is not None

    async def test_on_global_summary_generated_emits_tldr_when_enabled(
        self, pipeline, mock_command_bus
    ):
        """Debería emitir GenerateTLDRCommand después de global summary si está habilitado."""
        # Arrange
        article_id = "test-global-then-tldr"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
            enable_tldr=True,
        )

        mock_command_bus.reset_mock()

        # Act
        await pipeline.on_global_summary_generated(article_id)

        # Assert
        assert mock_command_bus.send.call_count == 1
        command = mock_command_bus.send.call_args[0][0]
        assert isinstance(command, GenerateTLDRCommand)

    async def test_on_global_summary_generated_completes_when_tldr_disabled(
        self, pipeline, mock_command_bus
    ):
        """Debería completar pipeline después de global summary si TLDR está deshabilitado."""
        # Arrange
        article_id = "test-global-only"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
            enable_tldr=False,
        )

        state = pipeline.get_pipeline_state(article_id)
        mock_command_bus.reset_mock()

        # Act
        await pipeline.on_global_summary_generated(article_id)

        # Assert
        mock_command_bus.send.assert_not_called()
        assert state.state == PipelineState.COMPLETED

    async def test_on_tldr_generated_completes_pipeline(self, pipeline):
        """Debería completar pipeline después de generar TLDR."""
        # Arrange
        article_id = "test-tldr-complete"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        state = pipeline.get_pipeline_state(article_id)

        # Act
        await pipeline.on_tldr_generated(article_id)

        # Assert
        assert state.state == PipelineState.COMPLETED
        assert state.metrics.completed_at is not None

    async def test_on_pipeline_failed_marks_as_failed(self, pipeline, mock_event_bus):
        """Debería marcar pipeline como fallido y emitir evento."""
        # Arrange
        article_id = "test-failed"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        error_message = "Test error"

        # Act
        await pipeline.on_pipeline_failed(article_id, error_message)

        # Assert
        # El estado se limpia después del fallo
        state = pipeline.get_pipeline_state(article_id)
        assert state is None

        # Verificar que se emitió ArticleAIProcessedEvent con error
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, ArticleAIProcessedEvent)
        assert event.success is False
        assert event.error_message == error_message

    async def test_get_active_pipelines_count(self, pipeline):
        """Debería contar pipelines activos correctamente."""
        # Arrange & Act
        await pipeline.start_pipeline(
            article_id="active-1",
            article_text="Test 1",
            source_url="https://example.com",
        )
        await pipeline.start_pipeline(
            article_id="active-2",
            article_text="Test 2",
            source_url="https://example.com",
        )

        # Completar uno
        state = pipeline.get_pipeline_state("active-1")
        state.state = PipelineState.COMPLETED

        # Assert
        assert pipeline.get_active_pipelines_count() == 1

    async def test_pipeline_tracks_duration(self, pipeline):
        """Debería trackear duración del pipeline."""
        # Arrange
        article_id = "test-duration"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
            enable_global_summary=False,
            enable_tldr=False,
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 1
        state.metrics.chunks_created = 1
        state.metrics.chunks_embedded = 1
        state.metrics.chunks_summarized = 1

        # Act
        event = ChunkCompletedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
        )
        await pipeline.on_chunk_completed(event)

        # Assert
        assert state.metrics.duration_seconds is not None
        assert state.metrics.duration_seconds >= 0

    async def test_on_chunk_failed_increments_counter(self, pipeline):
        """Debería incrementar contador de chunks fallidos."""
        # Arrange
        article_id = "test-chunk-failed"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 3

        event = ChunkFailedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
            error_message="Test error",
        )

        # Act
        await pipeline.on_chunk_failed(event)

        # Assert
        assert state.metrics.chunks_failed == 1

    async def test_on_chunk_failed_continues_when_below_threshold(self, pipeline):
        """Debería continuar pipeline cuando fallos están por debajo del threshold."""
        # Arrange
        article_id = "test-continue"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 5

        # Act - Fallar 2 chunks (por debajo del máximo de 3)
        for i in range(2):
            event = ChunkFailedEvent(
                chunk_id=f"chunk-{i}",
                article_id=article_id,
                error_message=f"Error {i}",
            )
            await pipeline.on_chunk_failed(event)

        # Assert
        assert state.state != PipelineState.FAILED
        assert state.metrics.chunks_failed == 2

    async def test_on_chunk_failed_aborts_when_threshold_exceeded(
        self, pipeline, mock_event_bus
    ):
        """Debería abortar pipeline cuando se excede el threshold de fallos."""
        # Arrange
        article_id = "test-abort"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 5

        # Act - Fallar 3 chunks (alcanzar el máximo)
        for i in range(3):
            event = ChunkFailedEvent(
                chunk_id=f"chunk-{i}",
                article_id=article_id,
                error_message=f"Error {i}",
            )
            await pipeline.on_chunk_failed(event)

        # Assert
        # El pipeline ya no existe porque se limpió después del fallo
        state = pipeline.get_pipeline_state(article_id)
        assert state is None

        # Verificar que se emitió ArticleAIProcessedEvent con success=False
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, ArticleAIProcessedEvent)
        assert event.success is False
        assert "3 chunks fallidos" in event.error_message

    async def test_on_chunk_failed_aborts_immediately_when_configured(
        self, mock_command_bus, mock_event_bus, mock_logger
    ):
        """Debería abortar inmediatamente cuando abort_on_failure=True."""
        # Arrange
        pipeline = ArticleAIProcessingPipeline(
            command_bus=mock_command_bus,
            event_bus=mock_event_bus,
            logger=mock_logger,
            abort_on_failure=True,
        )

        article_id = "test-abort-immediate"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 5

        # Act - Fallar 1 chunk
        event = ChunkFailedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
            error_message="First error",
        )
        await pipeline.on_chunk_failed(event)

        # Assert
        state = pipeline.get_pipeline_state(article_id)
        assert state is None  # Pipeline limpiado

        # Verificar que se emitió ArticleAIProcessedEvent con success=False
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, ArticleAIProcessedEvent)
        assert event.success is False

    async def test_complete_pipeline_emits_article_ai_processed_event(
        self, pipeline, mock_event_bus
    ):
        """Debería emitir ArticleAIProcessedEvent al completar pipeline."""
        # Arrange
        article_id = "test-complete-event"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
            enable_global_summary=True,
            enable_tldr=True,
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 1
        state.metrics.chunks_created = 1
        state.metrics.chunks_embedded = 1
        state.metrics.chunks_summarized = 1

        # Act
        await pipeline.on_tldr_generated(article_id)

        # Assert
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, ArticleAIProcessedEvent)
        assert event.article_id == article_id
        assert event.success is True
        assert event.chunks_created == 1
        assert event.has_global_summary is True
        assert event.has_tldr is True

    async def test_complete_pipeline_cleans_up_state(self, pipeline):
        """Debería limpiar estado del pipeline al completar."""
        # Arrange
        article_id = "test-cleanup"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
            enable_global_summary=False,
            enable_tldr=False,
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 1
        state.metrics.chunks_created = 1
        state.metrics.chunks_embedded = 1
        state.metrics.chunks_summarized = 1

        # Act
        event = ChunkCompletedEvent(
            chunk_id="chunk-1",
            article_id=article_id,
        )
        await pipeline.on_chunk_completed(event)

        # Assert
        state = pipeline.get_pipeline_state(article_id)
        assert state is None  # Estado limpiado

    async def test_fail_pipeline_emits_article_ai_processed_event_with_error(
        self, pipeline, mock_event_bus
    ):
        """Debería emitir ArticleAIProcessedEvent con error al fallar."""
        # Arrange
        article_id = "test-fail-event"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        state = pipeline.get_pipeline_state(article_id)
        state.metrics.total_chunks = 3
        state.metrics.chunks_created = 2

        error_message = "Critical error occurred"

        # Act
        await pipeline.on_pipeline_failed(article_id, error_message)

        # Assert
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, ArticleAIProcessedEvent)
        assert event.article_id == article_id
        assert event.success is False
        assert event.error_message == error_message
        assert event.chunks_created == 2

    async def test_fail_pipeline_cleans_up_state(self, pipeline):
        """Debería limpiar estado del pipeline al fallar."""
        # Arrange
        article_id = "test-fail-cleanup"
        await pipeline.start_pipeline(
            article_id=article_id,
            article_text="Test",
            source_url="https://example.com",
        )

        # Act
        await pipeline.on_pipeline_failed(article_id, "Test error")

        # Assert
        state = pipeline.get_pipeline_state(article_id)
        assert state is None  # Estado limpiado
