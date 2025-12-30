"""Tests unitarios para ContextPack aggregate."""

from datetime import datetime, timezone

import numpy as np
import pytest

from src.ai.domain.value_objects import (
    ChunkId,
    ContextPackId,
    VectorEmbedding,
)
from src.chunking.domain.exceptions import (
    ChunkRelevanceOrderException,
    ContextPackFullException,
)
from src.rag.domain.aggregates import ContextPack


class TestContextPackCreation:
    """Tests para creación de ContextPack."""

    def test_create_with_defaults(self):
        """Debería crear ContextPack con valores por defecto."""
        # Arrange
        query = "Bitcoin ETF regulation"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")

        # Act
        pack = ContextPack.create(
            query=query,
            query_embedding=embedding,
        )

        # Assert
        assert pack.id is not None
        assert isinstance(pack.id, ContextPackId)
        assert pack.query == query
        assert pack.query_embedding == embedding
        assert pack.max_tokens == 4000  # Default
        assert pack.total_tokens == 0
        assert len(pack.chunk_ids) == 0
        assert len(pack.relevance_scores) == 0
        assert len(pack.sources) == 0
        assert isinstance(pack.created_at, datetime)

    def test_create_with_custom_max_tokens(self):
        """Debería crear ContextPack con max_tokens personalizado."""
        # Arrange
        query = "Bitcoin regulation"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")

        # Act
        pack = ContextPack.create(
            query=query,
            query_embedding=embedding,
            max_tokens=8000,
        )

        # Assert
        assert pack.max_tokens == 8000

    def test_create_with_custom_id(self):
        """Debería crear ContextPack con ID personalizado."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack_id = ContextPackId.generate()

        # Act
        pack = ContextPack.create(
            query=query,
            query_embedding=embedding,
            context_pack_id=pack_id,
        )

        # Assert
        assert pack.id == pack_id

    def test_create_with_empty_query_raises_error(self):
        """Debería lanzar error si query está vacío."""
        # Arrange
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ContextPack.create(
                query="",
                query_embedding=embedding,
            )

        assert "query no puede estar vacío" in str(exc_info.value)

    def test_create_with_invalid_max_tokens_raises_error(self):
        """Debería lanzar error si max_tokens es inválido."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ContextPack.create(
                query=query,
                query_embedding=embedding,
                max_tokens=0,
            )

        assert "max_tokens debe ser mayor a 0" in str(exc_info.value)


