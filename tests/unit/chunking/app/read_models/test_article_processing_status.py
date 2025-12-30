"""Tests para ArticleProcessingStatus read model."""

from datetime import datetime, timezone

import pytest

from src.chunking.app.read_models import ArticleProcessingStatus


class TestRssArticleProcessingStatus:
    """Tests para ArticleProcessingStatus read model."""

    def test_create_article_processing_status(self):
        """Debería crear ArticleProcessingStatus correctamente."""
        # Arrange & Act
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=5,
            chunks_embedded=3,
            chunks_summarized=2,
            chunks_completed=1,
            has_global_summary=False,
            has_tldr=False,
            cluster_id=None,
            status="PROCESSING",
            started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            completed_at=None,
        )

        # Assert
        assert status.article_id == "article-123"
        assert status.total_chunks == 5
        assert status.chunks_embedded == 3
        assert status.chunks_summarized == 2
        assert status.chunks_completed == 1
        assert status.has_global_summary is False
        assert status.has_tldr is False
        assert status.cluster_id is None
        assert status.status == "PROCESSING"
        assert status.started_at == datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert status.completed_at is None

    def test_is_completed_returns_false_when_not_all_chunks_completed(self):
        """Debería retornar False cuando no todos los chunks están completados."""
        # Arrange
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=5,
            chunks_embedded=5,
            chunks_summarized=5,
            chunks_completed=3,  # No todos completados
            has_global_summary=True,
            has_tldr=True,
            cluster_id=None,
            status="PROCESSING",
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )

        # Act & Assert
        assert status.is_completed is False

    def test_is_completed_returns_false_when_no_global_summary(self):
        """Debería retornar False cuando no hay summary global."""
        # Arrange
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=5,
            chunks_embedded=5,
            chunks_summarized=5,
            chunks_completed=5,
            has_global_summary=False,  # Sin summary global
            has_tldr=True,
            cluster_id=None,
            status="PROCESSING",
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )

        # Act & Assert
        assert status.is_completed is False

    def test_is_completed_returns_false_when_no_tldr(self):
        """Debería retornar False cuando no hay TLDR."""
        # Arrange
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=5,
            chunks_embedded=5,
            chunks_summarized=5,
            chunks_completed=5,
            has_global_summary=True,
            has_tldr=False,  # Sin TLDR
            cluster_id=None,
            status="PROCESSING",
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )

        # Act & Assert
        assert status.is_completed is False

    def test_is_completed_returns_false_when_no_chunks(self):
        """Debería retornar False cuando no hay chunks."""
        # Arrange
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=0,  # Sin chunks
            chunks_embedded=0,
            chunks_summarized=0,
            chunks_completed=0,
            has_global_summary=True,
            has_tldr=True,
            cluster_id=None,
            status="PENDING",
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )

        # Act & Assert
        assert status.is_completed is False

    def test_is_completed_returns_true_when_all_conditions_met(self):
        """Debería retornar True cuando todas las condiciones se cumplen."""
        # Arrange
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=5,
            chunks_embedded=5,
            chunks_summarized=5,
            chunks_completed=5,  # Todos completados
            has_global_summary=True,
            has_tldr=True,
            cluster_id="cluster-456",
            status="COMPLETED",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert status.is_completed is True

    def test_progress_percentage_returns_zero_when_no_chunks(self):
        """Debería retornar 0% cuando no hay chunks."""
        # Arrange
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=0,
            chunks_embedded=0,
            chunks_summarized=0,
            chunks_completed=0,
            has_global_summary=False,
            has_tldr=False,
            cluster_id=None,
            status="PENDING",
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )

        # Act
        progress = status.progress_percentage

        # Assert
        assert progress == 0.0

    def test_progress_percentage_calculates_correctly(self):
        """Debería calcular el porcentaje de progreso correctamente."""
        # Arrange
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=10,
            chunks_embedded=8,
            chunks_summarized=6,
            chunks_completed=5,  # 50% completado
            has_global_summary=False,
            has_tldr=False,
            cluster_id=None,
            status="PROCESSING",
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )

        # Act
        progress = status.progress_percentage

        # Assert
        assert progress == 50.0

    def test_progress_percentage_returns_100_when_all_completed(self):
        """Debería retornar 100% cuando todos los chunks están completados."""
        # Arrange
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=5,
            chunks_embedded=5,
            chunks_summarized=5,
            chunks_completed=5,
            has_global_summary=True,
            has_tldr=True,
            cluster_id=None,
            status="COMPLETED",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        # Act
        progress = status.progress_percentage

        # Assert
        assert progress == 100.0

    def test_progress_percentage_with_partial_completion(self):
        """Debería calcular correctamente con completación parcial."""
        # Arrange
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=8,
            chunks_embedded=6,
            chunks_summarized=4,
            chunks_completed=2,  # 25% completado
            has_global_summary=False,
            has_tldr=False,
            cluster_id=None,
            status="PROCESSING",
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )

        # Act
        progress = status.progress_percentage

        # Assert
        assert progress == 25.0

    def test_article_processing_status_with_cluster_id(self):
        """Debería manejar cluster_id correctamente."""
        # Arrange & Act
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=5,
            chunks_embedded=5,
            chunks_summarized=5,
            chunks_completed=5,
            has_global_summary=True,
            has_tldr=True,
            cluster_id="cluster-789",  # Con cluster
            status="COMPLETED",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        # Assert
        assert status.cluster_id == "cluster-789"
        assert status.is_completed is True

    def test_article_processing_status_with_completed_at(self):
        """Debería manejar completed_at correctamente."""
        # Arrange
        started = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        completed = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        # Act
        status = ArticleProcessingStatus(
            article_id="article-123",
            total_chunks=5,
            chunks_embedded=5,
            chunks_summarized=5,
            chunks_completed=5,
            has_global_summary=True,
            has_tldr=True,
            cluster_id=None,
            status="COMPLETED",
            started_at=started,
            completed_at=completed,
        )

        # Assert
        assert status.started_at == started
        assert status.completed_at == completed
        assert status.is_completed is True
