"""Tests para ContentChunkMapper."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import numpy as np
import pytest

from src.chunking.domain.aggregates.content_chunk import ContentChunk


def create_normalized_vector(size: int = 768, seed: float = 0.1) -> np.ndarray:
    """Crea un vector normalizado para tests."""
    vector = np.full(size, seed, dtype=np.float32)
    # Normalizar a magnitud 1.0
    magnitude = np.linalg.norm(vector)
    return vector / magnitude


from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.chunking.domain.value_objects.token_count import TokenCount
from src.chunking.domain.value_objects.vector_embedding import VectorEmbedding
from src.chunking.infra.persistence.mappers.content_chunk_mapper import (
    ContentChunkMapper,
)
from src.chunking.infra.persistence.models.content_chunk_model import (
    ContentChunkModel,
)


class TestContentChunkMapper:
    """Tests para ContentChunkMapper."""

    def test_to_domain_converts_model_to_aggregate(self):
        """Debería convertir modelo ORM a aggregate de dominio."""
        # Arrange
        now = datetime.now(timezone.utc)

        model = ContentChunkModel(
            id=str(uuid4()),
            article_id="art-456",
            content="Test chunk content for mapping",
            embedding=create_normalized_vector(768).tolist(),
            embedding_model="nomic-embed-text-v1.5",
            summary_text="This is a test summary.",
            summary_sentence_count=3,
            position=0,
            start_char=0,
            end_char=100,
            token_count=50,
            token_encoding="cl100k_base",
            source_url="https://example.com/article",
            status="PENDING",
            created_at=now,
            updated_at=now,
        )

        # Act
        aggregate = ContentChunkMapper.to_domain(model)

        # Assert
        assert isinstance(aggregate, ContentChunk)
        assert isinstance(aggregate.id.value, UUID)
        assert aggregate.article_id == "art-456"
        assert aggregate.content == "Test chunk content for mapping"
        assert aggregate.position == 0
        assert aggregate.start_char == 0
        assert aggregate.end_char == 100
        assert aggregate.token_count.value == 50
        assert aggregate.token_count.encoding == "cl100k_base"
        assert aggregate.source_url == "https://example.com/article"
        assert aggregate.status == ChunkStatus.PENDING
        assert aggregate.created_at == now
        assert aggregate.updated_at == now

        # Verificar embedding
        assert aggregate.embedding is not None
        assert aggregate.embedding.dimension == 768
        assert aggregate.embedding.model == "nomic-embed-text-v1.5"
        assert len(aggregate.embedding.vector) == 768

        # Verificar summary
        assert aggregate.summary is not None
        assert aggregate.summary.content == "This is a test summary."
        assert aggregate.summary.sentence_count == 3

    def test_to_domain_handles_none_embedding(self):
        """Debería manejar modelo sin embedding."""
        # Arrange
        now = datetime.now(timezone.utc)

        model = ContentChunkModel(
            id=str(uuid4()),
            article_id="art-456",
            content="Test content",
            embedding=None,
            embedding_model=None,
            summary_text=None,
            summary_sentence_count=None,
            position=0,
            start_char=0,
            end_char=100,
            token_count=50,
            token_encoding="cl100k_base",
            source_url="https://example.com/article",
            status="PENDING",
            created_at=now,
            updated_at=now,
        )

        # Act
        aggregate = ContentChunkMapper.to_domain(model)

        # Assert
        assert aggregate.embedding is None
        assert aggregate.summary is None

    def test_to_model_converts_aggregate_to_model(self):
        """Debería convertir aggregate de dominio a modelo ORM."""
        # Arrange
        now = datetime.now(timezone.utc)

        embedding = VectorEmbedding(
            vector=create_normalized_vector(768),
            model="nomic-embed-text-v1.5",
            dimension=768,
        )

        summary = ChunkSummary(
            content="This is a test summary.",
            sentence_count=3,
        )

        chunk_uuid = uuid4()
        aggregate = ContentChunk(
            id=ChunkId(chunk_uuid),
            article_id="art-456",
            content="Test chunk content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            embedding=embedding,
            summary=summary,
            status=ChunkStatus.EMBEDDED,
            created_at=now,
            updated_at=now,
        )

        # Act
        model = ContentChunkMapper.to_model(aggregate)

        # Assert
        assert isinstance(model, ContentChunkModel)
        assert model.id == str(chunk_uuid)
        assert model.article_id == "art-456"
        assert model.content == "Test chunk content"
        assert model.position == 0
        assert model.start_char == 0
        assert model.end_char == 100
        assert model.token_count == 50
        assert model.token_encoding == "cl100k_base"
        assert model.source_url == "https://example.com/article"
        assert model.status == "EMBEDDED"
        assert model.created_at == now
        assert model.updated_at == now

        # Verificar embedding
        assert model.embedding is not None
        assert len(model.embedding) == 768
        assert model.embedding_model == "nomic-embed-text-v1.5"

        # Verificar summary
        assert model.summary_text == "This is a test summary."
        assert model.summary_sentence_count == 3

    def test_to_model_handles_none_values(self):
        """Debería manejar aggregate sin embedding ni summary."""
        # Arrange
        now = datetime.now(timezone.utc)

        aggregate = ContentChunk(
            id=ChunkId(uuid4()),
            article_id="art-456",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            embedding=None,
            summary=None,
            status=ChunkStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        # Act
        model = ContentChunkMapper.to_model(aggregate)

        # Assert
        assert model.embedding is None
        assert model.embedding_model is None
        assert model.summary_text is None
        assert model.summary_sentence_count is None

    def test_round_trip_conversion_preserves_data(self):
        """Debería preservar datos en conversión de ida y vuelta."""
        # Arrange
        now = datetime.now(timezone.utc)

        embedding = VectorEmbedding(
            vector=create_normalized_vector(768, seed=0.2),
            model="nomic-embed-text-v1.5",
            dimension=768,
        )

        summary = ChunkSummary(
            content="Test summary with three sentences. This is the second. And the third.",
            sentence_count=3,
        )

        chunk_uuid = uuid4()
        original_aggregate = ContentChunk(
            id=ChunkId(chunk_uuid),
            article_id="art-round-trip",
            content="Round trip test content",
            position=5,
            start_char=500,
            end_char=600,
            token_count=TokenCount(value=75, encoding="cl100k_base"),
            source_url="https://example.com/round-trip",
            embedding=embedding,
            summary=summary,
            status=ChunkStatus.SUMMARIZED,
            created_at=now,
            updated_at=now,
        )

        # Act - Round trip
        model = ContentChunkMapper.to_model(original_aggregate)
        restored_aggregate = ContentChunkMapper.to_domain(model)

        # Assert
        assert str(restored_aggregate.id) == str(original_aggregate.id)
        assert restored_aggregate.article_id == original_aggregate.article_id
        assert restored_aggregate.content == original_aggregate.content
        assert restored_aggregate.position == original_aggregate.position
        assert restored_aggregate.start_char == original_aggregate.start_char
        assert restored_aggregate.end_char == original_aggregate.end_char
        assert (
            restored_aggregate.token_count.value == original_aggregate.token_count.value
        )
        assert (
            restored_aggregate.token_count.encoding
            == original_aggregate.token_count.encoding
        )
        assert restored_aggregate.source_url == original_aggregate.source_url
        assert restored_aggregate.status == original_aggregate.status

        # Verificar embedding
        assert restored_aggregate.embedding is not None
        assert (
            restored_aggregate.embedding.dimension
            == original_aggregate.embedding.dimension
        )
        assert restored_aggregate.embedding.model == original_aggregate.embedding.model
        assert len(restored_aggregate.embedding.vector) == len(
            original_aggregate.embedding.vector
        )

        # Verificar summary
        assert restored_aggregate.summary is not None
        assert restored_aggregate.summary.content == original_aggregate.summary.content
        assert (
            restored_aggregate.summary.sentence_count
            == original_aggregate.summary.sentence_count
        )

    def test_to_domain_maps_all_chunk_statuses(self):
        """Debería mapear correctamente todos los estados de chunk."""
        # Arrange
        now = datetime.now(timezone.utc)
        statuses = ["PENDING", "EMBEDDED", "SUMMARIZED", "COMPLETED", "FAILED"]

        for status_str in statuses:
            model = ContentChunkModel(
                id=str(uuid4()),
                article_id="art-456",
                content="Test content",
                embedding=None,
                embedding_model=None,
                summary_text=None,
                summary_sentence_count=None,
                position=0,
                start_char=0,
                end_char=100,
                token_count=50,
                token_encoding="cl100k_base",
                source_url="https://example.com/article",
                status=status_str,
                created_at=now,
                updated_at=now,
            )

            # Act
            aggregate = ContentChunkMapper.to_domain(model)

            # Assert
            assert aggregate.status == ChunkStatus(status_str)

    def test_update_model_updates_existing_model(self):
        """Debería actualizar modelo existente con datos del aggregate."""
        # Arrange
        now = datetime.now(timezone.utc)
        later = datetime(2024, 12, 12, 12, 0, 0, tzinfo=timezone.utc)
        chunk_uuid = uuid4()

        # Modelo existente
        existing_model = ContentChunkModel(
            id=str(chunk_uuid),
            article_id="art-456",
            content="Old content",
            embedding=None,
            embedding_model=None,
            summary_text=None,
            summary_sentence_count=None,
            position=0,
            start_char=0,
            end_char=100,
            token_count=50,
            token_encoding="cl100k_base",
            source_url="https://example.com/old",
            status="PENDING",
            created_at=now,
            updated_at=now,
        )

        # Aggregate actualizado
        new_embedding = VectorEmbedding(
            vector=create_normalized_vector(768, seed=0.5),
            model="nomic-embed-text-v1.5",
            dimension=768,
        )

        new_summary = ChunkSummary(
            content="New summary text.",
            sentence_count=3,
        )

        updated_aggregate = ContentChunk(
            id=ChunkId(chunk_uuid),
            article_id="art-456",
            content="New content",
            position=1,
            start_char=100,
            end_char=200,
            token_count=TokenCount(value=75, encoding="cl100k_base"),
            source_url="https://example.com/new",
            embedding=new_embedding,
            summary=new_summary,
            status=ChunkStatus.COMPLETED,
            created_at=now,
            updated_at=later,
        )

        # Act
        ContentChunkMapper.update_model(existing_model, updated_aggregate)

        # Assert
        assert existing_model.content == "New content"
        assert existing_model.position == 1
        assert existing_model.start_char == 100
        assert existing_model.end_char == 200
        assert existing_model.token_count == 75
        assert existing_model.token_encoding == "cl100k_base"
        assert existing_model.source_url == "https://example.com/new"
        assert existing_model.status == "COMPLETED"
        assert existing_model.updated_at == later

        # Verificar embedding actualizado
        assert existing_model.embedding is not None
        assert len(existing_model.embedding) == 768
        assert existing_model.embedding_model == "nomic-embed-text-v1.5"

        # Verificar summary actualizado
        assert existing_model.summary_text == "New summary text."
        assert existing_model.summary_sentence_count == 3

    def test_update_model_clears_optional_fields_when_none(self):
        """Debería limpiar campos opcionales cuando son None."""
        # Arrange
        now = datetime.now(timezone.utc)
        chunk_uuid = uuid4()

        # Modelo existente con embedding y summary
        existing_model = ContentChunkModel(
            id=str(chunk_uuid),
            article_id="art-456",
            content="Content",
            embedding=create_normalized_vector(768).tolist(),
            embedding_model="old-model",
            summary_text="Old summary",
            summary_sentence_count=3,
            position=0,
            start_char=0,
            end_char=100,
            token_count=50,
            token_encoding="cl100k_base",
            source_url="https://example.com/article",
            status="EMBEDDED",
            created_at=now,
            updated_at=now,
        )

        # Aggregate sin embedding ni summary
        updated_aggregate = ContentChunk(
            id=ChunkId(chunk_uuid),
            article_id="art-456",
            content="Content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            embedding=None,
            summary=None,
            status=ChunkStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        # Act
        ContentChunkMapper.update_model(existing_model, updated_aggregate)

        # Assert
        assert existing_model.embedding is None
        assert existing_model.embedding_model is None
        assert existing_model.summary_text is None
        assert existing_model.summary_sentence_count is None

    def test_to_domain_preserves_value_object_types(self):
        """Debería preservar tipos de Value Objects correctamente."""
        # Arrange
        now = datetime.now(timezone.utc)

        model = ContentChunkModel(
            id=str(uuid4()),
            article_id="art-456",
            content="Test content",
            embedding=None,
            embedding_model=None,
            summary_text=None,
            summary_sentence_count=None,
            position=0,
            start_char=0,
            end_char=100,
            token_count=50,
            token_encoding="cl100k_base",
            source_url="https://example.com/article",
            status="PENDING",
            created_at=now,
            updated_at=now,
        )

        # Act
        aggregate = ContentChunkMapper.to_domain(model)

        # Assert - Verificar tipos de Value Objects
        assert isinstance(aggregate.id, ChunkId)
        assert isinstance(aggregate.token_count, TokenCount)
        assert isinstance(aggregate.status, ChunkStatus)
