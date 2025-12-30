"""Tests de integración para SemanticCluster repositories."""

import numpy as np
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.value_objects import ClusterId, VectorEmbedding
from src.clustering.infra.persistence.repositories import (
    SqlAlchemySemanticClusterReadRepository,
    SqlAlchemySemanticClusterWriteRepository,
)


@pytest.mark.integration
class TestSemanticClusterRepositories:
    """Tests de integración para repositorios de SemanticCluster."""

    @pytest.fixture
    def write_repository(self, db_session: AsyncSession):
        """Crea write repository con sesión de test."""
        return SqlAlchemySemanticClusterWriteRepository(db_session)

    @pytest.fixture
    def read_repository(self, db_session: AsyncSession):
        """Crea read repository con sesión de test."""
        return SqlAlchemySemanticClusterReadRepository(db_session)

    @pytest.fixture
    def sample_embedding(self) -> VectorEmbedding:
        """Crea embedding de ejemplo."""
        values = np.random.rand(768).astype(np.float32)
        values = values / np.linalg.norm(values)  # Normalizar
        return VectorEmbedding(values=values)

    @pytest.fixture
    def sample_cluster(self, sample_embedding: VectorEmbedding) -> SemanticCluster:
        """Crea cluster de ejemplo."""
        cluster = SemanticCluster.create(
            label="Bitcoin Regulation",
            centroid=sample_embedding,
        )
        cluster.add_article("article-1")
        cluster.add_article("article-2")
        return cluster

    async def test_save_and_find_by_id(
        self,
        write_repository: SqlAlchemySemanticClusterWriteRepository,
        read_repository: SqlAlchemySemanticClusterReadRepository,
        sample_cluster: SemanticCluster,
        db_session: AsyncSession,
    ):
        """Debería guardar y recuperar cluster por ID."""
        # Arrange
        cluster_id = str(sample_cluster.id)

        # Act - Save
        await write_repository.save(sample_cluster)
        await db_session.commit()

        # Act - Find
        found = await read_repository.find_by_id(cluster_id)

        # Assert
        assert found is not None
        assert str(found.id) == cluster_id
        assert found.label == sample_cluster.label
        assert found.size == sample_cluster.size
        assert set(found.article_ids) == set(sample_cluster.article_ids)

        # Verificar centroid (con tolerancia por serialización)
        np.testing.assert_array_almost_equal(
            found.centroid.values,
            sample_cluster.centroid.values,
            decimal=5,
        )

    async def test_save_updates_existing_cluster(
        self,
        write_repository: SqlAlchemySemanticClusterWriteRepository,
        read_repository: SqlAlchemySemanticClusterReadRepository,
        sample_cluster: SemanticCluster,
        db_session: AsyncSession,
    ):
        """Debería actualizar cluster existente."""
        # Arrange - Save initial
        await write_repository.save(sample_cluster)
        await db_session.commit()

        # Act - Modify and save again
        sample_cluster.add_article("article-3")
        sample_cluster.update_label(
            "Updated Label",
            [("bitcoin", 0.8), ("regulation", 0.6)],
        )
        await write_repository.save(sample_cluster)
        await db_session.commit()

        # Assert
        found = await read_repository.find_by_id(str(sample_cluster.id))
        assert found is not None
        assert found.label == "Updated Label"
        assert found.size == 3
        assert "article-3" in found.article_ids

    async def test_find_by_article_id(
        self,
        write_repository: SqlAlchemySemanticClusterWriteRepository,
        read_repository: SqlAlchemySemanticClusterReadRepository,
        sample_cluster: SemanticCluster,
        db_session: AsyncSession,
    ):
        """Debería encontrar cluster por article_id."""
        # Arrange
        await write_repository.save(sample_cluster)
        await db_session.commit()

        # Act
        found = await read_repository.find_by_article_id("article-1")

        # Assert
        assert found is not None
        assert str(found.id) == str(sample_cluster.id)
        assert "article-1" in found.article_ids

    async def test_find_by_article_id_returns_none_when_not_found(
        self,
        read_repository: SqlAlchemySemanticClusterReadRepository,
    ):
        """Debería retornar None cuando artículo no está en ningún cluster."""
        # Act
        found = await read_repository.find_by_article_id("nonexistent-article")

        # Assert
        assert found is None

    async def test_find_all_returns_all_clusters(
        self,
        write_repository: SqlAlchemySemanticClusterWriteRepository,
        read_repository: SqlAlchemySemanticClusterReadRepository,
        sample_embedding: VectorEmbedding,
        db_session: AsyncSession,
    ):
        """Debería retornar todos los clusters."""
        # Arrange - Create multiple clusters
        cluster1 = SemanticCluster.create("Cluster 1", sample_embedding)
        cluster2 = SemanticCluster.create("Cluster 2", sample_embedding)
        cluster3 = SemanticCluster.create("Cluster 3", sample_embedding)

        await write_repository.save(cluster1)
        await write_repository.save(cluster2)
        await write_repository.save(cluster3)
        await db_session.commit()

        # Act
        clusters = await read_repository.find_all()

        # Assert
        assert len(clusters) >= 3
        cluster_ids = [str(c.id) for c in clusters]
        assert str(cluster1.id) in cluster_ids
        assert str(cluster2.id) in cluster_ids
        assert str(cluster3.id) in cluster_ids

    async def test_find_all_with_pagination(
        self,
        write_repository: SqlAlchemySemanticClusterWriteRepository,
        read_repository: SqlAlchemySemanticClusterReadRepository,
        sample_embedding: VectorEmbedding,
        db_session: AsyncSession,
    ):
        """Debería paginar resultados correctamente."""
        # Arrange - Create multiple clusters
        for i in range(5):
            cluster = SemanticCluster.create(f"Cluster {i}", sample_embedding)
            await write_repository.save(cluster)
        await db_session.commit()

        # Act
        page1 = await read_repository.find_all(limit=2, offset=0)
        page2 = await read_repository.find_all(limit=2, offset=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2

        # Verificar que son diferentes
        page1_ids = [str(c.id) for c in page1]
        page2_ids = [str(c.id) for c in page2]
        assert set(page1_ids).isdisjoint(set(page2_ids))

    async def test_count_returns_total_clusters(
        self,
        write_repository: SqlAlchemySemanticClusterWriteRepository,
        read_repository: SqlAlchemySemanticClusterReadRepository,
        sample_embedding: VectorEmbedding,
        db_session: AsyncSession,
    ):
        """Debería contar total de clusters."""
        # Arrange
        initial_count = await read_repository.count()

        # Create 3 clusters
        for i in range(3):
            cluster = SemanticCluster.create(f"Cluster {i}", sample_embedding)
            await write_repository.save(cluster)
        await db_session.commit()

        # Act
        final_count = await read_repository.count()

        # Assert
        assert final_count == initial_count + 3

    async def test_exists_returns_true_when_cluster_exists(
        self,
        write_repository: SqlAlchemySemanticClusterWriteRepository,
        read_repository: SqlAlchemySemanticClusterReadRepository,
        sample_cluster: SemanticCluster,
        db_session: AsyncSession,
    ):
        """Debería retornar True cuando cluster existe."""
        # Arrange
        await write_repository.save(sample_cluster)
        await db_session.commit()

        # Act
        exists = await read_repository.exists(str(sample_cluster.id))

        # Assert
        assert exists is True

    async def test_exists_returns_false_when_cluster_not_exists(
        self,
        read_repository: SqlAlchemySemanticClusterReadRepository,
    ):
        """Debería retornar False cuando cluster no existe."""
        # Act
        exists = await read_repository.exists("nonexistent-cluster")

        # Assert
        assert exists is False

    async def test_delete_removes_cluster(
        self,
        write_repository: SqlAlchemySemanticClusterWriteRepository,
        read_repository: SqlAlchemySemanticClusterReadRepository,
        sample_cluster: SemanticCluster,
        db_session: AsyncSession,
    ):
        """Debería eliminar cluster correctamente."""
        # Arrange
        await write_repository.save(sample_cluster)
        await db_session.commit()

        cluster_id = str(sample_cluster.id)

        # Verify exists
        assert await read_repository.exists(cluster_id)

        # Act
        await write_repository.delete(cluster_id)
        await db_session.commit()

        # Assert
        assert not await read_repository.exists(cluster_id)
        found = await read_repository.find_by_id(cluster_id)
        assert found is None

    async def test_delete_cascades_to_members(
        self,
        write_repository: SqlAlchemySemanticClusterWriteRepository,
        read_repository: SqlAlchemySemanticClusterReadRepository,
        sample_cluster: SemanticCluster,
        db_session: AsyncSession,
    ):
        """Debería eliminar members en cascade al eliminar cluster."""
        # Arrange
        await write_repository.save(sample_cluster)
        await db_session.commit()

        cluster_id = str(sample_cluster.id)

        # Verify cluster has members
        found = await read_repository.find_by_id(cluster_id)
        assert found is not None
        assert len(found.article_ids) > 0

        # Act
        await write_repository.delete(cluster_id)
        await db_session.commit()

        # Assert - Members should be deleted too
        # Try to find by article_id should return None
        for article_id in sample_cluster.article_ids:
            cluster_with_article = await read_repository.find_by_article_id(article_id)
            # Should be None or a different cluster
            if cluster_with_article:
                assert str(cluster_with_article.id) != cluster_id

    async def test_save_preserves_member_collection(
        self,
        write_repository: SqlAlchemySemanticClusterWriteRepository,
        read_repository: SqlAlchemySemanticClusterReadRepository,
        sample_cluster: SemanticCluster,
        db_session: AsyncSession,
    ):
        """Debería preservar colección de members correctamente."""
        # Arrange
        await write_repository.save(sample_cluster)
        await db_session.commit()

        # Act
        found = await read_repository.find_by_id(str(sample_cluster.id))

        # Assert
        assert found is not None
        assert len(found.article_ids) == len(sample_cluster.article_ids)
        assert set(found.article_ids) == set(sample_cluster.article_ids)

    async def test_find_by_id_returns_none_when_not_found(
        self,
        read_repository: SqlAlchemySemanticClusterReadRepository,
    ):
        """Debería retornar None cuando cluster no existe."""
        # Act
        found = await read_repository.find_by_id("nonexistent-cluster")

        # Assert
        assert found is None
