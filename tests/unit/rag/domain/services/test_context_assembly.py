"""Unit tests para RAGContextAssemblyService."""

from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.interfaces.services import IVectorStore
from src.chunking.domain.value_objects import (
    ChunkId,
    ChunkSummary,
    TokenCount,
    VectorEmbedding,
)
from src.rag.domain.aggregates.context_pack import ContextPack
from src.rag.domain.services.context_assembly import RAGContextAssemblyService


class TestRAGContextAssemblyService:
    """Tests para RAGContextAssemblyService."""

    @pytest.fixture
    def mock_vector_store(self):
        """Mock para vector store."""
        return AsyncMock(spec=IVectorStore)

    @pytest.fixture
    def service(self, mock_vector_store):
        """Service con vector store mockeado."""
        return RAGContextAssemblyService(
            vector_store=mock_vector_store,
            max_tokens=4000,
        )

    @pytest.fixture
    def sample_query_embedding(self):
        """Sample query embedding."""
        vec = np.random.rand(768).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        return VectorEmbedding(vector=vec, model="test", dimension=768)

    @pytest.fixture
    def sample_chunks(self) -> List[ContentChunk]:
        """Sample chunks para testing."""
        chunks = []
        base_time = datetime.now(timezone.utc)

        for i in range(5):
            vec = np.random.rand(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)

            chunk = Mock(spec=ContentChunk)
            chunk.id = ChunkId.generate()
            chunk.content = f"Content of chunk {i}"
            chunk.embedding = VectorEmbedding(vector=vec, model="test", dimension=768)
            chunk.summary = ChunkSummary(
                content=f"Summary of chunk {i}. Second sentence. Third sentence.",
                sentence_count=3,
            )
            chunk.token_count = TokenCount(value=300 + i * 50, encoding="cl100k_base")
            chunk.source_url = f"https://example.com/article-{i % 2}"
            chunk.published_at = base_time - timedelta(days=i)
            chunk.article_id = f"article-{i % 2}"

            chunks.append(chunk)

        return chunks

    # Test initialization

    def test_init_with_valid_parameters(self, mock_vector_store):
        """Debería inicializar con parámetros válidos."""
        # Act
        service = RAGContextAssemblyService(
            vector_store=mock_vector_store,
            max_tokens=5000,
        )

        # Assert
        assert service._vector_store == mock_vector_store
        assert service._max_tokens == 5000

    def test_init_with_invalid_max_tokens_raises_error(self, mock_vector_store):
        """Debería lanzar error con max_tokens inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            RAGContextAssemblyService(
                vector_store=mock_vector_store,
                max_tokens=0,
            )

        assert "max_tokens debe ser > 0" in str(exc_info.value)

    # Test context pack assembly

    @pytest.mark.asyncio
    async def test_assemble_context_pack_creates_pack(
        self,
        service,
        mock_vector_store,
        sample_query_embedding,
        sample_chunks,
    ):
        """Debería crear context pack con chunks relevantes."""
        # Arrange
        search_results = [
            (chunk, 0.9 - i * 0.1) for i, chunk in enumerate(sample_chunks)
        ]
        mock_vector_store.search_similar.return_value = search_results

        # Act
        pack = await service.assemble_context_pack(
            query="Bitcoin regulation",
            query_embedding=sample_query_embedding,
            top_k=10,
        )

        # Assert
        assert isinstance(pack, ContextPack)
        assert pack.query == "Bitcoin regulation"
        assert pack.get_chunk_count() > 0
        assert pack.total_tokens <= service._max_tokens

    @pytest.mark.asyncio
    async def test_assemble_context_pack_calls_vector_store(
        self,
        service,
        mock_vector_store,
        sample_query_embedding,
    ):
        """Debería llamar al vector store con parámetros correctos."""
        # Arrange
        mock_vector_store.search_similar.return_value = []
        filters = {"date_from": datetime.now()}

        # Act
        await service.assemble_context_pack(
            query="Test query",
            query_embedding=sample_query_embedding,
            top_k=15,
            filters=filters,
        )

        # Assert
        mock_vector_store.search_similar.assert_called_once_with(
            query_embedding=sample_query_embedding,
            top_k=15,
            filters=filters,
        )

    @pytest.mark.asyncio
    async def test_assemble_context_pack_with_empty_query_raises_error(
        self,
        service,
        sample_query_embedding,
    ):
        """Debería lanzar error con query vacío."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await service.assemble_context_pack(
                query="",
                query_embedding=sample_query_embedding,
            )

        assert "query no puede estar vacío" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assemble_context_pack_with_invalid_top_k_raises_error(
        self,
        service,
        sample_query_embedding,
    ):
        """Debería lanzar error con top_k inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await service.assemble_context_pack(
                query="Test",
                query_embedding=sample_query_embedding,
                top_k=0,
            )

        assert "top_k debe ser > 0" in str(exc_info.value)

    # Property 9: Context Pack Token Limit
    # **Validates: Requirements 7.3, 7.4**

    @pytest.mark.asyncio
    async def test_property_context_pack_token_limit(
        self,
        service,
        mock_vector_store,
        sample_query_embedding,
        sample_chunks,
    ):
        """
        Property 9: Context Pack Token Limit.

        Para cualquier context pack ensamblado, el total de tokens
        no debe exceder el max_tokens configurado.
        """
        # Arrange
        search_results = [
            (chunk, 0.9 - i * 0.1) for i, chunk in enumerate(sample_chunks)
        ]
        mock_vector_store.search_similar.return_value = search_results

        # Act
        pack = await service.assemble_context_pack(
            query="Test query",
            query_embedding=sample_query_embedding,
            top_k=20,
        )

        # Assert
        assert (
            pack.total_tokens <= service._max_tokens
        ), f"Context pack excede límite: {pack.total_tokens} > {service._max_tokens}"

    # Property 10: Context Pack Ordering
    # **Validates: Requirements 7.3, 7.4**

    @pytest.mark.asyncio
    async def test_property_context_pack_ordering(
        self,
        service,
        mock_vector_store,
        sample_query_embedding,
        sample_chunks,
    ):
        """
        Property 10: Context Pack Ordering.

        Para cualquier context pack, los chunks deben estar ordenados
        primero por relevancia (descendente), luego por fecha (descendente).
        """
        # Arrange
        search_results = [
            (chunk, 0.9 - i * 0.1) for i, chunk in enumerate(sample_chunks)
        ]
        mock_vector_store.search_similar.return_value = search_results

        # Act
        pack = await service.assemble_context_pack(
            query="Test query",
            query_embedding=sample_query_embedding,
            top_k=20,
        )

        # Assert
        # Verificar que relevance_scores están en orden descendente
        scores = pack.relevance_scores
        for i in range(len(scores) - 1):
            assert (
                scores[i] >= scores[i + 1]
            ), f"Relevance scores no están ordenados: {scores[i]} < {scores[i + 1]}"

    # Test chunk ordering

    @pytest.mark.asyncio
    async def test_assemble_orders_by_relevance_first(
        self,
        service,
        mock_vector_store,
        sample_query_embedding,
        sample_chunks,
    ):
        """Debería ordenar por relevancia primero."""
        # Arrange
        # Crear chunks con diferentes scores pero misma fecha
        same_date = datetime.now(timezone.utc)
        for chunk in sample_chunks:
            chunk.published_at = same_date

        search_results = [
            (sample_chunks[0], 0.9),
            (sample_chunks[1], 0.8),
            (sample_chunks[2], 0.7),
        ]
        mock_vector_store.search_similar.return_value = search_results

        # Act
        pack = await service.assemble_context_pack(
            query="Test",
            query_embedding=sample_query_embedding,
        )

        # Assert
        scores = pack.relevance_scores
        assert scores == sorted(scores, reverse=True)

    # Test token limit enforcement

    @pytest.mark.asyncio
    async def test_assemble_stops_at_token_limit(
        self,
        mock_vector_store,
        sample_query_embedding,
    ):
        """Debería detenerse al alcanzar límite de tokens."""
        # Arrange
        service = RAGContextAssemblyService(
            vector_store=mock_vector_store,
            max_tokens=1000,  # Límite bajo
        )

        # Crear chunks grandes
        large_chunks = []
        for i in range(5):
            chunk = Mock(spec=ContentChunk)
            chunk.id = ChunkId.generate()
            chunk.token_count = TokenCount(value=400, encoding="cl100k_base")
            chunk.source_url = f"https://example.com/article-{i}"
            chunk.published_at = datetime.now(timezone.utc)
            large_chunks.append(chunk)

        search_results = [
            (chunk, 0.9 - i * 0.1) for i, chunk in enumerate(large_chunks)
        ]
        mock_vector_store.search_similar.return_value = search_results

        # Act
        pack = await service.assemble_context_pack(
            query="Test",
            query_embedding=sample_query_embedding,
        )

        # Assert
        # Solo deberían caber 2 chunks (400 + 400 = 800 < 1000)
        assert pack.get_chunk_count() <= 2
        assert pack.total_tokens <= 1000

    # Test source deduplication

    @pytest.mark.asyncio
    async def test_assemble_tracks_unique_sources(
        self,
        service,
        mock_vector_store,
        sample_query_embedding,
        sample_chunks,
    ):
        """Debería trackear fuentes únicas."""
        # Arrange
        search_results = [
            (chunk, 0.9 - i * 0.1) for i, chunk in enumerate(sample_chunks)
        ]
        mock_vector_store.search_similar.return_value = search_results

        # Act
        pack = await service.assemble_context_pack(
            query="Test",
            query_embedding=sample_query_embedding,
        )

        # Assert
        # sample_chunks tiene 2 fuentes únicas (article-0 y article-1)
        assert pack.get_source_count() <= 2
        assert len(set(pack.sources)) == pack.get_source_count()

    @pytest.mark.asyncio
    async def test_assemble_with_source_deduplication_limits_per_source(
        self,
        service,
        mock_vector_store,
        sample_query_embedding,
        sample_chunks,
    ):
        """Debería limitar chunks por fuente."""
        # Arrange
        search_results = [
            (chunk, 0.9 - i * 0.1) for i, chunk in enumerate(sample_chunks)
        ]
        mock_vector_store.search_similar.return_value = search_results

        # Act
        pack = await service.assemble_with_source_deduplication(
            query="Test",
            query_embedding=sample_query_embedding,
            max_chunks_per_source=2,
        )

        # Assert
        # Contar chunks por fuente
        chunks_by_source = {}
        for i, chunk_id in enumerate(pack.chunk_ids):
            source = (
                pack.sources[0]
                if i < 2
                else pack.sources[1] if len(pack.sources) > 1 else pack.sources[0]
            )
            chunks_by_source[source] = chunks_by_source.get(source, 0) + 1

        # Ninguna fuente debería tener más de 2 chunks
        for source, count in chunks_by_source.items():
            assert count <= 2

    @pytest.mark.asyncio
    async def test_assemble_with_source_deduplication_invalid_max_raises_error(
        self,
        service,
        sample_query_embedding,
    ):
        """Debería lanzar error con max_chunks_per_source inválido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await service.assemble_with_source_deduplication(
                query="Test",
                query_embedding=sample_query_embedding,
                max_chunks_per_source=0,
            )

        assert "max_chunks_per_source debe ser > 0" in str(exc_info.value)

    # Test context pack summary

    @pytest.mark.asyncio
    async def test_get_context_pack_summary_returns_statistics(
        self,
        service,
        mock_vector_store,
        sample_query_embedding,
        sample_chunks,
    ):
        """Debería retornar estadísticas del context pack."""
        # Arrange
        search_results = [(sample_chunks[0], 0.9), (sample_chunks[1], 0.8)]
        mock_vector_store.search_similar.return_value = search_results

        pack = await service.assemble_context_pack(
            query="Test query",
            query_embedding=sample_query_embedding,
        )

        # Act
        summary = await service.get_context_pack_summary(pack)

        # Assert
        assert "query" in summary
        assert "chunk_count" in summary
        assert "total_tokens" in summary
        assert "max_tokens" in summary
        assert "remaining_tokens" in summary
        assert "source_count" in summary
        assert "average_relevance" in summary
        assert "is_full" in summary
        assert "sources" in summary
        assert "created_at" in summary

        assert summary["query"] == "Test query"
        assert summary["chunk_count"] == pack.get_chunk_count()
        assert summary["total_tokens"] == pack.total_tokens
        assert summary["max_tokens"] == pack.max_tokens

    @pytest.mark.asyncio
    async def test_get_context_pack_summary_calculates_average_relevance(
        self,
        service,
        mock_vector_store,
        sample_query_embedding,
        sample_chunks,
    ):
        """Debería calcular relevancia promedio correctamente."""
        # Arrange
        search_results = [
            (sample_chunks[0], 0.9),
            (sample_chunks[1], 0.7),
            (sample_chunks[2], 0.5),
        ]
        mock_vector_store.search_similar.return_value = search_results

        pack = await service.assemble_context_pack(
            query="Test",
            query_embedding=sample_query_embedding,
        )

        # Act
        summary = await service.get_context_pack_summary(pack)

        # Assert
        expected_avg = (0.9 + 0.7 + 0.5) / 3
        assert abs(summary["average_relevance"] - expected_avg) < 0.01