class TestContextPackAddChunk:
    """Tests para agregar chunks al ContextPack."""

    def test_add_chunk_successfully(self):
        """Debería agregar chunk correctamente."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding, max_tokens=1000)

        chunk_id = ChunkId.generate()

        # Act
        pack.add_chunk(
            chunk_id=chunk_id,
            token_count=500,
            relevance_score=0.95,
            source_url="https://example.com/article1",
        )

        # Assert
        assert len(pack.chunk_ids) == 1
        assert pack.chunk_ids[0] == chunk_id
        assert pack.total_tokens == 500
        assert len(pack.relevance_scores) == 1
        assert pack.relevance_scores[0] == 0.95
        assert len(pack.sources) == 1
        assert pack.sources[0] == "https://example.com/article1"

    def test_add_multiple_chunks_in_descending_order(self):
        """Debería agregar múltiples chunks en orden descendente."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding, max_tokens=2000)

        # Act
        pack.add_chunk(ChunkId.generate(), 300, 0.95, "https://example.com/1")
        pack.add_chunk(ChunkId.generate(), 300, 0.90, "https://example.com/2")
        pack.add_chunk(ChunkId.generate(), 300, 0.85, "https://example.com/3")

        # Assert
        assert len(pack.chunk_ids) == 3
        assert pack.total_tokens == 900
        assert pack.relevance_scores == [0.95, 0.90, 0.85]
        assert len(pack.sources) == 3

    def test_add_chunks_from_same_source(self):
        """Debería no duplicar source URL."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding, max_tokens=2000)

        # Act
        pack.add_chunk(ChunkId.generate(), 300, 0.95, "https://example.com/article")
        pack.add_chunk(ChunkId.generate(), 300, 0.90, "https://example.com/article")

        # Assert
        assert len(pack.chunk_ids) == 2
        assert len(pack.sources) == 1  # No duplicado
        assert pack.sources[0] == "https://example.com/article"

    def test_add_chunk_exceeding_max_tokens_raises_exception(self):
        """Debería lanzar ContextPackFullException si excede max_tokens."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding, max_tokens=1000)

        pack.add_chunk(ChunkId.generate(), 800, 0.95, "https://example.com/1")

        # Act & Assert
        with pytest.raises(ContextPackFullException) as exc_info:
            pack.add_chunk(ChunkId.generate(), 300, 0.90, "https://example.com/2")

        exception = exc_info.value
        assert exception.current_tokens == 800
        assert exception.max_tokens == 1000
        assert exception.attempted_tokens == 300
        assert "would exceed max_tokens" in str(exception)

    def test_add_chunk_with_higher_relevance_raises_exception(self):
        """Debería lanzar ChunkRelevanceOrderException si score no está en orden."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding, max_tokens=2000)

        pack.add_chunk(ChunkId.generate(), 300, 0.90, "https://example.com/1")

        # Act & Assert
        with pytest.raises(ChunkRelevanceOrderException) as exc_info:
            pack.add_chunk(ChunkId.generate(), 300, 0.95, "https://example.com/2")

        exception = exc_info.value
        assert exception.new_score == 0.95
        assert exception.last_score == 0.90
        assert "descending relevance order" in str(exception)

    def test_add_chunk_with_invalid_token_count_raises_error(self):
        """Debería lanzar ValueError si token_count es inválido."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            pack.add_chunk(
                ChunkId.generate(),
                token_count=0,
                relevance_score=0.9,
                source_url="https://example.com",
            )

        assert "token_count debe ser positivo" in str(exc_info.value)

    def test_add_chunk_with_invalid_relevance_score_raises_error(self):
        """Debería lanzar ValueError si relevance_score está fuera de rango."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding)

        # Act & Assert - Score > 1.0
        with pytest.raises(ValueError) as exc_info:
            pack.add_chunk(
                ChunkId.generate(),
                token_count=100,
                relevance_score=1.5,
                source_url="https://example.com",
            )

        assert "relevance_score debe estar en [0.0, 1.0]" in str(exc_info.value)

        # Act & Assert - Score < 0.0
        with pytest.raises(ValueError) as exc_info:
            pack.add_chunk(
                ChunkId.generate(),
                token_count=100,
                relevance_score=-0.1,
                source_url="https://example.com",
            )

        assert "relevance_score debe estar en [0.0, 1.0]" in str(exc_info.value)

    def test_add_chunk_with_invalid_source_url_raises_error(self):
        """Debería lanzar ValueError si source_url es inválida."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            pack.add_chunk(
                ChunkId.generate(),
                token_count=100,
                relevance_score=0.9,
                source_url="invalid-url",
            )

        assert "source_url inválida" in str(exc_info.value)


