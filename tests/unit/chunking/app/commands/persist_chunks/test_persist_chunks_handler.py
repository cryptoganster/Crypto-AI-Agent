"""Tests para PersistChunksHandler."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import numpy as np
import pytest

from src.chunking.app.commands.persist_chunks.command import PersistChunksCommand
from src.chunking.app.commands.persist_chunks.handler import PersistChunksHandler
from src.chunking.app.commands.persist_chunks.result import PersistChunksResult
from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.events import ChunkCompletedEvent
from src.chunking.domain.value_objects import (
    ChunkId,
    ChunkSummary,
    TokenCount,
    VectorEmbedding,
)

pytestmark = pytest.mark.asyncio


class TestPersistChunksHandler:
    """Tests para PersistChunksHandler."""

    @pytest.fixture
    def mock_chunk_repository(self):
        """Mock para chunk repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_vector_store(self):
        """Mock para vector store."""
        return AsyncMock()

    @pytest.fixture
    def mock_validation_service(self):
        """Mock para validation service."""
        return Mock()

    @pytest.fixture
    def mock_uow(self):
        """Mock para Unit of Work."""
        uow = AsyncMock()
        uow.__aenter__.return_value = uow
        uow.__aexit__.return_value = None
        return uow

    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        logger = Mock()
        logger.bind.return_value = logger
        return logger

    @pytest.fixture
    def handler(
        self,
        mock_chunk_repository,
        mock_vector_store,
        mock_validation_service,
        mock_uow,
        mock_logger,
    ):
        """Handler con dependencias mockeadas."""
        return PersistChunksHandler(
            chunk_repository=mock_chunk_repository,
            vector_store=mock_vector_store,
            validation_service=mock_validation_service,
            uow=mock_uow,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_chunks(self):
        """Chunks de ejemplo con embeddings y summaries."""
        article_id = str(uuid4())
        chunks = []

        for i in range(3):
            chunk = ContentChunk(
                id=ChunkId.generate(),
                article_id=article_id,
                content=f"Contenido del chunk {i}",
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                token_count=TokenCount(value=50, encoding="cl100k_base"),
                source_url="https://example.com/article",
            )
            # Agregar embedding y summary
            vec = np.array([0.1] * 768)
            vec = vec / np.linalg.norm(vec)  # Normalizar
            chunk.embed(
                VectorEmbedding(vector=vec, model="nomic-embed-text", dimension=768)
            )
            chunk.summarize(
                ChunkSummary(
                    content=f"Summary del chunk {i}. Esta es la segunda frase. Y la tercera frase.",
                    sentence_count=3,
                )
            )
            chunks.append(chunk)

        return chunks

    async def test_persiste_chunks_validos_en_vector_store(
        self,
        handler,
        mock_chunk_repository,
        mock_vector_store,
        mock_validation_service,
        mock_uow,
        sample_chunks,
    ):
        """Debería persistir solo chunks válidos en vector store."""
        # Arrange
        article_id = sample_chunks[0].article_id
        command = PersistChunksCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        # Service returns empty list when validation passes
        mock_validation_service.validate_chunks_for_persistence.return_value = []

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.chunks_persisted == 3
        assert result.chunks_skipped == 0

        # Verificar que se llamó al vector store
        mock_vector_store.store_chunks.assert_called_once_with(sample_chunks)

        # Verificar que se usó UoW
        mock_uow.__aenter__.assert_called_once()
        mock_uow.commit.assert_called_once()

    async def test_llama_mark_as_completed_correctamente(
        self,
        handler,
        mock_chunk_repository,
        mock_vector_store,
        mock_validation_service,
        mock_uow,
        sample_chunks,
    ):
        """Debería llamar chunk.mark_as_completed() para cada chunk."""
        # Arrange
        article_id = sample_chunks[0].article_id
        command = PersistChunksCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_validation_service.validate_chunks_for_persistence.return_value = []

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que todos los chunks están marcados como completados
        for chunk in sample_chunks:
            assert chunk.is_completed() is True

    async def test_content_chunk_emite_chunk_completed_event(
        self,
        handler,
        mock_chunk_repository,
        mock_vector_store,
        mock_validation_service,
        mock_uow,
        sample_chunks,
    ):
        """Debería verificar que ContentChunk emite ChunkCompletedEvent."""
        # Arrange
        article_id = sample_chunks[0].article_id
        command = PersistChunksCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_validation_service.validate_chunks_for_persistence.return_value = []

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que cada chunk tiene ChunkCompletedEvent
        for chunk in sample_chunks:
            events = chunk.get_uncommitted_events()
            completed_events = [e for e in events if isinstance(e, ChunkCompletedEvent)]
            assert len(completed_events) >= 1
            assert completed_events[-1].chunk_id == str(chunk.id)

    async def test_usa_uow_correctamente(
        self,
        handler,
        mock_chunk_repository,
        mock_vector_store,
        mock_validation_service,
        mock_uow,
        sample_chunks,
    ):
        """Debería usar UoW correctamente para transacción."""
        # Arrange
        article_id = sample_chunks[0].article_id
        command = PersistChunksCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_validation_service.validate_chunks_for_persistence.return_value = []

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se usó UoW como context manager
        mock_uow.__aenter__.assert_called_once()
        mock_uow.__aexit__.assert_called_once()

        # Verificar que se hizo commit
        mock_uow.commit.assert_called_once()

    async def test_persiste_chunks_actualizados_en_repository(
        self,
        handler,
        mock_chunk_repository,
        mock_vector_store,
        mock_validation_service,
        mock_uow,
        sample_chunks,
    ):
        """Debería persistir chunks actualizados en repository."""
        # Arrange
        article_id = sample_chunks[0].article_id
        command = PersistChunksCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_validation_service.validate_chunks_for_persistence.return_value = []

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se guardó cada chunk
        assert mock_chunk_repository.save.call_count == 3

        # Verificar que se guardaron los chunks correctos
        saved_chunks = [
            call.args[0] for call in mock_chunk_repository.save.call_args_list
        ]
        assert set(saved_chunks) == set(sample_chunks)

    async def test_omite_chunks_ya_completados(
        self,
        handler,
        mock_chunk_repository,
        mock_vector_store,
        mock_validation_service,
        mock_uow,
        sample_chunks,
    ):
        """Debería omitir chunks que ya están completados."""
        # Arrange
        article_id = sample_chunks[0].article_id
        command = PersistChunksCommand(article_id=article_id)

        # Marcar primer chunk como completado
        sample_chunks[0].mark_as_completed()

        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_validation_service.validate_chunks_for_persistence.return_value = []

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.chunks_persisted == 2  # Solo 2 chunks no completados
        assert result.chunks_skipped == 1

        # Verificar que solo se persistieron chunks no completados
        persisted_chunks = mock_vector_store.store_chunks.call_args[0][0]
        assert len(persisted_chunks) == 2
        assert sample_chunks[0] not in persisted_chunks

    async def test_retorna_error_cuando_no_hay_chunks(
        self,
        handler,
        mock_chunk_repository,
        mock_validation_service,
    ):
        """Debería retornar error cuando no hay chunks."""
        # Arrange
        article_id = str(uuid4())
        command = PersistChunksCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = []

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "No se encontraron chunks" in result.error_message

        # No debería llamar a validation ni vector store
        mock_validation_service.validate_chunks_for_persistence.assert_not_called()

    async def test_retorna_error_cuando_validacion_falla(
        self,
        handler,
        mock_chunk_repository,
        mock_validation_service,
        sample_chunks,
    ):
        """Debería retornar error cuando validación falla."""
        # Arrange
        article_id = sample_chunks[0].article_id
        command = PersistChunksCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        # Service returns list of errors when validation fails
        mock_validation_service.validate_chunks_for_persistence.return_value = [
            "Chunk sin embedding",
            "Chunk sin summary",
        ]

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "Validación falló" in result.error_message
        assert "Chunk sin embedding" in result.error_message

    async def test_maneja_excepcion_en_vector_store(
        self,
        handler,
        mock_chunk_repository,
        mock_vector_store,
        mock_validation_service,
        mock_uow,
        sample_chunks,
    ):
        """Debería manejar excepción en vector store."""
        # Arrange
        article_id = sample_chunks[0].article_id
        command = PersistChunksCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_validation_service.validate_chunks_for_persistence.return_value = []
        mock_vector_store.store_chunks.side_effect = Exception("Vector store error")

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "Error persistiendo chunks" in result.error_message
        assert "Vector store error" in result.error_message

    async def test_logging_detallado(
        self,
        handler,
        mock_chunk_repository,
        mock_vector_store,
        mock_validation_service,
        mock_uow,
        mock_logger,
        sample_chunks,
    ):
        """Debería loggear operaciones detalladamente."""
        # Arrange
        article_id = sample_chunks[0].article_id
        command = PersistChunksCommand(
            article_id=article_id,
            correlation_id="test-correlation-123",
        )

        mock_chunk_repository.find_by_article_id.return_value = sample_chunks
        mock_validation_service.validate_chunks_for_persistence.return_value = []

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se loggeó inicio
        info_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Iniciando persistencia" in str(call)
        ]
        assert len(info_calls) >= 1

        # Verificar que se loggeó completitud
        completion_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "completada exitosamente" in str(call)
        ]
        assert len(completion_calls) >= 1
