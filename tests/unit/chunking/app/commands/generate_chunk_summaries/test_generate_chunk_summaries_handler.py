"""Tests para GenerateChunkSummariesHandler."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from src.chunking.app.commands.generate_chunk_summaries.command import (
    GenerateChunkSummariesCommand,
)
from src.chunking.app.commands.generate_chunk_summaries.handler import (
    GenerateChunkSummariesHandler,
)
from src.chunking.app.commands.generate_chunk_summaries.result import (
    GenerateChunkSummariesResult,
)
from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects.chunk_id import ChunkId
from src.chunking.domain.value_objects.chunk_status import ChunkStatus
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
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


class TestGenerateChunkSummariesHandler:
    """Tests para GenerateChunkSummariesHandler."""

    @pytest.fixture
    def mock_summarization_service(self):
        """Mock para ISummarizationService."""
        service = AsyncMock()
        # Por defecto retorna summary válido
        service.summarize_chunk.return_value = "Este es un resumen del chunk."
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
        mock_summarization_service,
        mock_chunk_read_repository,
        mock_chunk_write_repository,
        ai_config,
        mock_logger,
    ):
        """Handler con dependencias mockeadas."""
        return GenerateChunkSummariesHandler(
            summarization_service=mock_summarization_service,
            chunk_read_repository=mock_chunk_read_repository,
            chunk_write_repository=mock_chunk_write_repository,
            config=ai_config,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_chunk(self):
        """Crea un chunk de ejemplo con embedding pero sin summary."""
        chunk = ContentChunk(
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
        # Agregar embedding para que esté en estado EMBEDDED
        chunk.embed(create_test_embedding())
        return chunk

    @pytest.mark.asyncio
    async def test_genera_summaries_para_todos_los_chunks(
        self,
        handler,
        mock_chunk_read_repository,
        mock_chunk_write_repository,
        mock_summarization_service,
        sample_chunk,
    ):
        """Debería generar summaries para todos los chunks."""
        # Arrange
        chunks = [sample_chunk]
        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        command = GenerateChunkSummariesCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.chunks_summarized == 1
        assert result.total_chunks == 1
        mock_summarization_service.summarize_chunk.assert_called_once_with(
            sample_chunk.content
        )
        mock_chunk_write_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_llama_chunk_summarize_correctamente(
        self,
        handler,
        mock_chunk_read_repository,
        mock_chunk_write_repository,
        mock_summarization_service,
        sample_chunk,
    ):
        """Debería llamar chunk.summarize() correctamente."""
        # Arrange
        chunks = [sample_chunk]
        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        summary_text = "Resumen del chunk sobre Bitcoin. Segunda frase. Tercera frase."
        mock_summarization_service.summarize_chunk.return_value = summary_text

        command = GenerateChunkSummariesCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        # Verificar que el chunk tiene el summary
        assert sample_chunk.summary is not None
        assert sample_chunk.summary.content == summary_text

    @pytest.mark.asyncio
    async def test_content_chunk_emite_chunk_summarized_event(
        self,
        handler,
        mock_chunk_read_repository,
        mock_chunk_write_repository,
        mock_summarization_service,
        sample_chunk,
    ):
        """Debería verificar que ContentChunk emite ChunkSummarizedEvent."""
        # Arrange
        chunks = [sample_chunk]
        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        summary_text = "Resumen del chunk. Segunda frase. Tercera frase."
        mock_summarization_service.summarize_chunk.return_value = summary_text

        command = GenerateChunkSummariesCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        # Verificar que el chunk tiene eventos
        events = sample_chunk.get_uncommitted_events()
        assert len(events) > 0
        # El evento debería ser ChunkSummarizedEvent
        from src.chunking.domain.events import ChunkSummarizedEvent

        assert any(isinstance(e, ChunkSummarizedEvent) for e in events)

    @pytest.mark.asyncio
    async def test_maneja_errores_en_chunks_individuales(
        self,
        handler,
        mock_chunk_read_repository,
        mock_chunk_write_repository,
        mock_summarization_service,
        sample_chunk,
    ):
        """Debería manejar errores en chunks individuales y continuar."""
        # Arrange
        chunk1 = sample_chunk
        chunk2 = ContentChunk(
            id=ChunkId.generate(),
            article_id="art-123",
            content="Otro contenido...",
            position=1,
            start_char=100,
            end_char=200,
            token_count=TokenCount(value=50, encoding="cl100k_base"),
            source_url="https://example.com/article",
            status=ChunkStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        # Agregar embedding al segundo chunk
        chunk2.embed(create_test_embedding())

        chunks = [chunk1, chunk2]
        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        # Primer chunk falla, segundo exitoso
        mock_summarization_service.summarize_chunk.side_effect = [
            Exception("Error en summarization"),
            "Resumen exitoso del segundo chunk. Segunda frase. Tercera frase.",
        ]

        command = GenerateChunkSummariesCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        # Solo 1 chunk se summarizó exitosamente
        assert result.chunks_summarized == 1
        assert result.total_chunks == 2
        # Verificar que se intentó guardar el chunk exitoso
        assert mock_chunk_write_repository.save.call_count == 1

    @pytest.mark.asyncio
    async def test_persiste_chunks_actualizados(
        self,
        handler,
        mock_chunk_read_repository,
        mock_chunk_write_repository,
        mock_summarization_service,
        sample_chunk,
    ):
        """Debería persistir chunks actualizados."""
        # Arrange
        chunks = [sample_chunk]
        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        command = GenerateChunkSummariesCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        # Verificar que se guardó el chunk
        mock_chunk_write_repository.save.assert_called_once_with(sample_chunk)

    @pytest.mark.asyncio
    async def test_retorna_error_cuando_no_hay_chunks(
        self,
        handler,
        mock_chunk_read_repository,
    ):
        """Debería retornar error cuando no hay chunks."""
        # Arrange
        mock_chunk_read_repository.find_by_article_id.return_value = []

        command = GenerateChunkSummariesCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "No se encontraron chunks" in result.error_message

    @pytest.mark.asyncio
    async def test_skip_chunks_que_ya_tienen_summary(
        self,
        handler,
        mock_chunk_read_repository,
        mock_summarization_service,
        sample_chunk,
    ):
        """Debería skip chunks que ya tienen summary."""
        # Arrange
        # Agregar summary al chunk
        summary = ChunkSummary.from_text(
            "Summary existente. Segunda frase. Tercera frase."
        )
        sample_chunk.summarize(summary)

        chunks = [sample_chunk]
        mock_chunk_read_repository.find_by_article_id.return_value = chunks

        command = GenerateChunkSummariesCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.chunks_summarized == 0
        assert result.total_chunks == 1
        # No debería llamar al servicio de summarization
        mock_summarization_service.summarize_chunk.assert_not_called()

    @pytest.mark.asyncio
    async def test_maneja_excepcion_general(
        self,
        handler,
        mock_chunk_read_repository,
    ):
        """Debería manejar excepciones generales."""
        # Arrange
        mock_chunk_read_repository.find_by_article_id.side_effect = Exception(
            "Error de base de datos"
        )

        command = GenerateChunkSummariesCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "Error generando summaries" in result.error_message

    @pytest.mark.asyncio
    async def test_procesa_multiples_chunks_correctamente(
        self,
        handler,
        mock_chunk_read_repository,
        mock_chunk_write_repository,
        mock_summarization_service,
    ):
        """Debería procesar múltiples chunks correctamente."""
        # Arrange
        chunks = []
        for i in range(5):
            chunk = ContentChunk(
                id=ChunkId.generate(),
                article_id="art-123",
                content=f"Contenido del chunk {i}",
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                token_count=TokenCount(value=50, encoding="cl100k_base"),
                source_url="https://example.com/article",
                status=ChunkStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            # Agregar embedding a cada chunk
            chunk.embed(create_test_embedding())
            chunks.append(chunk)

        mock_chunk_read_repository.find_by_article_id.return_value = chunks
        mock_summarization_service.summarize_chunk.return_value = (
            "Resumen del chunk. Segunda frase. Tercera frase."
        )

        command = GenerateChunkSummariesCommand(article_id="art-123")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.chunks_summarized == 5
        assert result.total_chunks == 5
        assert mock_summarization_service.summarize_chunk.call_count == 5
        assert mock_chunk_write_repository.save.call_count == 5