class TestContextPackQueries:
    """Tests para métodos de consulta del ContextPack."""

    def test_is_full_returns_false_when_not_full(self):
        """Debería retornar False cuando no está lleno."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding, max_tokens=1000)

        pack.add_chunk(ChunkId.generate(), 500, 0.9, "https://example.com")

        # Act & Assert
        assert pack.is_full() is False

    def test_is_full_returns_true_when_full(self):
        """Debería retornar True cuando está lleno."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding, max_tokens=1000)

        pack.add_chunk(ChunkId.generate(), 1000, 0.9, "https://example.com")

        # Act & Assert
        assert pack.is_full() is True

    def test_is_full_returns_true_when_at_limit(self):
        """Debería retornar True cuando alcanza exactamente el límite."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding, max_tokens=1000)

        pack.add_chunk(ChunkId.generate(), 600, 0.9, "https://example.com/1")
        pack.add_chunk(ChunkId.generate(), 400, 0.8, "https://example.com/2")

        # Act & Assert
        assert pack.total_tokens == 1000
        assert pack.is_full() is True

    def test_get_remaining_tokens(self):
        """Debería calcular tokens restantes correctamente."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding, max_tokens=1000)

        # Act & Assert - Vacío
        assert pack.get_remaining_tokens() == 1000

        # Act & Assert - Parcialmente lleno
        pack.add_chunk(ChunkId.generate(), 300, 0.9, "https://example.com")
        assert pack.get_remaining_tokens() == 700

        # Act & Assert - Lleno
        pack.add_chunk(ChunkId.generate(), 700, 0.8, "https://example.com")
        assert pack.get_remaining_tokens() == 0

    def test_get_chunk_count(self):
        """Debería contar chunks correctamente."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding)

        # Act & Assert - Vacío
        assert pack.get_chunk_count() == 0

        # Act & Assert - Con chunks
        pack.add_chunk(ChunkId.generate(), 100, 0.9, "https://example.com/1")
        assert pack.get_chunk_count() == 1

        pack.add_chunk(ChunkId.generate(), 100, 0.8, "https://example.com/2")
        assert pack.get_chunk_count() == 2

    def test_get_source_count(self):
        """Debería contar fuentes únicas correctamente."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding)

        # Act & Assert - Vacío
        assert pack.get_source_count() == 0

        # Act & Assert - Una fuente
        pack.add_chunk(ChunkId.generate(), 100, 0.9, "https://example.com/1")
        assert pack.get_source_count() == 1

        # Act & Assert - Misma fuente (no duplica)
        pack.add_chunk(ChunkId.generate(), 100, 0.8, "https://example.com/1")
        assert pack.get_source_count() == 1

        # Act & Assert - Nueva fuente
        pack.add_chunk(ChunkId.generate(), 100, 0.7, "https://example.com/2")
        assert pack.get_source_count() == 2

    def test_get_average_relevance_empty_pack(self):
        """Debería retornar 0.0 para pack vacío."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding)

        # Act & Assert
        assert pack.get_average_relevance() == 0.0

    def test_get_average_relevance_with_chunks(self):
        """Debería calcular promedio de relevancia correctamente."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding)

        # Act - Agregar en orden descendente
        pack.add_chunk(ChunkId.generate(), 100, 0.9, "https://example.com/1")
        pack.add_chunk(ChunkId.generate(), 100, 0.8, "https://example.com/2")
        pack.add_chunk(ChunkId.generate(), 100, 0.7, "https://example.com/3")

        # Assert
        expected_avg = (0.9 + 0.8 + 0.7) / 3
        assert pack.get_average_relevance() == pytest.approx(expected_avg)


class TestContextPackInvariants:
    """Tests para invariantes del ContextPack."""

    def test_chunk_ids_and_relevance_scores_same_length(self):
        """Debería mantener chunk_ids y relevance_scores con misma longitud."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding)

        # Act
        pack.add_chunk(ChunkId.generate(), 100, 0.9, "https://example.com/1")
        pack.add_chunk(ChunkId.generate(), 100, 0.8, "https://example.com/2")

        # Assert
        assert len(pack.chunk_ids) == len(pack.relevance_scores)

    def test_sources_no_duplicates(self):
        """Debería mantener sources sin duplicados."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding)

        # Act
        pack.add_chunk(ChunkId.generate(), 100, 0.9, "https://example.com/article")
        pack.add_chunk(ChunkId.generate(), 100, 0.8, "https://example.com/article")
        pack.add_chunk(ChunkId.generate(), 100, 0.7, "https://example.com/article")

        # Assert
        assert len(pack.sources) == 1
        assert pack.sources == ["https://example.com/article"]

    def test_total_tokens_never_exceeds_max_tokens(self):
        """Debería garantizar que total_tokens nunca exceda max_tokens."""
        # Arrange
        query = "Bitcoin"
        embedding = VectorEmbedding.from_list([0.1] * 768, "nomic-embed-text")
        pack = ContextPack.create(query, embedding, max_tokens=1000)

        # Act
        pack.add_chunk(ChunkId.generate(), 400, 0.9, "https://example.com/1")
        pack.add_chunk(ChunkId.generate(), 400, 0.8, "https://example.com/2")

        # Assert
        assert pack.total_tokens <= pack.max_tokens

        # Intentar exceder debería fallar
        with pytest.raises(ContextPackFullException):
            pack.add_chunk(ChunkId.generate(), 300, 0.7, "https://example.com/3")

        # Verificar que no se agregó
        assert pack.total_tokens == 800
        assert len(pack.chunk_ids) == 2
