"""Unit tests para ContentChunk aggregate."""

from datetime import datetime, timezone

import numpy as np
import pytest

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.events import (
    ChunkCompletedEvent,
    ChunkCreatedEvent,
    ChunkEmbeddedEvent,
    ChunkFailedEvent,
    ChunkSummarizedEvent,
)
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.chunking.domain.value_objects.token_count import TokenCount
from src.chunking.domain.value_objects.vector_embedding import VectorEmbedding


class TestContentChunkCreation:
    """Tests para creación de ContentChunk."""

    def test_create_content_chunk_with_valid_data(self):
        """Debería crear ContentChunk con datos válidos."""
        # Arrange
        chunk_id = ChunkId.generate()
        token_count = TokenCount(value=100, encoding="cl100k_base")

        # Act
        chunk = ContentChunk(
            id=chunk_id,
            article_id="article-123",
            content="Test content for chunk",
            position=0,
            start_char=0,
            end_char=100,
            token_count=token_count,
            source_url="https://example.com/article",
        )

        # Assert
        assert chunk.id == chunk_id
        assert chunk.article_id == "article-123"
        assert chunk.content == "Test content for chunk"
        assert chunk.position == 0
        assert chunk.status == ChunkStatus.PENDING
        assert chunk.embedding is None
        assert chunk.summary is None
        assert chunk.has_uncommitted_events()

    def test_create_chunk_emits_created_event(self):
        """Debería emitir ChunkCreatedEvent al crear."""
        # Arrange & Act
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        # Assert
        events = chunk.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ChunkCreatedEvent)
        assert events[0].chunk_id == str(chunk.id)
        assert events[0].article_id == "article-123"
        assert events[0].position == 0

    def test_create_chunk_with_empty_article_id_raises_error(self):
        """Debería lanzar error si article_id está vacío."""
        # Act & Assert
        with pytest.raises(ValueError, match="article_id no puede estar vacío"):
            ContentChunk(
                id=ChunkId.generate(),
                article_id="",
                content="Test content",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(value=50),
                source_url="https://example.com/article",
            )

    def test_create_chunk_with_empty_content_raises_error(self):
        """Debería lanzar error si content está vacío."""
        # Act & Assert
        with pytest.raises(ValueError, match="content no puede estar vacío"):
            ContentChunk(
                id=ChunkId.generate(),
                article_id="article-123",
                content="",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(value=50),
                source_url="https://example.com/article",
            )

    def test_create_chunk_with_negative_position_raises_error(self):
        """Debería lanzar error si position es negativo."""
        # Act & Assert
        with pytest.raises(ValueError, match="position debe ser >= 0"):
            ContentChunk(
                id=ChunkId.generate(),
                article_id="article-123",
                content="Test content",
                position=-1,
                start_char=0,
                end_char=100,
                token_count=TokenCount(value=50),
                source_url="https://example.com/article",
            )

    def test_create_chunk_with_invalid_char_positions_raises_error(self):
        """Debería lanzar error si end_char <= start_char."""
        # Act & Assert
        with pytest.raises(ValueError, match="end_char debe ser > start_char"):
            ContentChunk(
                id=ChunkId.generate(),
                article_id="article-123",
                content="Test content",
                position=0,
                start_char=100,
                end_char=100,
                token_count=TokenCount(value=50),
                source_url="https://example.com/article",
            )

    def test_create_chunk_with_invalid_url_raises_error(self):
        """Debería lanzar error si source_url no es válida."""
        # Act & Assert
        with pytest.raises(ValueError, match="source_url debe ser una URL válida"):
            ContentChunk(
                id=ChunkId.generate(),
                article_id="article-123",
                content="Test content",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(value=50),
                source_url="not-a-url",
            )


class TestContentChunkEmbed:
    """Tests para método embed()."""

    def test_embed_chunk_with_valid_embedding(self):
        """Debería agregar embedding y cambiar estado a EMBEDDED."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        # Crear embedding normalizado
        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(
            vector=vector, model="nomic-embed-text", dimension=768
        )

        # Act
        chunk.embed(embedding)

        # Assert
        assert chunk.embedding == embedding
        assert chunk.status == ChunkStatus.EMBEDDED
        assert chunk.has_embedding()
        assert chunk.can_summarize()

    def test_embed_emits_embedded_event(self):
        """Debería emitir ChunkEmbeddedEvent."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=768)

        # Clear creation event
        chunk.mark_events_as_committed()

        # Act
        chunk.embed(embedding)

        # Assert
        events = chunk.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ChunkEmbeddedEvent)
        assert events[0].chunk_id == str(chunk.id)
        assert events[0].embedding_model == "test"
        assert events[0].embedding_dimension == 768

    def test_embed_chunk_already_embedded_raises_error(self):
        """Debería lanzar error si el chunk ya tiene embedding."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=768)
        chunk.embed(embedding)

        # Act & Assert
        with pytest.raises(ValueError, match="Chunk already has embedding"):
            chunk.embed(embedding)

    def test_embed_chunk_wrong_dimension_raises_error(self):
        """Debería lanzar error si embedding no es 768 dimensiones."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        vector = np.random.randn(512).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=512)

        # Act & Assert
        with pytest.raises(ValueError, match="Embedding must be 768 dimensions"):
            chunk.embed(embedding)


