"""Unit tests for ContentChunkMapper."""

from datetime import datetime, timezone
from uuid import uuid4

import numpy as np
import pytest

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects import VectorEmbedding
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.chunking.domain.value_objects.token_count import TokenCount
from src.chunking.infra.persistence.mappers import ContentChunkMapper
from src.chunking.infra.persistence.models import ContentChunkModel


class TestContentChunkMapper:
    """Unit tests for ContentChunkMapper."""

    @pytest.fixture
    def sample_embedding(self) -> VectorEmbedding:
        """Create a sample normalized embedding."""
        vec = np.random.randn(768).astype(np.float32)
        vec = vec / np.linalg.norm(vec)

        return VectorEmbedding(
            vector=vec,
            model="nomic-embed-text",
            dimension=768,
        )

    @pytest.fixture
    def sample_chunk(self, sample_embedding: VectorEmbedding) -> ContentChunk:
        """Create a sample ContentChunk."""
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id=f"article-{uuid4()}",
            content="Bitcoin alcanzó $50,000 en el mercado cripto...",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=150, encoding="cl100k_base"),
            source_url="https://example.com/article",
            status=ChunkStatus.PENDING,
        )

        # Add embedding
        chunk.embed(sample_embedding)

        # Add summary
        summary = ChunkSummary(
            content="Bitcoin alcanzó $50,000. El mercado reaccionó positivamente. "
            "Los inversores están optimistas.",
            sentence_count=3,
        )
        chunk.summarize(summary)

        return chunk

    def test_to_model_converts_correctly(self, sample_chunk: ContentChunk):
        """Debería convertir ContentChunk a ContentChunkModel correctamente."""
        # Act
        model = ContentChunkMapper.to_model(sample_chunk)

        # Assert
        assert model.id == sample_chunk.id.value
        assert model.article_id == sample_chunk.article_id
        assert model.content == sample_chunk.content
        assert model.position == sample_chunk.position
        assert model.start_char == sample_chunk.start_char
        assert model.end_char == sample_chunk.end_char
        assert model.token_count == int(sample_chunk.token_count)
        assert model.source_url == sample_chunk.source_url
        assert model.status == sample_chunk.status.value

        # Verify embedding is converted to list
        assert isinstance(model.embedding, list)
        assert len(model.embedding) == 768

        # Verify summary is converted to text
        assert model.summary == sample_chunk.summary.content

    def test_to_domain_converts_correctly(self, sample_chunk: ContentChunk):
        """Debería convertir ContentChunkModel a ContentChunk correctamente."""
        # Arrange - First convert to model
        model = ContentChunkMapper.to_model(sample_chunk)

        # Act - Convert back to domain
        chunk = ContentChunkMapper.to_domain(model)

        # Assert
        assert chunk.id.value == model.id
        assert chunk.article_id == model.article_id
        assert chunk.content == model.content
        assert chunk.position == model.position
        assert chunk.start_char == model.start_char
        assert chunk.end_char == model.end_char
        assert int(chunk.token_count) == model.token_count
        assert chunk.source_url == model.source_url
        assert chunk.status.value == model.status

        # Verify embedding is converted back
        assert chunk.embedding is not None
        assert chunk.embedding.dimension == 768
        assert chunk.embedding.is_normalized()

        # Verify summary is converted back
        assert chunk.summary is not None
        assert chunk.summary.content == model.summary

    def test_to_model_without_embedding(self):
        """Debería manejar chunks sin embedding."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id=f"article-{uuid4()}",
            content="Content without embedding...",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=150, encoding="cl100k_base"),
            source_url="https://example.com/article",
            status=ChunkStatus.PENDING,
        )

        # Act
        model = ContentChunkMapper.to_model(chunk)

        # Assert
        assert model.embedding is None
        assert model.summary is None

    def test_to_domain_without_embedding(self):
        """Debería manejar modelos sin embedding."""
        # Arrange
        model = ContentChunkModel(
            id=uuid4(),
            article_id=f"article-{uuid4()}",
            content="Content without embedding...",
            position=0,
            start_char=0,
            end_char=100,
            token_count=150,
            source_url="https://example.com/article",
            status="PENDING",
            embedding=None,
            summary=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act
        chunk = ContentChunkMapper.to_domain(model)

        # Assert
        assert chunk.embedding is None
        assert chunk.summary is None
        assert chunk.status == ChunkStatus.PENDING

    def test_round_trip_conversion(self, sample_chunk: ContentChunk):
        """Debería mantener datos después de conversión round-trip."""
        # Act
        model = ContentChunkMapper.to_model(sample_chunk)
        chunk = ContentChunkMapper.to_domain(model)

        # Assert - Verify key fields match
        assert chunk.id.value == sample_chunk.id.value
        assert chunk.article_id == sample_chunk.article_id
        assert chunk.content == sample_chunk.content
        assert chunk.position == sample_chunk.position
        assert chunk.status == sample_chunk.status

        # Verify embedding similarity (may have small numerical differences)
        if sample_chunk.embedding and chunk.embedding:
            similarity = sample_chunk.embedding.cosine_similarity(chunk.embedding)
            assert similarity > 0.99  # Very high similarity

    def test_update_model_updates_fields(self, sample_chunk: ContentChunk):
        """Debería actualizar modelo existente correctamente."""
        # Arrange - Create initial model
        model = ContentChunkModel(
            id=sample_chunk.id.value,
            article_id=sample_chunk.article_id,
            content="Old content",
            position=sample_chunk.position,
            start_char=sample_chunk.start_char,
            end_char=sample_chunk.end_char,
            token_count=int(sample_chunk.token_count),
            source_url=sample_chunk.source_url,
            status="PENDING",
            embedding=None,
            summary=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act - Update model with chunk data
        ContentChunkMapper.update_model(model, sample_chunk)

        # Assert
        assert model.content == sample_chunk.content
        assert model.status == sample_chunk.status.value
        assert model.embedding is not None
        assert model.summary is not None
