"""Tests para ArticleEmbeddingMapper."""

from datetime import datetime, timezone

import numpy as np
import pytest

from src.embedding.domain.aggregates import ArticleEmbedding
from src.embedding.infra.persistence.mappers import ArticleEmbeddingMapper
from src.embedding.infra.persistence.models import ArticleEmbeddingModel


class TestRssArticleEmbeddingMapper:
    """Tests para ArticleEmbeddingMapper."""

    @pytest.fixture
    def sample_embedding_vector(self) -> np.ndarray:
        """Crea vector de embedding normalizado de prueba."""
        # Crear vector aleatorio y normalizarlo
        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        return vector

    @pytest.fixture
    def sample_embedding_aggregate(
        self, sample_embedding_vector: np.ndarray
    ) -> ArticleEmbedding:
        """Crea ArticleEmbedding aggregate de prueba."""
        return ArticleEmbedding(
            id="emb-123",
            article_id="art-456",
            embedding=sample_embedding_vector,
            model="nomic-embed-text",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

    @pytest.fixture
    def sample_embedding_model(
        self, sample_embedding_vector: np.ndarray
    ) -> ArticleEmbeddingModel:
        """Crea ArticleEmbeddingModel de prueba."""
        return ArticleEmbeddingModel(
            id="emb-123",
            article_id="art-456",
            embedding=sample_embedding_vector.tolist(),
            model="nomic-embed-text",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

    def test_to_domain_converts_model_to_aggregate(
        self,
        sample_embedding_model: ArticleEmbeddingModel,
    ):
        """Debería convertir ArticleEmbeddingModel a ArticleEmbedding."""
        # Act
        aggregate = ArticleEmbeddingMapper.to_domain(sample_embedding_model)

        # Assert
        assert isinstance(aggregate, ArticleEmbedding)
        assert aggregate.id == sample_embedding_model.id
        assert aggregate.article_id == sample_embedding_model.article_id
        assert aggregate.model == sample_embedding_model.model
        assert aggregate.created_at == sample_embedding_model.created_at
        assert aggregate.updated_at == sample_embedding_model.updated_at

    def test_to_domain_converts_embedding_to_numpy_array(
        self,
        sample_embedding_model: ArticleEmbeddingModel,
    ):
        """Debería convertir embedding de lista a numpy array."""
        # Act
        aggregate = ArticleEmbeddingMapper.to_domain(sample_embedding_model)

        # Assert
        assert isinstance(aggregate.embedding, np.ndarray)
        assert aggregate.embedding.dtype == np.float32
        assert aggregate.embedding.shape == (768,)

    def test_to_domain_preserves_embedding_values(
        self,
        sample_embedding_model: ArticleEmbeddingModel,
    ):
        """Debería preservar valores del embedding."""
        # Act
        aggregate = ArticleEmbeddingMapper.to_domain(sample_embedding_model)

        # Assert
        expected_array = np.array(sample_embedding_model.embedding, dtype=np.float32)
        np.testing.assert_array_almost_equal(aggregate.embedding, expected_array)

    def test_to_model_converts_aggregate_to_model(
        self,
        sample_embedding_aggregate: ArticleEmbedding,
    ):
        """Debería convertir ArticleEmbedding a ArticleEmbeddingModel."""
        # Act
        model = ArticleEmbeddingMapper.to_model(sample_embedding_aggregate)

        # Assert
        assert isinstance(model, ArticleEmbeddingModel)
        assert model.id == sample_embedding_aggregate.id
        assert model.article_id == sample_embedding_aggregate.article_id
        assert model.model == sample_embedding_aggregate.model
        assert model.created_at == sample_embedding_aggregate.created_at
        assert model.updated_at == sample_embedding_aggregate.updated_at

    def test_to_model_converts_embedding_to_list(
        self,
        sample_embedding_aggregate: ArticleEmbedding,
    ):
        """Debería convertir embedding de numpy array a lista."""
        # Act
        model = ArticleEmbeddingMapper.to_model(sample_embedding_aggregate)

        # Assert
        assert isinstance(model.embedding, list)
        assert len(model.embedding) == 768
        assert all(isinstance(x, float) for x in model.embedding)

    def test_to_model_preserves_embedding_values(
        self,
        sample_embedding_aggregate: ArticleEmbedding,
    ):
        """Debería preservar valores del embedding."""
        # Act
        model = ArticleEmbeddingMapper.to_model(sample_embedding_aggregate)

        # Assert
        expected_list = sample_embedding_aggregate.to_list()
        assert model.embedding == expected_list

    def test_round_trip_conversion_preserves_data(
        self,
        sample_embedding_aggregate: ArticleEmbedding,
    ):
        """Debería preservar datos en conversión ida y vuelta."""
        # Act
        model = ArticleEmbeddingMapper.to_model(sample_embedding_aggregate)
        aggregate_back = ArticleEmbeddingMapper.to_domain(model)

        # Assert
        assert aggregate_back.id == sample_embedding_aggregate.id
        assert aggregate_back.article_id == sample_embedding_aggregate.article_id
        assert aggregate_back.model == sample_embedding_aggregate.model
        np.testing.assert_array_almost_equal(
            aggregate_back.embedding,
            sample_embedding_aggregate.embedding,
        )

    def test_update_model_updates_all_fields(
        self,
        sample_embedding_model: ArticleEmbeddingModel,
        sample_embedding_vector: np.ndarray,
    ):
        """Debería actualizar todos los campos del model."""
        # Arrange
        new_vector = sample_embedding_vector * 0.5
        new_vector = new_vector / np.linalg.norm(new_vector)

        updated_aggregate = ArticleEmbedding(
            id="emb-123",
            article_id="art-789",  # Cambiado
            embedding=new_vector,  # Cambiado
            model="new-model",  # Cambiado
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),  # Cambiado
        )

        # Act
        ArticleEmbeddingMapper.update_model(sample_embedding_model, updated_aggregate)

        # Assert
        assert sample_embedding_model.article_id == "art-789"
        assert sample_embedding_model.model == "new-model"
        assert sample_embedding_model.updated_at == datetime(
            2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc
        )

        # Verificar embedding actualizado
        expected_list = updated_aggregate.to_list()
        assert sample_embedding_model.embedding == expected_list

    def test_update_model_preserves_id(
        self,
        sample_embedding_model: ArticleEmbeddingModel,
        sample_embedding_aggregate: ArticleEmbedding,
    ):
        """Debería preservar el ID del model al actualizar."""
        # Arrange
        original_id = sample_embedding_model.id

        # Act
        ArticleEmbeddingMapper.update_model(
            sample_embedding_model, sample_embedding_aggregate
        )

        # Assert
        assert sample_embedding_model.id == original_id

    def test_mapper_is_static(self):
        """Debería ser métodos estáticos (no requiere instancia)."""
        # Arrange
        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)

        aggregate = ArticleEmbedding(
            id="emb-test",
            article_id="art-test",
            embedding=vector,
            model="test-model",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act - Llamar sin instanciar la clase
        model = ArticleEmbeddingMapper.to_model(aggregate)
        aggregate_back = ArticleEmbeddingMapper.to_domain(model)

        # Assert
        assert aggregate_back is not None
        assert aggregate_back.id == "emb-test"
