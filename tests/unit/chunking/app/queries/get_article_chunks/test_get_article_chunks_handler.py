"""Tests para GetArticleChunksHandler."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

pytestmark = pytest.mark.asyncio

from src.chunking.app.queries.get_article_chunks.dto import (
    ArticleChunkDTO,
    ArticleChunksResultDTO,
)
from src.chunking.app.queries.get_article_chunks.handler import (
    GetArticleChunksHandler,
)
from src.chunking.app.queries.get_article_chunks.query import GetArticleChunksQuery
from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.chunking.domain.value_objects.token_count import TokenCount
from src.chunking.domain.value_objects.vector_embedding import VectorEmbedding


class TestGetArticleChunksHandler:
    """Tests para GetArticleChunksHandler."""

    @pytest.fixture
    def mock_chunk_repository(self):
        """Mock para ContentChunk repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        logger = Mock()
        logger.bind.return_value = logger
        return logger

    @pytest.fixture
    def handler(self, mock_chunk_repository, mock_logger):
        """Handler con dependencias mockeadas."""
        return GetArticleChunksHandler(
            chunk_repository=mock_chunk_repository,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_chunks(self):
        """Chunks de ejemplo para tests."""
        chunks = []
        for i in range(3):
            chunk = ContentChunk(
                id=ChunkId.generate(),
                article_id=f"art-123",
                position=i,
                content=f"This is chunk {i} with some content...",
                start_char=i * 100,
                end_char=(i + 1) * 100,
                token_count=TokenCount(value=50, encoding="cl100k_base"),
                source_url="https://example.com/article",
            )
            # Agregar embedding
            vector = np.random.randn(768).astype(np.float32)
            vector = vector / np.linalg.norm(vector)  # Normalizar
            embedding = VectorEmbedding(vector=vector, model="test", dimension=768)
            chunk.embed(embedding)
            # Agregar summary
            chunk.summarize(
                ChunkSummary(
                    content=f"Summary of chunk {i}. Second sentence. Third sentence.",
                    sentence_count=3,
                )
            )
            # Marcar como completado
            chunk.mark_as_completed()
            chunks.append(chunk)
        return chunks

    async def test_handle_returns_all_chunks_without_pagination(
        self,
        handler,
        mock_chunk_repository,
        sample_chunks,
    ):
        """Debería retornar todos los chunks cuando no hay paginación."""
        # Arrange
        query = GetArticleChunksQuery(article_id="art-123")
        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_chunk_repository.count_by_article_id.return_value = 3

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, ArticleChunksResultDTO)
        assert result.article_id == "art-123"
        assert result.total_chunks == 3
        assert result.returned_chunks == 3
        assert len(result.chunks) == 3
        assert result.offset == 0
        assert result.has_more is False

        # Verificar llamadas
        mock_chunk_repository.find_by_article_id.assert_called_once_with(
            article_id="art-123",
            limit=None,
            offset=0,
        )
        mock_chunk_repository.count_by_article_id.assert_called_once_with(
            article_id="art-123"
        )

    async def test_handle_returns_chunks_with_pagination(
        self,
        handler,
        mock_chunk_repository,
        sample_chunks,
    ):
        """Debería retornar chunks paginados correctamente."""
        # Arrange
        query = GetArticleChunksQuery(
            article_id="art-123",
            limit=2,
            offset=0,
        )
        mock_chunk_repository.find_by_article_id.return_value = sample_chunks[:2]
        mock_chunk_repository.count_by_article_id.return_value = 3

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_chunks == 3
        assert result.returned_chunks == 2
        assert len(result.chunks) == 2
        assert result.offset == 0
        assert result.has_more is True  # Hay más chunks disponibles

        # Verificar llamadas
        mock_chunk_repository.find_by_article_id.assert_called_once_with(
            article_id="art-123",
            limit=2,
            offset=0,
        )

    async def test_handle_returns_empty_result_when_no_chunks(
        self,
        handler,
        mock_chunk_repository,
    ):
        """Debería retornar resultado vacío cuando no hay chunks."""
        # Arrange
        query = GetArticleChunksQuery(article_id="art-456")
        mock_chunk_repository.find_by_article_id.return_value = []
        mock_chunk_repository.count_by_article_id.return_value = 0

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_chunks == 0
        assert result.returned_chunks == 0
        assert len(result.chunks) == 0
        assert result.is_empty is True
        assert result.has_more is False

    async def test_handle_includes_summaries_by_default(
        self,
        handler,
        mock_chunk_repository,
        sample_chunks,
    ):
        """Debería incluir summaries por defecto."""
        # Arrange
        query = GetArticleChunksQuery(article_id="art-123")
        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_chunk_repository.count_by_article_id.return_value = 3

        # Act
        result = await handler.handle(query)

        # Assert
        for chunk_dto in result.chunks:
            assert chunk_dto.has_summary is True
            assert chunk_dto.summary is not None
            assert "Summary of chunk" in chunk_dto.summary

    async def test_handle_excludes_summaries_when_requested(
        self,
        handler,
        mock_chunk_repository,
        sample_chunks,
    ):
        """Debería excluir summaries cuando se solicita."""
        # Arrange
        query = GetArticleChunksQuery(
            article_id="art-123",
            include_summaries=False,
        )
        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_chunk_repository.count_by_article_id.return_value = 3

        # Act
        result = await handler.handle(query)

        # Assert
        for chunk_dto in result.chunks:
            assert chunk_dto.summary is None
            assert chunk_dto.has_summary is False

    async def test_handle_excludes_embeddings_by_default(
        self,
        handler,
        mock_chunk_repository,
        sample_chunks,
    ):
        """Debería excluir embeddings por defecto."""
        # Arrange
        query = GetArticleChunksQuery(article_id="art-123")
        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_chunk_repository.count_by_article_id.return_value = 3

        # Act
        result = await handler.handle(query)

        # Assert
        for chunk_dto in result.chunks:
            assert chunk_dto.embedding is None
            assert chunk_dto.has_embedding is False
            # Pero sí debe incluir la dimensión
            assert chunk_dto.embedding_dimension == 768

    async def test_handle_includes_embeddings_when_requested(
        self,
        handler,
        mock_chunk_repository,
        sample_chunks,
    ):
        """Debería incluir embeddings cuando se solicita."""
        # Arrange
        query = GetArticleChunksQuery(
            article_id="art-123",
            include_embeddings=True,
        )
        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_chunk_repository.count_by_article_id.return_value = 3

        # Act
        result = await handler.handle(query)

        # Assert
        for chunk_dto in result.chunks:
            assert chunk_dto.has_embedding is True
            assert chunk_dto.embedding is not None
            assert len(chunk_dto.embedding) == 768
            assert chunk_dto.embedding_dimension == 768

    async def test_handle_converts_chunks_to_dtos_correctly(
        self,
        handler,
        mock_chunk_repository,
        sample_chunks,
    ):
        """Debería convertir ContentChunk aggregates a DTOs correctamente."""
        # Arrange
        query = GetArticleChunksQuery(article_id="art-123")
        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_chunk_repository.count_by_article_id.return_value = 3

        # Act
        result = await handler.handle(query)

        # Assert
        for i, chunk_dto in enumerate(result.chunks):
            assert isinstance(chunk_dto, ArticleChunkDTO)
            assert chunk_dto.article_id == "art-123"
            assert chunk_dto.position == i
            assert f"This is chunk {i}" in chunk_dto.text
            assert chunk_dto.token_count == 50
            assert chunk_dto.is_completed is True

    async def test_handle_preserves_chunk_order_by_position(
        self,
        handler,
        mock_chunk_repository,
        sample_chunks,
    ):
        """Debería preservar el orden de chunks por posición."""
        # Arrange
        query = GetArticleChunksQuery(article_id="art-123")
        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_chunk_repository.count_by_article_id.return_value = 3

        # Act
        result = await handler.handle(query)

        # Assert
        positions = [chunk.position for chunk in result.chunks]
        assert positions == [0, 1, 2]  # Ordenados por posición

    async def test_handle_calculates_has_more_correctly_with_limit(
        self,
        handler,
        mock_chunk_repository,
        sample_chunks,
    ):
        """Debería calcular has_more correctamente con límite."""
        # Arrange - Primera página
        query = GetArticleChunksQuery(
            article_id="art-123",
            limit=2,
            offset=0,
        )
        mock_chunk_repository.find_by_article_id.return_value = sample_chunks[:2]
        mock_chunk_repository.count_by_article_id.return_value = 3

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.has_more is True  # offset=0 + returned=2 < total=3

        # Arrange - Segunda página (última)
        query = GetArticleChunksQuery(
            article_id="art-123",
            limit=2,
            offset=2,
        )
        mock_chunk_repository.find_by_article_id.return_value = [sample_chunks[2]]

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.has_more is False  # offset=2 + returned=1 >= total=3

    async def test_handle_logs_query_execution(
        self,
        handler,
        mock_chunk_repository,
        mock_logger,
        sample_chunks,
    ):
        """Debería loggear la ejecución de la query."""
        # Arrange
        query = GetArticleChunksQuery(article_id="art-123")
        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_chunk_repository.count_by_article_id.return_value = 3

        # Act
        await handler.handle(query)

        # Assert
        assert mock_logger.debug.call_count >= 2  # Inicio y fin

        # Verificar log de inicio
        first_call = mock_logger.debug.call_args_list[0]
        assert "Consultando chunks" in first_call[0][0]

        # Verificar log de fin
        last_call = mock_logger.debug.call_args_list[-1]
        assert "Chunks obtenidos" in last_call[0][0]

    async def test_chunk_dto_text_preview_truncates_long_text(self):
        """ChunkDTO.text_preview debería truncar texto largo."""
        # Arrange
        long_text = "a" * 150
        dto = ArticleChunkDTO(
            chunk_id="chunk-1",
            article_id="art-1",
            position=0,
            text=long_text,
            token_count=100,
            summary=None,
            embedding=None,
            embedding_dimension=None,
            is_completed=False,
        )

        # Act
        preview = dto.text_preview

        # Assert
        assert len(preview) == 103  # 100 chars + "..."
        assert preview.endswith("...")

    async def test_chunk_dto_text_preview_does_not_truncate_short_text(self):
        """ChunkDTO.text_preview no debería truncar texto corto."""
        # Arrange
        short_text = "Short text"
        dto = ArticleChunkDTO(
            chunk_id="chunk-1",
            article_id="art-1",
            position=0,
            text=short_text,
            token_count=10,
            summary=None,
            embedding=None,
            embedding_dimension=None,
            is_completed=False,
        )

        # Act
        preview = dto.text_preview

        # Assert
        assert preview == short_text
        assert not preview.endswith("...")

    async def test_result_dto_completion_percentage_calculates_correctly(self):
        """ResultDTO.completion_percentage debería calcular correctamente."""
        # Arrange
        chunks = [
            ArticleChunkDTO(
                chunk_id=f"chunk-{i}",
                article_id="art-1",
                position=i,
                text="text",
                token_count=50,
                summary=None,
                embedding=None,
                embedding_dimension=None,
                is_completed=(i < 2),  # Primeros 2 completados
            )
            for i in range(4)
        ]

        result = ArticleChunksResultDTO(
            article_id="art-1",
            chunks=chunks,
            total_chunks=4,
            returned_chunks=4,
            offset=0,
            has_more=False,
        )

        # Act
        percentage = result.completion_percentage

        # Assert
        assert percentage == 50.0  # 2 de 4 completados = 50%

    async def test_result_dto_is_empty_property(self):
        """ResultDTO.is_empty debería indicar si no hay chunks."""
        # Arrange - Con chunks
        result_with_chunks = ArticleChunksResultDTO(
            article_id="art-1",
            chunks=[Mock()],
            total_chunks=1,
            returned_chunks=1,
            offset=0,
            has_more=False,
        )

        # Arrange - Sin chunks
        result_empty = ArticleChunksResultDTO(
            article_id="art-1",
            chunks=[],
            total_chunks=0,
            returned_chunks=0,
            offset=0,
            has_more=False,
        )

        # Assert
        assert result_with_chunks.is_empty is False
        assert result_empty.is_empty is True
