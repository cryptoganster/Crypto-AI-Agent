"""
Tests unitarios para ContextPackMapper.

Verifica conversión entre ContextPack domain y ContextPackModel ORM.
"""

from datetime import datetime, timezone

import pytest

from src.rag.domain.aggregates.context_pack import ContextPack
from src.rag.domain.value_objects.context_chunk import ContextChunk
from src.rag.domain.value_objects.context_pack_id import ContextPackId
from src.rag.infra.persistence.mappers.context_pack_mapper import ContextPackMapper
from src.rag.infra.persistence.models.context_chunk_model import ContextChunkModel
from src.rag.infra.persistence.models.context_pack_model import ContextPackModel


class TestContextPackMapper:
    """Tests para ContextPackMapper."""

    @pytest.fixture
    def sample_chunks(self) -> list[ContextChunk]:
        """Crea chunks de ejemplo."""
        return [
            ContextChunk(
                chunk_id="chunk-1",
                content="First chunk content",
                position=0,
                relevance_score=0.95,
                token_count=50,
            ),
            ContextChunk(
                chunk_id="chunk-2",
                content="Second chunk content",
                position=1,
                relevance_score=0.85,
                token_count=45,
            ),
            ContextChunk(
                chunk_id="chunk-3",
                content="Third chunk content",
                position=2,
                relevance_score=0.75,
                token_count=40,
            ),
        ]

    @pytest.fixture
    def sample_context_pack(self, sample_chunks) -> ContextPack:
        """Crea ContextPack de ejemplo."""
        return ContextPack(
            id=ContextPackId("pack-123"),
            article_id="article-456",
            query="test query",
            chunks=sample_chunks,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            metadata={"source": "test", "version": "1.0"},
        )

    @pytest.fixture
    def sample_context_pack_model(self) -> ContextPackModel:
        """Crea ContextPackModel de ejemplo."""
        model = ContextPackModel(
            id="pack-123",
            article_id="article-456",
            query="test query",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            total_chunks=3,
            total_tokens=135,
            avg_relevance_score=0.85,
            metadata={"source": "test", "version": "1.0"},
        )

        model.chunks = [
            ContextChunkModel(
                id="chunk-model-1",
                context_pack_id="pack-123",
                chunk_id="chunk-1",
                content="First chunk content",
                position=0,
                relevance_score=0.95,
                token_count=50,
                created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            ContextChunkModel(
                id="chunk-model-2",
                context_pack_id="pack-123",
                chunk_id="chunk-2",
                content="Second chunk content",
                position=1,
                relevance_score=0.85,
                token_count=45,
                created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            ContextChunkModel(
                id="chunk-model-3",
                context_pack_id="pack-123",
                chunk_id="chunk-3",
                content="Third chunk content",
                position=2,
                relevance_score=0.75,
                token_count=40,
                created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        return model

    def test_to_domain_converts_correctly(self, sample_context_pack_model):
        """Debería convertir ContextPackModel a ContextPack correctamente."""
        # Act
        context_pack = ContextPackMapper.to_domain(sample_context_pack_model)

        # Assert
        assert str(context_pack.id) == "pack-123"
        assert context_pack.article_id == "article-456"
        assert context_pack.query == "test query"
        assert context_pack.total_chunks == 3
        assert context_pack.total_tokens == 135
        assert context_pack.avg_relevance_score == 0.85
        assert context_pack.metadata == {"source": "test", "version": "1.0"}
        assert len(context_pack.chunks) == 3

    def test_to_domain_converts_chunks_in_order(self, sample_context_pack_model):
        """Debería convertir chunks en orden correcto."""
        # Act
        context_pack = ContextPackMapper.to_domain(sample_context_pack_model)

        # Assert
        assert context_pack.chunks[0].chunk_id == "chunk-1"
        assert context_pack.chunks[0].position == 0
        assert context_pack.chunks[1].chunk_id == "chunk-2"
        assert context_pack.chunks[1].position == 1
        assert context_pack.chunks[2].chunk_id == "chunk-3"
        assert context_pack.chunks[2].position == 2

    def test_to_domain_handles_empty_metadata(self):
        """Debería manejar metadata vacío correctamente."""
        # Arrange
        model = ContextPackModel(
            id="pack-empty",
            article_id="article-123",
            query="test",
            created_at=datetime.utcnow(),
            total_chunks=0,
            total_tokens=0,
            metadata=None,
        )
        model.chunks = []

        # Act
        context_pack = ContextPackMapper.to_domain(model)

        # Assert
        assert context_pack.metadata == {}

    def test_to_model_converts_correctly(self, sample_context_pack):
        """Debería convertir ContextPack a ContextPackModel correctamente."""
        # Act
        model = ContextPackMapper.to_model(sample_context_pack)

        # Assert
        assert model.id == "pack-123"
        assert model.article_id == "article-456"
        assert model.query == "test query"
        assert model.total_chunks == 3
        assert model.total_tokens == 135
        assert model.avg_relevance_score == 0.85
        assert model.metadata == {"source": "test", "version": "1.0"}
        assert len(model.chunks) == 3

    def test_to_model_creates_chunk_models(self, sample_context_pack):
        """Debería crear ContextChunkModels correctamente."""
        # Act
        model = ContextPackMapper.to_model(sample_context_pack)

        # Assert
        assert len(model.chunks) == 3

        chunk_1 = model.chunks[0]
        assert chunk_1.context_pack_id == "pack-123"
        assert chunk_1.chunk_id == "chunk-1"
        assert chunk_1.content == "First chunk content"
        assert chunk_1.position == 0
        assert chunk_1.relevance_score == 0.95
        assert chunk_1.token_count == 50

    def test_to_model_preserves_chunk_order(self, sample_context_pack):
        """Debería preservar orden de chunks."""
        # Act
        model = ContextPackMapper.to_model(sample_context_pack)

        # Assert
        positions = [chunk.position for chunk in model.chunks]
        assert positions == [0, 1, 2]

    def test_update_model_updates_attributes(
        self, sample_context_pack_model, sample_chunks
    ):
        """Debería actualizar atributos del modelo."""
        # Arrange
        updated_pack = ContextPack(
            id=ContextPackId("pack-123"),
            article_id="article-456",
            query="updated query",
            chunks=sample_chunks[:2],  # Solo 2 chunks
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            metadata={"updated": True},
        )

        # Act
        ContextPackMapper.update_model(sample_context_pack_model, updated_pack)

        # Assert
        assert sample_context_pack_model.query == "updated query"
        assert sample_context_pack_model.total_chunks == 2
        assert sample_context_pack_model.total_tokens == 95
        assert sample_context_pack_model.metadata == {"updated": True}

    def test_update_model_replaces_chunks(
        self, sample_context_pack_model, sample_chunks
    ):
        """Debería reemplazar chunks existentes."""
        # Arrange
        updated_pack = ContextPack(
            id=ContextPackId("pack-123"),
            article_id="article-456",
            query="test query",
            chunks=sample_chunks[:1],  # Solo 1 chunk
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            metadata={},
        )

        original_chunk_count = len(sample_context_pack_model.chunks)

        # Act
        ContextPackMapper.update_model(sample_context_pack_model, updated_pack)

        # Assert
        assert original_chunk_count == 3
        assert len(sample_context_pack_model.chunks) == 1
        assert sample_context_pack_model.chunks[0].chunk_id == "chunk-1"

    def test_roundtrip_conversion_preserves_data(self, sample_context_pack):
        """Debería preservar datos en conversión ida y vuelta."""
        # Act
        model = ContextPackMapper.to_model(sample_context_pack)
        restored_pack = ContextPackMapper.to_domain(model)

        # Assert
        assert str(restored_pack.id) == str(sample_context_pack.id)
        assert restored_pack.article_id == sample_context_pack.article_id
        assert restored_pack.query == sample_context_pack.query
        assert restored_pack.total_chunks == sample_context_pack.total_chunks
        assert restored_pack.total_tokens == sample_context_pack.total_tokens
        assert (
            restored_pack.avg_relevance_score == sample_context_pack.avg_relevance_score
        )
        assert len(restored_pack.chunks) == len(sample_context_pack.chunks)

    def test_to_model_is_static_method(self, sample_context_pack):
        """Debería ser método estático (no requiere instancia)."""
        # Act - Llamar sin instanciar la clase
        model = ContextPackMapper.to_model(sample_context_pack)

        # Assert
        assert model is not None
        assert model.id == "pack-123"

    def test_to_domain_is_static_method(self, sample_context_pack_model):
        """Debería ser método estático (no requiere instancia)."""
        # Act - Llamar sin instanciar la clase
        context_pack = ContextPackMapper.to_domain(sample_context_pack_model)

        # Assert
        assert context_pack is not None
        assert str(context_pack.id) == "pack-123"
