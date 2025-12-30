"""Tests para GetArticleProcessingStatusHandler."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from src.chunking.app.process_managers.article_ai_processing_pipeline import (
    ArticlePipelineState,
    PipelineMetrics,
    PipelineState,
)
from src.chunking.app.queries.get_article_processing_status import (
    ArticleProcessingStatusDTO,
    GetArticleProcessingStatusHandler,
    GetArticleProcessingStatusQuery,
)


class TestGetArticleProcessingStatusHandler:
    """Tests para GetArticleProcessingStatusHandler."""

    @pytest.fixture
    def mock_pipeline_manager(self):
        """Mock para ArticleAIProcessingPipeline."""
        return Mock()

    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        logger = Mock()
        logger.bind.return_value = logger
        return logger

    @pytest.fixture
    def handler(self, mock_pipeline_manager, mock_logger):
        """Handler con dependencias mockeadas."""
        return GetArticleProcessingStatusHandler(
            pipeline_manager=mock_pipeline_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_returns_dto_when_pipeline_exists(
        self,
        handler,
        mock_pipeline_manager,
    ):
        """Debería retornar DTO cuando el pipeline existe."""
        # Arrange
        article_id = "art-123"
        started_at = datetime.now(timezone.utc)

        pipeline_state = ArticlePipelineState(
            article_id=article_id,
            state=PipelineState.EMBEDDING,
            enable_global_summary=True,
            enable_tldr=True,
        )
        pipeline_state.metrics = PipelineMetrics(
            total_chunks=10,
            chunks_created=10,
            chunks_embedded=5,
            chunks_summarized=0,
            chunks_completed=0,
            chunks_failed=0,
            started_at=started_at,
            completed_at=None,
        )

        mock_pipeline_manager.get_pipeline_state.return_value = pipeline_state

        query = GetArticleProcessingStatusQuery(article_id=article_id)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        assert isinstance(result, ArticleProcessingStatusDTO)
        assert result.article_id == article_id
        assert result.state == "embedding"
        assert result.total_chunks == 10
        assert result.chunks_created == 10
        assert result.chunks_embedded == 5
        assert result.chunks_summarized == 0
        assert result.chunks_completed == 0
        assert result.chunks_failed == 0
        assert result.started_at == started_at
        assert result.completed_at is None
        assert result.duration_seconds is None
        assert result.error_message is None
        assert result.enable_global_summary is True
        assert result.enable_tldr is True

        # Verificar que se llamó al pipeline manager
        mock_pipeline_manager.get_pipeline_state.assert_called_once_with(article_id)

    @pytest.mark.asyncio
    async def test_handle_returns_none_when_pipeline_not_found(
        self,
        handler,
        mock_pipeline_manager,
    ):
        """Debería retornar None cuando no hay pipeline activo."""
        # Arrange
        article_id = "art-456"
        mock_pipeline_manager.get_pipeline_state.return_value = None

        query = GetArticleProcessingStatusQuery(article_id=article_id)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is None
        mock_pipeline_manager.get_pipeline_state.assert_called_once_with(article_id)

    @pytest.mark.asyncio
    async def test_handle_does_not_modify_state(
        self,
        handler,
        mock_pipeline_manager,
    ):
        """Debería NO modificar el estado del pipeline (query pura)."""
        # Arrange
        article_id = "art-789"
        pipeline_state = ArticlePipelineState(
            article_id=article_id,
            state=PipelineState.CHUNKING,
        )
        pipeline_state.metrics = PipelineMetrics(
            total_chunks=5,
            chunks_created=3,
            started_at=datetime.now(timezone.utc),
        )

        mock_pipeline_manager.get_pipeline_state.return_value = pipeline_state

        query = GetArticleProcessingStatusQuery(article_id=article_id)

        # Act
        await handler.handle(query)

        # Assert - Solo debe llamar get_pipeline_state (lectura)
        mock_pipeline_manager.get_pipeline_state.assert_called_once()

        # Verificar que NO se llamaron métodos de escritura
        assert (
            not hasattr(mock_pipeline_manager, "set_total_chunks")
            or not mock_pipeline_manager.set_total_chunks.called
        )
        assert (
            not hasattr(mock_pipeline_manager, "start_pipeline")
            or not mock_pipeline_manager.start_pipeline.called
        )

    @pytest.mark.asyncio
    async def test_handle_returns_dto_with_completed_state(
        self,
        handler,
        mock_pipeline_manager,
    ):
        """Debería retornar DTO con estado completed correctamente."""
        # Arrange
        article_id = "art-completed"
        started_at = datetime.now(timezone.utc)
        completed_at = datetime.now(timezone.utc)

        pipeline_state = ArticlePipelineState(
            article_id=article_id,
            state=PipelineState.COMPLETED,
        )
        pipeline_state.metrics = PipelineMetrics(
            total_chunks=10,
            chunks_created=10,
            chunks_embedded=10,
            chunks_summarized=10,
            chunks_completed=10,
            chunks_failed=0,
            started_at=started_at,
            completed_at=completed_at,
        )

        mock_pipeline_manager.get_pipeline_state.return_value = pipeline_state

        query = GetArticleProcessingStatusQuery(article_id=article_id)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        assert result.state == "completed"
        assert result.is_completed is True
        assert result.is_failed is False
        assert result.is_in_progress is False
        assert result.completed_at == completed_at
        assert result.duration_seconds is not None

    @pytest.mark.asyncio
    async def test_handle_returns_dto_with_failed_state(
        self,
        handler,
        mock_pipeline_manager,
    ):
        """Debería retornar DTO con estado failed y error message."""
        # Arrange
        article_id = "art-failed"
        error_message = "Error en chunking: timeout"

        pipeline_state = ArticlePipelineState(
            article_id=article_id,
            state=PipelineState.FAILED,
            error_message=error_message,
        )
        pipeline_state.metrics = PipelineMetrics(
            total_chunks=10,
            chunks_created=5,
            chunks_failed=3,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        mock_pipeline_manager.get_pipeline_state.return_value = pipeline_state

        query = GetArticleProcessingStatusQuery(article_id=article_id)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        assert result.state == "failed"
        assert result.is_failed is True
        assert result.is_completed is False
        assert result.error_message == error_message
        assert result.chunks_failed == 3

    @pytest.mark.asyncio
    async def test_handle_returns_dto_with_all_states(
        self,
        handler,
        mock_pipeline_manager,
    ):
        """Debería retornar DTO correctamente para todos los estados del pipeline."""
        # Arrange
        article_id = "art-all-states"

        states_to_test = [
            PipelineState.PENDING,
            PipelineState.CHUNKING,
            PipelineState.EMBEDDING,
            PipelineState.SUMMARIZING,
            PipelineState.PERSISTING,
            PipelineState.GLOBAL_SUMMARY,
            PipelineState.TLDR,
            PipelineState.COMPLETED,
            PipelineState.FAILED,
        ]

        for state in states_to_test:
            # Arrange
            pipeline_state = ArticlePipelineState(
                article_id=article_id,
                state=state,
            )
            pipeline_state.metrics = PipelineMetrics(
                total_chunks=10,
                started_at=datetime.now(timezone.utc),
            )

            mock_pipeline_manager.get_pipeline_state.return_value = pipeline_state

            query = GetArticleProcessingStatusQuery(article_id=article_id)

            # Act
            result = await handler.handle(query)

            # Assert
            assert result is not None
            assert result.state == state.value
            assert result.article_id == article_id

    @pytest.mark.asyncio
    async def test_dto_progress_percentage_calculation(
        self,
        handler,
        mock_pipeline_manager,
    ):
        """Debería calcular correctamente el porcentaje de progreso."""
        # Arrange
        article_id = "art-progress"

        pipeline_state = ArticlePipelineState(
            article_id=article_id,
            state=PipelineState.EMBEDDING,
        )
        pipeline_state.metrics = PipelineMetrics(
            total_chunks=10,
            chunks_created=10,  # 10 steps
            chunks_embedded=5,  # 5 steps
            chunks_summarized=0,  # 0 steps
            chunks_completed=0,  # 0 steps
            started_at=datetime.now(timezone.utc),
        )

        mock_pipeline_manager.get_pipeline_state.return_value = pipeline_state

        query = GetArticleProcessingStatusQuery(article_id=article_id)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        # Total steps = 10 chunks * 4 stages = 40
        # Completed steps = 10 + 5 + 0 + 0 = 15
        # Progress = 15 / 40 * 100 = 37.5%
        assert result.progress_percentage == 37.5

    @pytest.mark.asyncio
    async def test_dto_progress_percentage_zero_when_no_chunks(
        self,
        handler,
        mock_pipeline_manager,
    ):
        """Debería retornar 0% de progreso cuando no hay chunks."""
        # Arrange
        article_id = "art-no-chunks"

        pipeline_state = ArticlePipelineState(
            article_id=article_id,
            state=PipelineState.PENDING,
        )
        pipeline_state.metrics = PipelineMetrics(
            total_chunks=0,
            started_at=datetime.now(timezone.utc),
        )

        mock_pipeline_manager.get_pipeline_state.return_value = pipeline_state

        query = GetArticleProcessingStatusQuery(article_id=article_id)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        assert result.progress_percentage == 0.0

    @pytest.mark.asyncio
    async def test_dto_is_in_progress_property(
        self,
        handler,
        mock_pipeline_manager,
    ):
        """Debería identificar correctamente si el pipeline está en progreso."""
        # Arrange
        article_id = "art-in-progress"

        # Test: Estado en progreso
        pipeline_state = ArticlePipelineState(
            article_id=article_id,
            state=PipelineState.EMBEDDING,
        )
        pipeline_state.metrics = PipelineMetrics(started_at=datetime.now(timezone.utc))

        mock_pipeline_manager.get_pipeline_state.return_value = pipeline_state
        query = GetArticleProcessingStatusQuery(article_id=article_id)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        assert result.is_in_progress is True
        assert result.is_completed is False
        assert result.is_failed is False
