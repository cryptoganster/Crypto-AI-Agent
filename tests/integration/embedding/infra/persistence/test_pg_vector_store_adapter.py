"""Integration tests for PgVectorStoreAdapter.

Feature: ai-content-processing-bounded-context
Tests: Chunk storage, retrieval, semantic search, ordering, top-k, deletion
Properties: Property 7 (Vector Search Ordering), Property 8 (Vector Search Top-K)
Validates: Requirements 4.1, 5.1, 5.3, 5.5
"""

from datetime import datetime, timedelta, timezone
from typing import List
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects import VectorEmbedding
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.chunking.domain.value_objects.token_count import TokenCount
from src.chunking.infra.persistence import (
    PgVectorStoreAdapter,
)
from src.shared.kernel.logger import ILogger


@pytest.mark.integration
@pytest.mark.skip(
    reason="Requires database setup - to be run manually with test database"
)
class TestPgVectorStoreAdapter:
    """Integration tests for PgVectorStoreAdapter."""

    @pytest.fixture
    def mock_logger(self) -> ILogger:
        """Create mock logger."""
        logger = Mock(spec=ILogger)
        logger.bind.return_value = logger
        logger.info = Mock()
        logger.debug = Mock()
        logger.error = Mock()
        logger.warning = Mock()
        return logger

    @pytest.fixture
    async def adapter(
        self,
        mock_logger: ILogger,
    ) -> PgVectorStoreAdapter:
        """Create PgVectorStoreAdapter with mock session."""
        # Note: This requires actual database session for real integration tests
        # For now, we skip these tests and they should be run manually
        mock_session = AsyncMock()
        return PgVectorStoreAdapter(mock_session, mock_logger)

    @pytest.fixture
    def sample_embedding(self) -> VectorEmbedding:
        """Create a sample normalized embedding."""
        # Create random vector and normalize
        vec = np.random.randn(768).astype(np.float32)
        vec = vec / np.linalg.norm(vec)

        return VectorEmbedding(
            vector=vec,
            model="nomic-embed-text",
            dimension=768,
        )

    @pytest.fixture
    def sample_chunk(self, sample_embedding: VectorEmbedding) -> ContentChunk:
        """Create a sample ContentChunk with embedding."""
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

    async def test_store_chunks_success(
        self,
        adapter: PgVectorStoreAdapter,
        sample_chunk: ContentChunk,
    ):
        """Debería almacenar chunks exitosamente."""
        # Arrange
        chunks = [sample_chunk]
        article_id = sample_chunk.article_id

        # Act
        chunk_ids = await adapter.store_chunks(chunks, article_id)

        # Assert
        assert len(chunk_ids) == 1
        assert chunk_ids[0] == str(sample_chunk.id.value)

    async def test_store_multiple_chunks(
        self,
        adapter: PgVectorStoreAdapter,
        sample_embedding: VectorEmbedding,
        db_session: AsyncSession,
    ):
        """Debería almacenar múltiples chunks en bulk."""
        # Arrange
        article_id = f"article-{uuid4()}"
        chunks = []

        for i in range(3):
            # Create unique embedding for each chunk
            vec = np.random.randn(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
            embedding = VectorEmbedding(
                vector=vec, model="nomic-embed-text", dimension=768
            )

            chunk = ContentChunk(
                id=ChunkId.generate(),
                article_id=article_id,
                content=f"Chunk {i} content...",
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                token_count=TokenCount(value=150, encoding="cl100k_base"),
                source_url="https://example.com/article",
                status=ChunkStatus.PENDING,
            )
            chunk.embed(embedding)

            summary = ChunkSummary(
                content=f"Summary {i}. Sentence 2. Sentence 3.",
                sentence_count=3,
            )
            chunk.summarize(summary)

            chunks.append(chunk)

        # Act
        chunk_ids = await adapter.store_chunks(chunks, article_id)
        await db_session.commit()

        # Assert
        assert len(chunk_ids) == 3
        assert all(isinstance(cid, str) for cid in chunk_ids)

    async def test_store_chunks_without_embedding_raises_error(
        self,
        adapter: PgVectorStoreAdapter,
    ):
        """Debería lanzar error si chunk no tiene embedding."""
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

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await adapter.store_chunks([chunk], chunk.article_id)

        assert "no tiene embedding" in str(exc_info.value)

    async def test_search_similar_returns_ordered_results(
        self,
        adapter: PgVectorStoreAdapter,
        sample_embedding: VectorEmbedding,
        db_session: AsyncSession,
    ):
        """Debería retornar resultados ordenados por similitud."""
        # Arrange - Store some chunks first
        article_id = f"article-{uuid4()}"
        chunks = []

        for i in range(5):
            vec = np.random.randn(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
            embedding = VectorEmbedding(
                vector=vec, model="nomic-embed-text", dimension=768
            )

            chunk = ContentChunk(
                id=ChunkId.generate(),
                article_id=article_id,
                content=f"Chunk {i} content...",
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                token_count=TokenCount(value=150, encoding="cl100k_base"),
                source_url="https://example.com/article",
                status=ChunkStatus.PENDING,
            )
            chunk.embed(embedding)

            summary = ChunkSummary(
                content=f"Summary {i}. Sentence 2. Sentence 3.",
                sentence_count=3,
            )
            chunk.summarize(summary)

            chunks.append(chunk)

        await adapter.store_chunks(chunks, article_id)
        await db_session.commit()

        # Act - Search with query embedding
        query_vec = np.random.randn(768).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        results = await adapter.search_similar(query_embedding, top_k=3)

        # Assert
        assert len(results) <= 3

        # Verify ordering (scores should be descending)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i][1] >= results[i + 1][1]

        # Verify all scores are in valid range
        for chunk, score in results:
            assert 0.0 <= score <= 1.0
            assert isinstance(chunk, ContentChunk)

    async def test_search_similar_with_filters(
        self,
        adapter: PgVectorStoreAdapter,
        sample_embedding: VectorEmbedding,
        db_session: AsyncSession,
    ):
        """Debería aplicar filtros correctamente."""
        # Arrange - Store chunks with different article_ids
        article_id_1 = f"article-{uuid4()}"
        article_id_2 = f"article-{uuid4()}"

        # Store chunks for article 1
        chunk1 = ContentChunk(
            id=ChunkId.generate(),
            article_id=article_id_1,
            content="Chunk 1 content...",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=150, encoding="cl100k_base"),
            source_url="https://example.com/article1",
            status=ChunkStatus.PENDING,
        )

        vec1 = np.random.randn(768).astype(np.float32)
        vec1 = vec1 / np.linalg.norm(vec1)
        embedding1 = VectorEmbedding(
            vector=vec1, model="nomic-embed-text", dimension=768
        )
        chunk1.embed(embedding1)

        summary1 = ChunkSummary(
            content="Summary 1. Sentence 2. Sentence 3.", sentence_count=3
        )
        chunk1.summarize(summary1)

        # Store chunks for article 2
        chunk2 = ContentChunk(
            id=ChunkId.generate(),
            article_id=article_id_2,
            content="Chunk 2 content...",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=150, encoding="cl100k_base"),
            source_url="https://example.com/article2",
            status=ChunkStatus.PENDING,
        )

        vec2 = np.random.randn(768).astype(np.float32)
        vec2 = vec2 / np.linalg.norm(vec2)
        embedding2 = VectorEmbedding(
            vector=vec2, model="nomic-embed-text", dimension=768
        )
        chunk2.embed(embedding2)

        summary2 = ChunkSummary(
            content="Summary 2. Sentence 2. Sentence 3.", sentence_count=3
        )
        chunk2.summarize(summary2)

        await adapter.store_chunks([chunk1], article_id_1)
        await adapter.store_chunks([chunk2], article_id_2)
        await db_session.commit()

        # Act - Search with filter for article_id_1 only
        query_vec = np.random.randn(768).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        results = await adapter.search_similar(
            query_embedding, top_k=10, filters={"article_ids": [article_id_1]}
        )

        # Assert - Should only return chunks from article_id_1
        assert len(results) >= 1
        for chunk, score in results:
            assert chunk.article_id == article_id_1

    async def test_delete_chunks_removes_all_chunks(
        self,
        adapter: PgVectorStoreAdapter,
        sample_chunk: ContentChunk,
        db_session: AsyncSession,
    ):
        """Debería eliminar todos los chunks de un artículo."""
        # Arrange - Store chunk first
        article_id = sample_chunk.article_id
        await adapter.store_chunks([sample_chunk], article_id)
        await db_session.commit()

        # Act - Delete chunks
        await adapter.delete_chunks(article_id)
        await db_session.commit()

        # Assert - Search should return no results
        query_vec = np.random.randn(768).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        results = await adapter.search_similar(
            query_embedding, top_k=10, filters={"article_ids": [article_id]}
        )

        assert len(results) == 0

    async def test_delete_chunks_with_empty_article_id_raises_error(
        self,
        adapter: PgVectorStoreAdapter,
    ):
        """Debería lanzar error si article_id está vacío."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await adapter.delete_chunks("")

        assert "article_id no puede estar vacío" in str(exc_info.value)

    async def test_get_tldrs_returns_empty_list(
        self,
        adapter: PgVectorStoreAdapter,
    ):
        """Debería retornar lista vacía (implementación pendiente)."""
        # Act
        tldrs = await adapter.get_tldrs(["article-123", "article-456"])

        # Assert
        assert isinstance(tldrs, list)
        assert len(tldrs) == 0

    async def test_search_similar_with_invalid_top_k_raises_error(
        self,
        adapter: PgVectorStoreAdapter,
        sample_embedding: VectorEmbedding,
    ):
        """Debería lanzar error si top_k <= 0."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await adapter.search_similar(sample_embedding, top_k=0)

        assert "top_k debe ser > 0" in str(exc_info.value)

    async def test_search_similar_with_wrong_dimension_raises_error(
        self,
        adapter: PgVectorStoreAdapter,
    ):
        """Debería lanzar error si embedding tiene dimensión incorrecta."""
        # Arrange - Create embedding with wrong dimension
        vec = np.random.randn(512).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        wrong_embedding = VectorEmbedding(
            vector=vec,
            model="test",
            dimension=512,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await adapter.search_similar(wrong_embedding, top_k=5)

        assert "768 dimensiones" in str(exc_info.value)

    # ========================================================================
    # COMPREHENSIVE INTEGRATION TESTS
    # ========================================================================

    async def test_chunk_storage_and_retrieval_roundtrip(
        self,
        adapter: PgVectorStoreAdapter,
        sample_embedding: VectorEmbedding,
        db_session: AsyncSession,
    ):
        """
        Debería almacenar y recuperar chunks correctamente (roundtrip).

        Tests: Chunk storage and retrieval
        Validates: Requirements 4.1
        """
        # Arrange - Create chunk with all fields
        article_id = f"article-{uuid4()}"
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id=article_id,
            content="Bitcoin alcanzó $50,000 en el mercado cripto. "
            "Los inversores están optimistas sobre el futuro.",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=150, encoding="cl100k_base"),
            source_url="https://example.com/article",
            status=ChunkStatus.PENDING,
        )

        # Add embedding
        vec = np.random.randn(768).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        embedding = VectorEmbedding(vector=vec, model="nomic-embed-text", dimension=768)
        chunk.embed(embedding)

        # Add summary
        summary = ChunkSummary(
            content="Bitcoin alcanzó $50,000. Los inversores están optimistas. "
            "El mercado reaccionó positivamente.",
            sentence_count=3,
        )
        chunk.summarize(summary)

        # Act - Store chunk
        chunk_ids = await adapter.store_chunks([chunk], article_id)
        await db_session.commit()

        # Assert - Storage successful
        assert len(chunk_ids) == 1
        assert chunk_ids[0] == str(chunk.id.value)

        # Act - Retrieve via search
        query_vec = vec.copy()  # Use same vector for exact match
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        results = await adapter.search_similar(query_embedding, top_k=1)

        # Assert - Retrieved chunk matches stored chunk
        assert len(results) == 1
        retrieved_chunk, similarity = results[0]

        assert retrieved_chunk.article_id == chunk.article_id
        assert retrieved_chunk.content == chunk.content
        assert retrieved_chunk.position == chunk.position
        assert retrieved_chunk.token_count.value == chunk.token_count.value
        assert retrieved_chunk.source_url == chunk.source_url
        assert retrieved_chunk.summary.content == chunk.summary.content
        assert similarity > 0.99  # Should be very similar (same vector)

    async def test_semantic_search_accuracy_with_similar_content(
        self,
        adapter: PgVectorStoreAdapter,
        db_session: AsyncSession,
    ):
        """
        Debería encontrar chunks semánticamente similares.

        Tests: Semantic search accuracy
        Validates: Requirements 5.1
        """
        # Arrange - Create chunks with related content
        article_id = f"article-{uuid4()}"

        # Chunk 1: About Bitcoin price
        chunk1 = self._create_chunk_with_content(
            article_id,
            "Bitcoin alcanzó $50,000 en el mercado cripto.",
            position=0,
        )

        # Chunk 2: About Ethereum (different topic)
        chunk2 = self._create_chunk_with_content(
            article_id,
            "Ethereum implementó nueva actualización de red.",
            position=1,
        )

        # Chunk 3: Also about Bitcoin price (similar to chunk1)
        chunk3 = self._create_chunk_with_content(
            article_id,
            "El precio de Bitcoin superó los $50,000 dólares.",
            position=2,
        )

        # Store all chunks
        await adapter.store_chunks([chunk1, chunk2, chunk3], article_id)
        await db_session.commit()

        # Act - Search with query similar to chunk1
        query_vec = chunk1.embedding.vector.copy()
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        results = await adapter.search_similar(query_embedding, top_k=3)

        # Assert - Chunk1 should be most similar
        assert len(results) == 3
        assert results[0][0].position == 0  # chunk1 should be first
        assert results[0][1] > 0.99  # Very high similarity (same vector)

    async def test_search_ordering_by_similarity_descending(
        self,
        adapter: PgVectorStoreAdapter,
        db_session: AsyncSession,
    ):
        """
        Debería ordenar resultados por similitud descendente.

        Tests: Search ordering
        Validates: Requirements 5.5
        Property 7: Vector Search Ordering
        """
        # Arrange - Create chunks with varying similarity to query
        article_id = f"article-{uuid4()}"
        chunks = []

        # Create 10 chunks with random embeddings
        for i in range(10):
            chunk = self._create_chunk_with_content(
                article_id,
                f"Chunk {i} content about various topics.",
                position=i,
            )
            chunks.append(chunk)

        await adapter.store_chunks(chunks, article_id)
        await db_session.commit()

        # Act - Search with random query
        query_vec = np.random.randn(768).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        results = await adapter.search_similar(query_embedding, top_k=10)

        # Assert - Results ordered by similarity descending
        assert len(results) == 10

        # **Property 7: Vector Search Ordering**
        # For any semantic search result, chunks should be ordered by
        # similarity score in descending order
        for i in range(len(results) - 1):
            current_score = results[i][1]
            next_score = results[i + 1][1]
            assert current_score >= next_score, (
                f"Results not ordered: position {i} has score {current_score}, "
                f"position {i+1} has score {next_score}"
            )

        # All scores should be in valid range [0, 1]
        for chunk, score in results:
            assert 0.0 <= score <= 1.0

    async def test_search_top_k_returns_exactly_k_results(
        self,
        adapter: PgVectorStoreAdapter,
        db_session: AsyncSession,
    ):
        """
        Debería retornar exactamente k resultados (o menos si no hay suficientes).

        Tests: Top-k limiting
        Validates: Requirements 5.3
        Property 8: Vector Search Top-K
        """
        # Arrange - Create 20 chunks
        article_id = f"article-{uuid4()}"
        chunks = []

        for i in range(20):
            chunk = self._create_chunk_with_content(
                article_id,
                f"Chunk {i} content.",
                position=i,
            )
            chunks.append(chunk)

        await adapter.store_chunks(chunks, article_id)
        await db_session.commit()

        # Create query embedding
        query_vec = np.random.randn(768).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        # **Property 8: Vector Search Top-K**
        # For any semantic search with parameter k, the result should contain
        # exactly k chunks (or fewer if not enough exist)

        # Test various k values
        test_cases = [1, 5, 10, 15, 20, 25]

        for k in test_cases:
            # Act
            results = await adapter.search_similar(query_embedding, top_k=k)

            # Assert
            expected_count = min(k, 20)  # Can't return more than exist
            assert len(results) == expected_count, (
                f"Expected {expected_count} results for top_k={k}, "
                f"got {len(results)}"
            )

    async def test_search_with_date_filters(
        self,
        adapter: PgVectorStoreAdapter,
        db_session: AsyncSession,
    ):
        """
        Debería filtrar chunks por rango de fechas.

        Tests: Search with filters
        Validates: Requirements 5.2
        """
        # Arrange - Create chunks with different dates
        article_id = f"article-{uuid4()}"

        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        last_week = now - timedelta(days=7)

        # Chunk from last week
        chunk1 = self._create_chunk_with_content(
            article_id,
            "Old content from last week.",
            position=0,
        )
        chunk1._published_at = last_week

        # Chunk from yesterday
        chunk2 = self._create_chunk_with_content(
            article_id,
            "Recent content from yesterday.",
            position=1,
        )
        chunk2._published_at = yesterday

        # Chunk from today
        chunk3 = self._create_chunk_with_content(
            article_id,
            "Fresh content from today.",
            position=2,
        )
        chunk3._published_at = now

        await adapter.store_chunks([chunk1, chunk2, chunk3], article_id)
        await db_session.commit()

        # Act - Search with date filter (only last 2 days)
        query_vec = np.random.randn(768).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        two_days_ago = now - timedelta(days=2)
        results = await adapter.search_similar(
            query_embedding, top_k=10, filters={"date_from": two_days_ago}
        )

        # Assert - Should only return chunk2 and chunk3
        assert len(results) == 2
        positions = {chunk.position for chunk, _ in results}
        assert 1 in positions  # chunk2
        assert 2 in positions  # chunk3
        assert 0 not in positions  # chunk1 excluded

    async def test_search_with_source_url_filters(
        self,
        adapter: PgVectorStoreAdapter,
        db_session: AsyncSession,
    ):
        """
        Debería filtrar chunks por URLs de fuentes.

        Tests: Search with filters
        Validates: Requirements 5.2
        """
        # Arrange - Create chunks from different sources
        article_id = f"article-{uuid4()}"

        chunk1 = self._create_chunk_with_content(
            article_id,
            "Content from source A.",
            position=0,
        )
        chunk1._source_url = "https://source-a.com/article"

        chunk2 = self._create_chunk_with_content(
            article_id,
            "Content from source B.",
            position=1,
        )
        chunk2._source_url = "https://source-b.com/article"

        chunk3 = self._create_chunk_with_content(
            article_id,
            "More content from source A.",
            position=2,
        )
        chunk3._source_url = "https://source-a.com/article"

        await adapter.store_chunks([chunk1, chunk2, chunk3], article_id)
        await db_session.commit()

        # Act - Search filtering by source A only
        query_vec = np.random.randn(768).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        results = await adapter.search_similar(
            query_embedding,
            top_k=10,
            filters={"source_urls": ["https://source-a.com/article"]},
        )

        # Assert - Should only return chunks from source A
        assert len(results) == 2
        for chunk, _ in results:
            assert chunk.source_url == "https://source-a.com/article"

    async def test_chunk_deletion_removes_all_article_chunks(
        self,
        adapter: PgVectorStoreAdapter,
        db_session: AsyncSession,
    ):
        """
        Debería eliminar todos los chunks de un artículo.

        Tests: Chunk deletion
        Validates: Requirements 4.1
        """
        # Arrange - Create multiple chunks for same article
        article_id = f"article-{uuid4()}"
        chunks = []

        for i in range(5):
            chunk = self._create_chunk_with_content(
                article_id,
                f"Chunk {i} content.",
                position=i,
            )
            chunks.append(chunk)

        await adapter.store_chunks(chunks, article_id)
        await db_session.commit()

        # Verify chunks exist
        query_vec = np.random.randn(768).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        results_before = await adapter.search_similar(
            query_embedding, top_k=10, filters={"article_ids": [article_id]}
        )
        assert len(results_before) == 5

        # Act - Delete all chunks
        await adapter.delete_chunks(article_id)
        await db_session.commit()

        # Assert - No chunks should remain
        results_after = await adapter.search_similar(
            query_embedding, top_k=10, filters={"article_ids": [article_id]}
        )
        assert len(results_after) == 0

    async def test_tldr_retrieval_returns_empty_for_now(
        self,
        adapter: PgVectorStoreAdapter,
    ):
        """
        Debería retornar lista vacía para TLDRs (implementación pendiente).

        Tests: TLDR retrieval
        Validates: Requirements 5.4
        """
        # Act
        tldrs = await adapter.get_tldrs(["article-123", "article-456"])

        # Assert - Currently returns empty list
        assert isinstance(tldrs, list)
        assert len(tldrs) == 0

    # ========================================================================
    # PROPERTY-BASED TESTS
    # ========================================================================

    @given(
        top_k=st.integers(min_value=1, max_value=100),
        num_chunks=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=10, deadline=None)
    async def test_property_search_top_k_never_exceeds_k(
        self,
        adapter: PgVectorStoreAdapter,
        db_session: AsyncSession,
        top_k: int,
        num_chunks: int,
    ):
        """
        **Property 8: Vector Search Top-K**

        For any semantic search with parameter k, the result should contain
        exactly k chunks (or fewer if not enough exist).

        Validates: Requirements 5.3
        """
        # Arrange - Create num_chunks chunks
        article_id = f"article-{uuid4()}"
        chunks = []

        for i in range(num_chunks):
            chunk = self._create_chunk_with_content(
                article_id,
                f"Chunk {i} content.",
                position=i,
            )
            chunks.append(chunk)

        await adapter.store_chunks(chunks, article_id)
        await db_session.commit()

        # Act - Search with top_k
        query_vec = np.random.randn(768).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        results = await adapter.search_similar(query_embedding, top_k=top_k)

        # Assert - Property 8
        expected_count = min(top_k, num_chunks)
        assert len(results) == expected_count
        assert len(results) <= top_k

    @given(
        num_chunks=st.integers(min_value=2, max_value=20),
    )
    @settings(max_examples=10, deadline=None)
    async def test_property_search_ordering_always_descending(
        self,
        adapter: PgVectorStoreAdapter,
        db_session: AsyncSession,
        num_chunks: int,
    ):
        """
        **Property 7: Vector Search Ordering**

        For any semantic search result, the chunks should be ordered by
        similarity score in descending order.

        Validates: Requirements 5.5
        """
        # Arrange - Create chunks
        article_id = f"article-{uuid4()}"
        chunks = []

        for i in range(num_chunks):
            chunk = self._create_chunk_with_content(
                article_id,
                f"Chunk {i} content.",
                position=i,
            )
            chunks.append(chunk)

        await adapter.store_chunks(chunks, article_id)
        await db_session.commit()

        # Act - Search
        query_vec = np.random.randn(768).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        query_embedding = VectorEmbedding(
            vector=query_vec,
            model="nomic-embed-text",
            dimension=768,
        )

        results = await adapter.search_similar(query_embedding, top_k=num_chunks)

        # Assert - Property 7: Descending order
        for i in range(len(results) - 1):
            assert results[i][1] >= results[i + 1][1]

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _create_chunk_with_content(
        self,
        article_id: str,
        content: str,
        position: int,
    ) -> ContentChunk:
        """Helper to create a chunk with random embedding."""
        chunk = ContentChunk(
            id=ChunkId.generate(),
            article_id=article_id,
            content=content,
            position=position,
            start_char=position * 100,
            end_char=(position + 1) * 100,
            token_count=TokenCount(value=150, encoding="cl100k_base"),
            source_url="https://example.com/article",
            status=ChunkStatus.PENDING,
        )

        # Add random normalized embedding
        vec = np.random.randn(768).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        embedding = VectorEmbedding(
            vector=vec,
            model="nomic-embed-text",
            dimension=768,
        )
        chunk.embed(embedding)

        # Add summary
        summary = ChunkSummary(
            content=f"Summary of {content}. Second sentence. Third sentence.",
            sentence_count=3,
        )
        chunk.summarize(summary)

        return chunk
