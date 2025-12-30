"""Tests unitarios para SemanticClusterMapper."""

import json
from datetime import datetime, timezone

import numpy as np
import pytest

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.value_objects import ClusterId, VectorEmbedding
from src.clustering.infra.persistence.mappers import SemanticClusterMapper
from src.clustering.infra.persistence.models import (
    ClusterMemberModel,
    SemanticClusterModel,
)


class TestSemanticClusterMapper:
    """Tests para SemanticClusterMapper."""

    @pytest.fixture
    def sample_embedding(self) -> VectorEmbedding:
        """Crea embedding de ejemplo."""
        vector = np.random.rand(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)  # Normalizar
        return VectorEmbedding(vector=vector, model="test-model", dimension=768)

    @pytest.fixture
    def sample_cluster(self, sample_embedding: VectorEmbedding) -> SemanticCluster:
        """Crea cluster de ejemplo."""
        cluster = SemanticCluster.create(
            label="Bitcoin Regulation",
            centroid=sample_embedding,
            cluster_id=ClusterId.from_string(
                "cluster-12345678-1234-5678-1234-567812345678"
            ),
        )
        cluster.add_article("article-1")
        cluster.add_article("article-2")
        return cluster

    @pytest.fixture
    def sample_model(self, sample_embedding: VectorEmbedding) -> SemanticClusterModel:
        """Crea modelo ORM de ejemplo."""
        centroid_json = json.dumps(sample_embedding.vector.tolist())

        model = SemanticClusterModel(
            id="cluster-87654321-4321-8765-4321-876543218765",
            label="Ethereum DeFi",
            description="Cluster about Ethereum DeFi",
            size=2,
            centroid=centroid_json,
            algorithm="kmeans",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        )

        model.members = [
            ClusterMemberModel(
                id="cluster-87654321-4321-8765-4321-876543218765-article-3",
                cluster_id="cluster-87654321-4321-8765-4321-876543218765",
                article_id="article-3",
                distance_to_centroid=0.1,
            ),
            ClusterMemberModel(
                id="cluster-87654321-4321-8765-4321-876543218765-article-4",
                cluster_id="cluster-87654321-4321-8765-4321-876543218765",
                article_id="article-4",
                distance_to_centroid=0.2,
            ),
        ]

        return model

    def test_to_domain_converts_model_to_aggregate(
        self,
        sample_model: SemanticClusterModel,
    ):
        """Debería convertir modelo ORM a aggregate correctamente."""
        # Act
        cluster = SemanticClusterMapper.to_domain(sample_model)

        # Assert
        assert str(cluster.id) == sample_model.id
        assert cluster.label == sample_model.label
        assert cluster.size == sample_model.size
        assert len(cluster.article_ids) == 2
        assert "article-3" in cluster.article_ids
        assert "article-4" in cluster.article_ids
        assert cluster.centroid.dimension == 768
        assert cluster.created_at == sample_model.created_at
        assert cluster.updated_at == sample_model.updated_at

    def test_to_domain_preserves_centroid_values(
        self,
        sample_model: SemanticClusterModel,
    ):
        """Debería preservar valores del centroid correctamente."""
        # Arrange
        original_centroid = json.loads(sample_model.centroid)

        # Act
        cluster = SemanticClusterMapper.to_domain(sample_model)

        # Assert
        np.testing.assert_array_almost_equal(
            cluster.centroid.vector,
            np.array(original_centroid, dtype=np.float32),
            decimal=6,
        )

    def test_to_model_converts_aggregate_to_model(
        self,
        sample_cluster: SemanticCluster,
    ):
        """Debería convertir aggregate a modelo ORM correctamente."""
        # Act
        model = SemanticClusterMapper.to_model(sample_cluster)

        # Assert
        assert model.id == str(sample_cluster.id)
        assert model.label == sample_cluster.label
        assert model.size == sample_cluster.size
        assert len(model.members) == 2

        member_article_ids = [m.article_id for m in model.members]
        assert "article-1" in member_article_ids
        assert "article-2" in member_article_ids

        # Verificar centroid serializado
        centroid_list = json.loads(model.centroid)
        assert len(centroid_list) == 768

    def test_to_model_creates_cluster_members(
        self,
        sample_cluster: SemanticCluster,
    ):
        """Debería crear ClusterMemberModel para cada artículo."""
        # Act
        model = SemanticClusterMapper.to_model(sample_cluster)

        # Assert
        assert len(model.members) == len(sample_cluster.article_ids)

        for member in model.members:
            assert member.cluster_id == str(sample_cluster.id)
            assert member.article_id in sample_cluster.article_ids
            assert member.id.startswith(str(sample_cluster.id))

    def test_to_model_preserves_centroid_values(
        self,
        sample_cluster: SemanticCluster,
    ):
        """Debería preservar valores del centroid al serializar."""
        # Arrange
        original_centroid = sample_cluster.centroid.vector

        # Act
        model = SemanticClusterMapper.to_model(sample_cluster)

        # Assert
        centroid_list = json.loads(model.centroid)
        np.testing.assert_array_almost_equal(
            np.array(centroid_list, dtype=np.float32),
            original_centroid,
            decimal=6,
        )

    def test_round_trip_conversion_preserves_data(
        self,
        sample_cluster: SemanticCluster,
    ):
        """Debería preservar datos en conversión ida y vuelta."""
        # Act
        model = SemanticClusterMapper.to_model(sample_cluster)
        cluster_back = SemanticClusterMapper.to_domain(model)

        # Assert
        assert str(cluster_back.id) == str(sample_cluster.id)
        assert cluster_back.label == sample_cluster.label
        assert cluster_back.size == sample_cluster.size
        assert set(cluster_back.article_ids) == set(sample_cluster.article_ids)

        # Verificar centroid (con tolerancia por serialización)
        np.testing.assert_array_almost_equal(
            cluster_back.centroid.vector,
            sample_cluster.centroid.vector,
            decimal=5,
        )

    def test_update_model_updates_existing_model(
        self,
        sample_model: SemanticClusterModel,
        sample_cluster: SemanticCluster,
    ):
        """Debería actualizar modelo existente con datos del aggregate."""
        # Arrange
        original_id = sample_model.id

        # Act
        SemanticClusterMapper.update_model(sample_model, sample_cluster)

        # Assert
        assert sample_model.id == original_id  # ID no cambia
        assert sample_model.label == sample_cluster.label
        assert sample_model.size == sample_cluster.size
        assert len(sample_model.members) == len(sample_cluster.article_ids)

        member_article_ids = [m.article_id for m in sample_model.members]
        for article_id in sample_cluster.article_ids:
            assert article_id in member_article_ids

    def test_update_model_replaces_members_collection(
        self,
        sample_model: SemanticClusterModel,
        sample_cluster: SemanticCluster,
    ):
        """Debería reemplazar colección de members completamente."""
        # Arrange
        original_member_ids = [m.id for m in sample_model.members]

        # Act
        SemanticClusterMapper.update_model(sample_model, sample_cluster)

        # Assert
        new_member_ids = [m.id for m in sample_model.members]

        # Los IDs de members cambian porque se recrean
        assert set(new_member_ids) != set(original_member_ids)

        # Pero los article_ids deben coincidir
        new_article_ids = [m.article_id for m in sample_model.members]
        assert set(new_article_ids) == set(sample_cluster.article_ids)

    def test_update_model_updates_centroid(
        self,
        sample_model: SemanticClusterModel,
        sample_embedding: VectorEmbedding,
    ):
        """Debería actualizar centroid del modelo."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Updated Label",
            centroid=sample_embedding,
            cluster_id=ClusterId.from_string(sample_model.id),
        )

        # Act
        SemanticClusterMapper.update_model(sample_model, cluster)

        # Assert
        centroid_list = json.loads(sample_model.centroid)
        np.testing.assert_array_almost_equal(
            np.array(centroid_list, dtype=np.float32),
            sample_embedding.vector,
            decimal=6,
        )

    def test_to_domain_handles_empty_cluster(
        self,
        sample_embedding: VectorEmbedding,
    ):
        """Debería manejar cluster vacío (sin members)."""
        # Arrange
        centroid_json = json.dumps(sample_embedding.vector.tolist())
        model = SemanticClusterModel(
            id="cluster-11111111-1111-1111-1111-111111111111",
            label="Empty Cluster",
            size=0,
            centroid=centroid_json,
            algorithm="kmeans",
        )
        model.members = []

        # Act
        cluster = SemanticClusterMapper.to_domain(model)

        # Assert
        assert cluster.size == 0
        assert len(cluster.article_ids) == 0
        assert cluster.is_empty()

    def test_to_model_handles_empty_cluster(
        self,
        sample_embedding: VectorEmbedding,
    ):
        """Debería manejar cluster vacío al convertir a modelo."""
        # Arrange
        cluster = SemanticCluster.create(
            label="Empty Cluster",
            centroid=sample_embedding,
        )

        # Act
        model = SemanticClusterMapper.to_model(cluster)

        # Assert
        assert model.size == 0
        assert len(model.members) == 0
