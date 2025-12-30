"""Tests para GenerateChunkEmbeddingsHandler."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from src.chunking.app.commands.generate_chunk_embeddings.command import (
    GenerateChunkEmbeddingsCommand,
)
from src.chunking.app.commands.generate_chunk_embeddings.handler import (
    GenerateChunkEmbeddingsHandler,
)
from src.chunking.app.commands.generate_chunk_embeddings.result import (
    GenerateChunkEmbeddingsResult,
)
from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.token_count import TokenCount
from src.chunking.domain.value_objects.vector_embedding import VectorEmbedding
from src.shared.config.ai_processing_config import AIProcessingConfig


def create_test_embedding(
    dimension: int = 768, model: str = "nomic-embed-text"
) -> VectorEmbedding:
    """Helper para crear embeddings de test."""
    vec = np.array([0.1] * dimension, dtype=np.float32)
    vec = vec / np.linalg.norm(vec)  # Normalizar
    return VectorEmbedding(
        vector=vec,
        model=model,
        dimension=dimension,
    )


class TestGenerateChunkEmbeddingsHandler:
    """Tests para GenerateChunkEmbeddingsHandler."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock para IEmbeddingService."""
        service = AsyncMock()
        # Por defecto retorna embeddings válidos
        service.embed_batch.return_value = [create_test_embedding()]
        return service

    @pytest.fixture
    def mock_chunk_read_repository(self):
        """Mock para IContentChunkReadRepository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def mock_chunk_write_repository(self):
        """Mock para IContentChunkWriteRepository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def ai_config(self):
        """Configuración AI para tests."""
        return AIProcessingConfig(
            summary_batch_size=5,
            max_retries=3,
        )

    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        logger = Mock()
        logger.bind.return_value = logger
        return logger

    @pytest.fixture
    def handler(
        self,
        mock_embedding_service,
        mock_chunk_read_repository,
        mock_chunk_write_repository,
        ai_config,
        mock_logger,
    ):
        """Handler con dependencias mockeadas."""
        return GenerateChunkEmbeddingsHandler(
            embedding_service=mock_embedding_service,
            chunk_read_repository=mock_chunk_read_repository,
            chunk_write_repository=mock_chunk_write_repository,
            config=ai_config,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_chunk(self):
        """Crea un chunk de ejemplo en estado PENDING."""
        return ContentChunk(
            id=ChunkId.generate(),
            article_id="art-123",
            content="Bitcoin alcanzó $50,000 en el mercado...",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            status=ChunkStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_genera_embeddings_en_batches(
        self,
        handler,
        mock_chunk_read_repository,
        mock_chunk_write_repository,
        mock_embedding_service,
        sample_chunk,
    ):
        """Debería generar embeddings en batches."""
        # Arrange
        chunks = [sample_chunk]
        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        # Mock embeddings
        embeddings = [create_test_embedding()]
        mock_embedding_service.embed_batch.return_value = embeddings

        command = GenerateChunkEmbeddingsCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.chunks_processed == 1
        mock_embedding_service.embed_batch.assert_called_once()
        mock_chunk_write_repository.save.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_usa_batch_size_de_configuracion(
        self,
        handler,
        mock_chunk_read_repository,
        mock_embedding_service,
        ai_config,
    ):
        """Debería usar batch_size de configuración."""
        # Arrange - Crear más chunks que el batch_size
        chunks = []
        for i in range(50):  # Más que batch_size=32
            chunk = ContentChunk(
                id=ChunkId.generate(),
                article_id="art-123",
                content=f"Chunk {i} content...",
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                token_count=TokenCount(value=50, encoding="cl100k_base"),
                source_url="https://example.com/article",
                status=ChunkStatus.PENDING,
            )
            chunks.append(chunk)

        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        # Mock embeddings - retornar embeddings para cada llamada
        def create_embeddings(texts):
            return [create_test_embedding() for _ in texts]

        mock_embedding_service.embed_batch.side_effect = create_embeddings

        command = GenerateChunkEmbeddingsCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.chunks_processed == 50

        # Verificar que se llamó embed_batch múltiples veces
        # 50 chunks / 32 batch_size = 2 batches (32 + 18)
        assert mock_embedding_service.embed_batch.call_count == 2

        # Verificar tamaños de batches
        first_call_args = mock_embedding_service.embed_batch.call_args_list[0][0][0]
        second_call_args = mock_embedding_service.embed_batch.call_args_list[1][0][0]

        assert len(first_call_args) == 32  # Primer batch completo
        assert len(second_call_args) == 18  # Segundo batch parcial

    @pytest.mark.asyncio
    async def test_llama_chunk_embed_correctamente(
        self,
        handler,
        mock_chunk_read_repository,
        mock_embedding_service,
        sample_chunk,
    ):
        """Debería llamar chunk.embed() correctamente."""
        # Arrange
        chunks = [sample_chunk]
        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        embedding = create_test_embedding()
        mock_embedding_service.embed_batch.return_value = [embedding]

        command = GenerateChunkEmbeddingsCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert sample_chunk.embedding is not None
        assert sample_chunk.status == ChunkStatus.EMBEDDED

    @pytest.mark.asyncio
    async def test_content_chunk_emite_chunk_embedded_event(
        self,
        handler,
        mock_chunk_read_repository,
        mock_embedding_service,
        sample_chunk,
    ):
        """Debería verificar que ContentChunk emite ChunkEmbeddedEvent."""
        # Arrange
        chunks = [sample_chunk]
        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        embedding = create_test_embedding()
        mock_embedding_service.embed_batch.return_value = [embedding]

        command = GenerateChunkEmbeddingsCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que el chunk tiene eventos pendientes
        events = sample_chunk.get_uncommitted_events()
        assert len(events) > 0

        # Verificar que hay un ChunkEmbeddedEvent
        from src.chunking.domain.events import ChunkEmbeddedEvent

        embedded_events = [e for e in events if isinstance(e, ChunkEmbeddedEvent)]
        assert len(embedded_events) == 1

        event = embedded_events[0]
        assert event.chunk_id == str(sample_chunk.id)
        assert event.article_id == "art-123"
        assert event.embedding_model == "nomic-embed-text"
        assert event.embedding_dimension == 768

    @pytest.mark.asyncio
    async def test_persiste_chunks_actualizados(
        self,
        handler,
        mock_chunk_read_repository,
        mock_chunk_write_repository,
        mock_embedding_service,
        sample_chunk,
    ):
        """Debería persistir chunks actualizados."""
        # Arrange
        chunks = [sample_chunk]
        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        embedding = create_test_embedding()
        mock_embedding_service.embed_batch.return_value = [embedding]

        command = GenerateChunkEmbeddingsCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        mock_chunk_write_repository.save.assert_called_once_with(sample_chunk)

    @pytest.mark.asyncio
    async def test_no_procesa_chunks_con_embedding_existente(
        self,
        handler,
        mock_chunk_read_repository,
        mock_embedding_service,
    ):
        """No debería procesar chunks que ya tienen embedding."""
        # Arrange - Chunk con embedding existente
        chunk_with_embedding = ContentChunk(
            id=ChunkId.generate(),
            article_id="art-123",
            content="Content...",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            embedding=create_test_embedding(),
            status=ChunkStatus.EMBEDDED,
        )

        mock_chunk_read_repository.find_by_article_id.return_value = [
            chunk_with_embedding
        ]

        command = GenerateChunkEmbeddingsCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.chunks_processed == 0
        mock_embedding_service.embed_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_maneja_error_en_chunk_individual(
        self,
        handler,
        mock_chunk_read_repository,
        mock_embedding_service,
        mock_logger,
    ):
        """Debería manejar error en chunk individual y continuar."""
        # Arrange - Crear chunks, uno con embedding inválido
        chunk1 = ContentChunk(
            id=ChunkId.generate(),
            article_id="art-123",
            content="Chunk 1",
            position=0,
            start_char=0,
            end_char=100,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            status=ChunkStatus.PENDING,
        )

        chunk2 = ContentChunk(
            id=ChunkId.generate(),
            article_id="art-123",
            content="Chunk 2",
            position=1,
            start_char=100,
            end_char=200,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            status=ChunkStatus.PENDING,
        )

        mock_chunk_read_repository.find_by_article_id.return_value = [chunk1, chunk2]

        # Mock embeddings - uno inválido (dimensión incorrecta)
        invalid_embedding = create_test_embedding(dimension=512, model="wrong-model")
        valid_embedding = create_test_embedding()
        mock_embedding_service.embed_batch.return_value = [
            invalid_embedding,
            valid_embedding,
        ]

        command = GenerateChunkEmbeddingsCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.chunks_processed == 1  # Solo chunk2 procesado

        # Verificar que se loggeó el warning
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_retorna_error_cuando_no_hay_chunks(
        self,
        handler,
        mock_chunk_read_repository,
    ):
        """Debería retornar error cuando no hay chunks."""
        # Arrange
        mock_chunk_read_repository.find_by_article_id.return_value = []

        command = GenerateChunkEmbeddingsCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "No se encontraron chunks" in result.error_message

    @pytest.mark.asyncio
    async def test_maneja_excepcion_en_embedding_service(
        self,
        handler,
        mock_chunk_read_repository,
        mock_embedding_service,
        sample_chunk,
        mock_logger,
    ):
        """Debería manejar excepción en embedding service y continuar."""
        # Arrange
        mock_chunk_read_repository.find_by_article_id.return_value = [sample_chunk]
        mock_embedding_service.embed_batch.side_effect = Exception("API Error")

        command = GenerateChunkEmbeddingsCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        # El handler es resiliente: captura excepciones en batches y continúa
        # Retorna success=True pero con chunks_processed=0
        assert result.success is True
        assert result.chunks_processed == 0

        # Verificar que se loggeó el error
        mock_logger.error.assert_called()
