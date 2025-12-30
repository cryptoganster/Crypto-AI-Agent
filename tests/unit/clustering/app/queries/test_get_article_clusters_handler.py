"""Tests para GetArticleClustersHandler."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from src.clustering.app.queries.get_article_clusters.handler import (
    GetArticleClustersHandler,
)
from src.clustering.app.queries.get_article_clusters.query import (
    GetArticleClustersQuery,
)
from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.value_objects.cluster_id import ClusterId
from src.clustering.domain.value_objects.vector_embedding import VectorEmbedding


class TestGetArticleClustersHandler:
    """Tests para GetArticleClustersHandler."""

    @pytest.fixture
    def mock_repository(self):
        """Mock para cluster repository."""
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
        return GetArticleClustersHandler(
            cluster_repository=mock_repository,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_cluster(self):
        """Cluster de ejemplo."""
        centroid_vector = np.random.rand(768).astype(np.float32)
        centroid_vector = centroid_vector / np.linalg.norm(centroid_vector)

        return SemanticCluster(
            id=ClusterId.generate(),
            label="Bitcoin ETF Regulation",
            article_ids=["art-1", "art-2", "art-3"],
            centroid=VectorEmbedding(
                vector=centroid_vector,
                model="nomic-embed-text",
                dimension=768,
            ),
            size=3,
            top_terms=[("bitcoin", 0.8), ("etf", 0.7), ("regulation", 0.6)],
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_handle_returns_clusters_successfully(
        self,
        handler,
        mock_repository,
        sample_cluster,
    ):
        """Debería retornar clusters exitosamente."""
        # Arrange
        query = GetArticleClustersQuery(
            min_size=2,
            order_by="size",
            ascending=False,
        )
        mock_repository.find_all.return_value = [sample_cluster]

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        assert result.total_clusters == 1
        assert len(result.clusters) == 1
        assert result.clusters[0].cluster_id == str(sample_cluster.id)
        assert result.clusters[0].label == "Bitcoin ETF Regulation"
        assert result.clusters[0].size == 3
        assert len(result.clusters[0].article_ids) == 3
        assert result.min_size_filter == 2
        assert result.order_by == "size"

        mock_repository.find_all.assert_called_once_with(
            min_size=2,
            order_by="size",
            ascending=False,
        )

    @pytest.mark.asyncio
    async def test_handle_returns_empty_list_when_no_clusters(
        self,
        handler,
        mock_repository,
    ):
        """Debería retornar lista vacía cuando no hay clusters."""
        # Arrange
        query = GetArticleClustersQuery()
        mock_repository.find_all.return_value = []

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        assert result.total_clusters == 0
        assert len(result.clusters) == 0

    @pytest.mark.asyncio
    async def test_handle_with_multiple_clusters(
        self,
        handler,
        mock_repository,
    ):
        """Debería manejar múltiples clusters correctamente."""
        # Arrange
        clusters = []
        for i in range(3):
            centroid_vector = np.random.rand(768).astype(np.float32)
            centroid_vector = centroid_vector / np.linalg.norm(centroid_vector)

            cluster = SemanticCluster(
                id=ClusterId.generate(),
                label=f"Cluster {i}",
                article_ids=[f"art-{i}-1", f"art-{i}-2"],
                centroid=VectorEmbedding(
                    vector=centroid_vector,
                    model="nomic-embed-text",
                    dimension=768,
                ),
                size=2,
                top_terms=[(f"term{i}", 0.8)],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            clusters.append(cluster)

        query = GetArticleClustersQuery(order_by="updated_at")
        mock_repository.find_all.return_value = clusters

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_clusters == 3
        assert len(result.clusters) == 3
        assert result.order_by == "updated_at"

    @pytest.mark.asyncio
    async def test_handle_preserves_cluster_data(
        self,
        handler,
        mock_repository,
        sample_cluster,
    ):
        """Debería preservar todos los datos del cluster."""
        # Arrange
        query = GetArticleClustersQuery()
        mock_repository.find_all.return_value = [sample_cluster]

        # Act
        result = await handler.handle(query)

        # Assert
        cluster_dto = result.clusters[0]
        assert cluster_dto.label == sample_cluster.label
        assert cluster_dto.size == sample_cluster.size
        assert cluster_dto.article_ids == sample_cluster.article_ids
        assert cluster_dto.top_terms == sample_cluster.top_terms
        assert cluster_dto.created_at == sample_cluster.created_at
        assert cluster_dto.updated_at == sample_cluster.updated_at

    @pytest.mark.asyncio
    async def test_handle_raises_exception_on_repository_error(
        self,
        handler,
        mock_repository,
    ):
        """Debería propagar excepción cuando repository falla."""
        # Arrange
        query = GetArticleClustersQuery()
        mock_repository.find_all.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await handler.handle(query)

        assert "Database error" in str(exc_info.value)