class TestContentChunkSummarize:
    """Tests para método summarize()."""

    def test_summarize_chunk_with_valid_summary(self):
        """Debería agregar summary y cambiar estado a SUMMARIZED."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        # Embed first
        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=768)
        chunk.embed(embedding)

        summary = ChunkSummary(
            content="First sentence. Second sentence. Third sentence.", sentence_count=3
        )

        # Act
        chunk.summarize(summary)

        # Assert
        assert chunk.summary == summary
        assert chunk.status == ChunkStatus.SUMMARIZED
        assert chunk.has_summary()
        assert chunk.can_complete()

    def test_summarize_emits_summarized_event(self):
        """Debería emitir ChunkSummarizedEvent."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=768)
        chunk.embed(embedding)
        chunk.mark_events_as_committed()

        summary = ChunkSummary(content="A. B. C. D.", sentence_count=4)

        # Act
        chunk.summarize(summary)

        # Assert
        events = chunk.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ChunkSummarizedEvent)
        assert events[0].sentence_count == 4

    def test_summarize_without_embedding_raises_error(self):
        """Debería lanzar error si el chunk no tiene embedding."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        summary = ChunkSummary(
            content="First sentence. Second sentence. Third sentence.", sentence_count=3
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Chunk must be embedded before summarizing"
        ):
            chunk.summarize(summary)

    def test_summarize_with_invalid_sentence_count_raises_error(self):
        """Debería lanzar error si summary no tiene 3-5 frases."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=768)
        chunk.embed(embedding)

        # Act & Assert - El Value Object ChunkSummary ya valida el sentence_count
        with pytest.raises(ValueError, match="Summary debe tener entre 3 y 5 frases"):
            summary = ChunkSummary(
                content="First sentence. Second sentence.", sentence_count=2
            )


class TestContentChunkComplete:
    """Tests para método mark_as_completed()."""

    def test_mark_as_completed_with_embedding_and_summary(self):
        """Debería marcar como completado si tiene embedding y summary."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        # Embed and summarize
        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=768)
        chunk.embed(embedding)

        summary = ChunkSummary(
            content="First sentence. Second sentence. Third sentence.", sentence_count=3
        )
        chunk.summarize(summary)

        # Act
        chunk.mark_as_completed()

        # Assert
        assert chunk.status == ChunkStatus.COMPLETED
        assert chunk.is_completed()

    def test_mark_as_completed_emits_completed_event(self):
        """Debería emitir ChunkCompletedEvent."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=768)
        chunk.embed(embedding)

        summary = ChunkSummary(
            content="First sentence. Second sentence. Third sentence.", sentence_count=3
        )
        chunk.summarize(summary)
        chunk.mark_events_as_committed()

        # Act
        chunk.mark_as_completed()

        # Assert
        events = chunk.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ChunkCompletedEvent)

    def test_mark_as_completed_without_embedding_raises_error(self):
        """Debería lanzar error si no tiene embedding."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Chunk must have embedding and summary to complete"
        ):
            chunk.mark_as_completed()

    def test_mark_as_completed_without_summary_raises_error(self):
        """Debería lanzar error si no tiene summary."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=768)
        chunk.embed(embedding)

        # Act & Assert
        with pytest.raises(
            ValueError, match="Chunk must have embedding and summary to complete"
        ):
            chunk.mark_as_completed()


class TestContentChunkFailed:
    """Tests para método mark_as_failed()."""

    def test_mark_as_failed_with_error_message(self):
        """Debería marcar como fallido con mensaje de error."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        # Act
        chunk.mark_as_failed("Embedding service unavailable")

        # Assert
        assert chunk.status == ChunkStatus.FAILED
        assert chunk.is_failed()

    def test_mark_as_failed_emits_failed_event(self):
        """Debería emitir ChunkFailedEvent."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )
        chunk.mark_events_as_committed()

        # Act
        chunk.mark_as_failed("Test error")

        # Assert
        events = chunk.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ChunkFailedEvent)
        assert events[0].error_message == "Test error"

    def test_mark_as_failed_with_empty_message_raises_error(self):
        """Debería lanzar error si error_message está vacío."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="error_message no puede estar vacío"):
            chunk.mark_as_failed("")


class TestContentChunkQueryMethods:
    """Tests para métodos de consulta."""

    def test_can_embed_returns_true_for_pending_chunk(self):
        """Debería retornar True si el chunk está PENDING."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        # Assert
        assert chunk.can_embed() is True

    def test_can_summarize_returns_true_for_embedded_chunk(self):
        """Debería retornar True si el chunk está EMBEDDED."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=768)
        chunk.embed(embedding)

        # Assert
        assert chunk.can_summarize() is True

    def test_can_complete_returns_true_for_summarized_chunk(self):
        """Debería retornar True si el chunk está SUMMARIZED."""
        # Arrange
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content="Test content",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        embedding = VectorEmbedding(vector=vector, model="test", dimension=768)
        chunk.embed(embedding)

        summary = ChunkSummary(
            content="First sentence. Second sentence. Third sentence.", sentence_count=3
        )
        chunk.summarize(summary)

        # Assert
        assert chunk.can_complete() is True

    def test_get_content_preview_truncates_long_content(self):
        """Debería truncar contenido largo."""
        # Arrange
        long_content = "A" * 200
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id="article-123",
            content=long_content,
            position=0,
            start_char=0,
            end_char=200,
            token_count=TokenCount(value=50),
            source_url="https://example.com/article",
        )

        # Act
        preview = chunk.get_content_preview(max_length=50)

        # Assert
        assert len(preview) == 50
        assert preview.endswith("...")
