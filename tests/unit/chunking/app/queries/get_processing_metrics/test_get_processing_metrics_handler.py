"""Tests para GetProcessingMetricsHandler."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from src.chunking.app.process_managers.article_ai_processing_pipeline import (
    ArticleAIProcessingPipeline,
    ArticlePipelineState,
    PipelineMetrics,
    PipelineState,
)
from src.chunking.app.queries.get_processing_metrics.dto import ProcessingMetricsDTO
from src.chunking.app.queries.get_processing_metrics.handler import (
    GetProcessingMetricsHandler,
)
from src.chunking.app.queries.get_processing_metrics.query import (
    GetProcessingMetricsQuery,
)


class TestGetProcessingMetricsHandler:
    """Tests para GetProcessingMetricsHandler."""

    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        logger = Mock()
        logger.bind.return_value = logger
        return logger

    @pytest.fixture
    def mock_pipeline(self):
        """Mock para pipeline."""
        return Mock(spec=ArticleAIProcessingPipeline)

    @pytest.fixture
    def handler(self, mock_pipeline, mock_logger):
        """Handler con dependencias mockeadas."""
        return GetProcessingMetricsHandler(
            pipeline=mock_pipeline,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_with_empty_pipelines_returns_zero_metrics(
        self,
        handler,
        mock_pipeline,
    ):
        """Debería retornar métricas en cero cuando no hay pipelines."""
        # Arrange
        mock_pipeline.get_all_pipeline_states.return_value = {}
        query = GetProcessingMetricsQuery()

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, ProcessingMetricsDTO)
        assert result.total_articles_processed == 0
        assert result.articles_completed == 0
        assert result.articles_failed == 0
        assert result.articles_in_progress == 0
        assert result.total_chunks_created == 0
        assert result.success_rate == 0.0
        assert result.failure_rate == 0.0

    @pytest.mark.asyncio
    async def test_handle_calculates_metrics_correctly(
        self,
        handler,
        mock_pipeline,
    ):
        """Debería calcular métricas correctamente."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Pipeline completado
        completed_state = ArticlePipelineState(
            article_id="art-1",
            state=PipelineState.COMPLETED,
        )
        completed_state.metrics.total_chunks = 10
        completed_state.metrics.chunks_created = 10
        completed_state.metrics.chunks_embedded = 10
        completed_state.metrics.chunks_summarized = 10
        completed_state.metrics.chunks_completed = 10
        completed_state.metrics.chunks_failed = 0
        completed_state.metrics.started_at = now - timedelta(seconds=60)
        completed_state.metrics.completed_at = now

        # Pipeline fallido
        failed_state = ArticlePipelineState(
            article_id="art-2",
            state=PipelineState.FAILED,
        )
        failed_state.metrics.total_chunks = 5
        failed_state.metrics.chunks_created = 5
        failed_state.metrics.chunks_embedded = 3
        failed_state.metrics.chunks_summarized = 0
        failed_state.metrics.chunks_completed = 0
        failed_state.metrics.chunks_failed = 2
        failed_state.metrics.started_at = now - timedelta(seconds=30)
        failed_state.metrics.completed_at = now

        # Pipeline en progreso
        in_progress_state = ArticlePipelineState(
            article_id="art-3",
            state=PipelineState.EMBEDDING,
        )
        in_progress_state.metrics.total_chunks = 8
        in_progress_state.metrics.chunks_created = 8
        in_progress_state.metrics.chunks_embedded = 4
        in_progress_state.metrics.chunks_summarized = 0
        in_progress_state.metrics.chunks_completed = 0
        in_progress_state.metrics.chunks_failed = 0
        in_progress_state.metrics.started_at = now - timedelta(seconds=20)

        mock_pipeline.get_all_pipeline_states.return_value = {
            "art-1": completed_state,
            "art-2": failed_state,
            "art-3": in_progress_state,
        }

        query = GetProcessingMetricsQuery()

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_articles_processed == 3
        assert result.articles_completed == 1
        assert result.articles_failed == 1
        assert result.articles_in_progress == 1

        # Chunks
        assert result.total_chunks_created == 23  # 10 + 5 + 8
        assert result.total_chunks_embedded == 17  # 10 + 3 + 4
        assert result.total_chunks_summarized == 10  # 10 + 0 + 0
        assert result.total_chunks_completed == 10  # 10 + 0 + 0
        assert result.total_chunks_failed == 2  # 0 + 2 + 0

        # Promedios
        assert result.average_chunks_per_article == pytest.approx(23 / 3, rel=0.01)
        assert result.average_processing_time_seconds == pytest.approx(45.0, rel=0.1)

        # Tasas
        assert result.success_rate == pytest.approx(1 / 3, rel=0.01)
        assert result.failure_rate == pytest.approx(1 / 3, rel=0.01)

        # Distribución por estado
        assert result.articles_by_state["completed"] == 1
        assert result.articles_by_state["failed"] == 1
        assert result.articles_by_state["embedding"] == 1

    @pytest.mark.asyncio
    async def test_handle_filters_by_start_date(
        self,
        handler,
        mock_pipeline,
    ):
        """Debería filtrar por fecha de inicio."""
        # Arrange
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        # Pipeline reciente
        recent_state = ArticlePipelineState(
            article_id="art-1",
            state=PipelineState.COMPLETED,
        )
        recent_state.metrics.started_at = now - timedelta(hours=1)
        recent_state.metrics.total_chunks = 10
        recent_state.metrics.chunks_created = 10

        # Pipeline antiguo
        old_state = ArticlePipelineState(
            article_id="art-2",
            state=PipelineState.COMPLETED,
        )
        old_state.metrics.started_at = two_days_ago
        old_state.metrics.total_chunks = 5
        old_state.metrics.chunks_created = 5

        mock_pipeline.get_all_pipeline_states.return_value = {
            "art-1": recent_state,
            "art-2": old_state,
        }

        query = GetProcessingMetricsQuery(start_date=yesterday)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_articles_processed == 1  # Solo el reciente
        assert result.total_chunks_created == 10  # Solo chunks del reciente

    @pytest.mark.asyncio
    async def test_handle_filters_by_end_date(
        self,
        handler,
        mock_pipeline,
    ):
        """Debería filtrar por fecha de fin."""
        # Arrange
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        # Pipeline reciente
        recent_state = ArticlePipelineState(
            article_id="art-1",
            state=PipelineState.COMPLETED,
        )
        recent_state.metrics.started_at = now - timedelta(hours=1)
        recent_state.metrics.total_chunks = 10
        recent_state.metrics.chunks_created = 10

        # Pipeline antiguo
        old_state = ArticlePipelineState(
            article_id="art-2",
            state=PipelineState.COMPLETED,
        )
        old_state.metrics.started_at = two_days_ago
        old_state.metrics.total_chunks = 5
        old_state.metrics.chunks_created = 5

        mock_pipeline.get_all_pipeline_states.return_value = {
            "art-1": recent_state,
            "art-2": old_state,
        }

        query = GetProcessingMetricsQuery(end_date=yesterday)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_articles_processed == 1  # Solo el antiguo
        assert result.total_chunks_created == 5  # Solo chunks del antiguo

    @pytest.mark.asyncio
    async def test_handle_filters_by_state(
        self,
        handler,
        mock_pipeline,
    ):
        """Debería filtrar por estado."""
        # Arrange
        completed_state = ArticlePipelineState(
            article_id="art-1",
            state=PipelineState.COMPLETED,
        )
        completed_state.metrics.total_chunks = 10
        completed_state.metrics.chunks_created = 10

        failed_state = ArticlePipelineState(
            article_id="art-2",
            state=PipelineState.FAILED,
        )
        failed_state.metrics.total_chunks = 5
        failed_state.metrics.chunks_created = 5

        in_progress_state = ArticlePipelineState(
            article_id="art-3",
            state=PipelineState.EMBEDDING,
        )
        in_progress_state.metrics.total_chunks = 8
        in_progress_state.metrics.chunks_created = 8

        mock_pipeline.get_all_pipeline_states.return_value = {
            "art-1": completed_state,
            "art-2": failed_state,
            "art-3": in_progress_state,
        }

        query = GetProcessingMetricsQuery(state_filter="completed")

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_articles_processed == 1  # Solo completados
        assert result.total_chunks_created == 10  # Solo chunks de completados

    @pytest.mark.asyncio
    async def test_handle_calculates_success_rate_correctly(
        self,
        handler,
        mock_pipeline,
    ):
        """Debería calcular tasa de éxito correctamente."""
        # Arrange
        # 7 completados, 2 fallidos, 1 en progreso = 70% success rate
        states = {}
        for i in range(7):
            state = ArticlePipelineState(
                article_id=f"art-{i}",
                state=PipelineState.COMPLETED,
            )
            state.metrics.total_chunks = 10
            state.metrics.chunks_created = 10
            states[f"art-{i}"] = state

        for i in range(7, 9):
            state = ArticlePipelineState(
                article_id=f"art-{i}",
                state=PipelineState.FAILED,
            )
            state.metrics.total_chunks = 10
            state.metrics.chunks_created = 10
            states[f"art-{i}"] = state

        state = ArticlePipelineState(
            article_id="art-9",
            state=PipelineState.EMBEDDING,
        )
        state.metrics.total_chunks = 10
        state.metrics.chunks_created = 10
        states["art-9"] = state

        mock_pipeline.get_all_pipeline_states.return_value = states

        query = GetProcessingMetricsQuery()

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_articles_processed == 10
        assert result.articles_completed == 7
        assert result.articles_failed == 2
        assert result.articles_in_progress == 1
        assert result.success_rate == pytest.approx(0.7, rel=0.01)
        assert result.failure_rate == pytest.approx(0.2, rel=0.01)
        assert result.success_rate_percentage == pytest.approx(70.0, rel=0.1)

    @pytest.mark.asyncio
    async def test_handle_calculates_average_processing_time(
        self,
        handler,
        mock_pipeline,
    ):
        """Debería calcular tiempo promedio de procesamiento."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Pipeline 1: 60 segundos
        state1 = ArticlePipelineState(
            article_id="art-1",
            state=PipelineState.COMPLETED,
        )
        state1.metrics.started_at = now - timedelta(seconds=60)
        state1.metrics.completed_at = now
        state1.metrics.total_chunks = 10
        state1.metrics.chunks_created = 10

        # Pipeline 2: 30 segundos
        state2 = ArticlePipelineState(
            article_id="art-2",
            state=PipelineState.COMPLETED,
        )
        state2.metrics.started_at = now - timedelta(seconds=30)
        state2.metrics.completed_at = now
        state2.metrics.total_chunks = 5
        state2.metrics.chunks_created = 5

        # Pipeline 3: Sin completar (no cuenta para promedio)
        state3 = ArticlePipelineState(
            article_id="art-3",
            state=PipelineState.EMBEDDING,
        )
        state3.metrics.started_at = now - timedelta(seconds=20)
        state3.metrics.total_chunks = 8
        state3.metrics.chunks_created = 8

        mock_pipeline.get_all_pipeline_states.return_value = {
            "art-1": state1,
            "art-2": state2,
            "art-3": state3,
        }

        query = GetProcessingMetricsQuery()

        # Act
        result = await handler.handle(query)

        # Assert
        # Promedio: (60 + 30) / 2 = 45 segundos
        assert result.average_processing_time_seconds == pytest.approx(45.0, rel=0.1)

    @pytest.mark.asyncio
    async def test_handle_does_not_modify_state(
        self,
        handler,
        mock_pipeline,
    ):
        """Debería ser un query puro - NO modificar estado."""
        # Arrange
        state = ArticlePipelineState(
            article_id="art-1",
            state=PipelineState.COMPLETED,
        )
        state.metrics.total_chunks = 10
        state.metrics.chunks_created = 10

        mock_pipeline.get_all_pipeline_states.return_value = {"art-1": state}

        query = GetProcessingMetricsQuery()

        # Act
        await handler.handle(query)

        # Assert
        # Verificar que solo se llamó get_all_pipeline_states (lectura)
        mock_pipeline.get_all_pipeline_states.assert_called_once()

        # Verificar que NO se llamaron métodos de escritura
        assert (
            not hasattr(mock_pipeline, "start_pipeline")
            or not mock_pipeline.start_pipeline.called
        )
        assert (
            not hasattr(mock_pipeline, "set_total_chunks")
            or not mock_pipeline.set_total_chunks.called
        )

    @pytest.mark.asyncio
    async def test_handle_returns_dto_not_aggregate(
        self,
        handler,
        mock_pipeline,
    ):
        """Debería retornar DTO, no aggregate."""
        # Arrange
        state = ArticlePipelineState(
            article_id="art-1",
            state=PipelineState.COMPLETED,
        )
        state.metrics.total_chunks = 10
        state.metrics.chunks_created = 10

        mock_pipeline.get_all_pipeline_states.return_value = {"art-1": state}

        query = GetProcessingMetricsQuery()

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, ProcessingMetricsDTO)
        assert not isinstance(result, ArticlePipelineState)
        assert not isinstance(result, PipelineMetrics)
