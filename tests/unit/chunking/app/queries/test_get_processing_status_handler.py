"""Tests para GetProcessingStatusHandler."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from src.chunking.app.queries.get_processing_status.handler import (
    GetProcessingStatusHandler,
)
from src.chunking.app.queries.get_processing_status.query import (
    GetProcessingStatusQuery,
)
from src.chunking.app.read_models.article_processing_status import (
    ArticleProcessingStatus,
)


class TestGetProcessingStatusHandler:
    """Tests para GetProcessingStatusHandler."""

    @pytest.fixture
    def mock_repository(self):
        """Mock para processing status repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        logger = Mock()
        logger.bind.return_value = logger
        return logger

    @pytest.fixture
    def handler(self, mock_repository, mock_logger):
        """Handler con dependencias mockeadas."""
        return GetProcessingStatusHandler(
            processing_status_repository=mock_repository,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_status(self):
        """Estado de procesamiento de ejemplo."""
        return ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=10,
            chunks_embedded=8,
            chunks_summarized=6,
            chunks_completed=5,
            has_global_summary=True,
            has_tldr=False,
            cluster_id="cluster-456",
            status="PROCESSING",
            started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            completed_at=None,
        )

    @pytest.mark.asyncio
    async def test_handle_returns_status_successfully(
        self,
        handler,
        mock_repository,
        sample_status,
    ):
        """Debería retornar estado exitosamente."""
        # Arrange
        query = GetProcessingStatusQuery(article_id="article-123")
        mock_repository.find_by_article_id.return_value = sample_status

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        assert result.article_id == "article-123"
        assert result.status == "PROCESSING"
        assert result.total_chunks == 10
        assert result.chunks_embedded == 8
        assert result.chunks_summarized == 6
        assert result.chunks_completed == 5
        assert result.has_global_summary is True
        assert result.has_tldr is False
        assert result.cluster_id == "cluster-456"
        assert result.progress_percentage == 50.0  # 5/10 * 100
        assert result.is_completed is False

        mock_repository.find_by_article_id.assert_called_once_with("article-123")

    @pytest.mark.asyncio
    async def test_handle_returns_none_when_not_found(
        self,
        handler,
        mock_repository,
    ):
        """Debería retornar None cuando no se encuentra el estado."""
        # Arrange
        query = GetProcessingStatusQuery(article_id="article-999")
        mock_repository.find_by_article_id.return_value = None

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is None
        mock_repository.find_by_article_id.assert_called_once_with("article-999")

    @pytest.mark.asyncio
    async def test_handle_with_completed_status(
        self,
        handler,
        mock_repository,
    ):
        """Debería manejar estado completado correctamente."""
        # Arrange
        completed_status = ArticleProcessingStatus(
            article_id="article-456",
            total_chunks=5,
            chunks_embedded=5,
            chunks_summarized=5,
            chunks_completed=5,
            has_global_summary=True,
            has_tldr=True,
            cluster_id="cluster-789",
            status="COMPLETED",
            started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )

        query = GetProcessingStatusQuery(article_id="article-456")
        mock_repository.find_by_article_id.return_value = completed_status

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        assert result.status == "COMPLETED"
        assert result.progress_percentage == 100.0
        assert result.is_completed is True
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_handle_preserves_all_status_fields(
        self,
        handler,
        mock_repository,
        sample_status,
    ):
        """Debería preservar todos los campos del estado."""
        # Arrange
        query = GetProcessingStatusQuery(article_id="article-123")
        mock_repository.find_by_article_id.return_value = sample_status

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.article_id == sample_status.article_id
        assert result.total_chunks == sample_status.total_chunks
        assert result.chunks_embedded == sample_status.chunks_embedded
        assert result.chunks_summarized == sample_status.chunks_summarized
        assert result.chunks_completed == sample_status.chunks_completed
        assert result.has_global_summary == sample_status.has_global_summary
        assert result.has_tldr == sample_status.has_tldr
        assert result.cluster_id == sample_status.cluster_id
        assert result.started_at == sample_status.started_at
        assert result.completed_at == sample_status.completed_at

    @pytest.mark.asyncio
    async def test_handle_calculates_progress_correctly(
        self,
        handler,
        mock_repository,
    ):
        """Debería calcular el progreso correctamente."""
        # Arrange
        status = ArticleProcessingStatus(
            article_id="article-789",
            total_chunks=20,
            chunks_embedded=15,
            chunks_summarized=10,
            chunks_completed=8,  # 8/20 = 40%
            has_global_summary=False,
            has_tldr=False,
            cluster_id=None,
            status="PROCESSING",
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )

        query = GetProcessingStatusQuery(article_id="article-789")
        mock_repository.find_by_article_id.return_value = status

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.progress_percentage == 40.0

    @pytest.mark.asyncio
    async def test_handle_raises_exception_on_repository_error(
        self,
        handler,
        mock_repository,
    ):
        """Debería propagar excepción cuando repository falla."""
        # Arrange
        query = GetProcessingStatusQuery(article_id="article-123")
        mock_repository.find_by_article_id.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await handler.handle(query)

        assert "Database error" in str(exc_info.value)
