"""Tests para GenerateGlobalSummaryHandler."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.chunking.app.commands.generate_global_summary.command import (
    GenerateGlobalSummaryCommand,
)
from src.chunking.app.commands.generate_global_summary.handler import (
    GenerateGlobalSummaryHandler,
)
from src.chunking.app.commands.generate_global_summary.result import (
    GenerateGlobalSummaryResult,
)
from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects import (
    ChunkId,
    ChunkSummary,
    TokenCount,
    VectorEmbedding,
)
from src.shared.config.ai_processing_config import AIProcessingConfig

pytestmark = pytest.mark.asyncio


class TestGenerateGlobalSummaryHandler:
    """Tests para GenerateGlobalSummaryHandler."""

    @pytest.fixture
    def mock_summarization_service(self):
        """Mock para summarization service."""
        service = Mock()
        service.generate_global_summary.return_value = (
            "Este es un summary global generado por el LLM. "
            "Resume el contenido completo del artículo en varias frases coherentes."
        )
        service.validate_summary_quality.return_value = True
        return service

    @pytest.fixture
    def mock_chunk_repository(self):
        """Mock para chunk repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_article_repository(self):
        """Mock para article repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_config(self):
        """Mock para configuración."""
        config = Mock(spec=AIProcessingConfig)
        config.global_summary_max_length = 500
        return config

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
        mock_chunk_repository,
        mock_article_repository,
        mock_config,
        mock_logger,
    ):
        """Handler con dependencias mockeadas."""
        return GenerateGlobalSummaryHandler(
            summarization_service=mock_summarization_service,
            chunk_repository=mock_chunk_repository,
            article_repository=mock_article_repository,
            config=mock_config,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_chunks_with_summaries(self):
        """Chunks de ejemplo con summaries."""
        import numpy as np

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
            # Agregar embedding primero (requerido antes de summary)
            vec = np.array([0.1] * 768)
            vec = vec / np.linalg.norm(vec)  # Normalizar
            chunk.embed(
                VectorEmbedding(vector=vec, model="nomic-embed-text", dimension=768)
            )
            # Agregar summary
            chunk.summarize(
                ChunkSummary(
                    content=f"Summary del chunk {i}. Contiene información importante. Datos relevantes.",
                    sentence_count=3,
                )
            )
            chunks.append(chunk)

        return chunks

    @pytest.fixture
    def sample_rss_article(self):
        """Artículo de ejemplo."""
        from src.rss.article.domain.aggregates.rss_article import RssArticle
        from src.rss.article.domain.value_objects.metadata import (
            RssArticleId,
            RssArticleMetadata,
            RssArticleTitle,
            RssArticleUrl,
        )

        metadata = RssArticleMetadata(
            id=RssArticleId.generate(),
            title=RssArticleTitle("Título del Artículo de Prueba"),
            url=RssArticleUrl("https://example.com/article"),
            source_id="source-123",
        )

        return RssArticle(metadata=metadata)

    async def test_genera_summary_global_correctamente(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        mock_summarization_service,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería generar summary global correctamente."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateGlobalSummaryCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.article_id == article_id
        assert result.global_summary is not None
        assert len(result.global_summary) > 0
        assert result.chunks_used == 3
        assert result.summary_length == len(result.global_summary)

        # Verificar que se llamó al service correctamente
        mock_summarization_service.generate_global_summary.assert_called_once()
        call_args = mock_summarization_service.generate_global_summary.call_args
        assert len(call_args.kwargs["chunk_summaries"]) == 3
        assert call_args.kwargs["article_title"] == str(sample_article._metadata.title)
        assert call_args.kwargs["max_length"] == 500

        # Verificar que se validó la calidad
        mock_summarization_service.validate_summary_quality.assert_called_once()

        # Verificar que se actualizó el artículo
        assert sample_article._metadata.summary is not None
        mock_article_repository.save.assert_called_once_with(sample_article)

    async def test_respeta_limite_de_texto_de_configuracion(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        mock_summarization_service,
        mock_config,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería respetar límite de texto de configuración."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateGlobalSummaryCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article
        mock_config.global_summary_max_length = 300

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se pasó el límite correcto al service
        call_args = mock_summarization_service.generate_global_summary.call_args
        assert call_args.kwargs["max_length"] == 300

        # Verificar que se validó con el límite correcto
        validate_call_args = (
            mock_summarization_service.validate_summary_quality.call_args
        )
        assert validate_call_args.kwargs["max_length"] == 300

    async def test_actualiza_article_aggregate(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería actualizar Article aggregate con global_summary."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateGlobalSummaryCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Verificar que inicialmente no tiene summary
        assert sample_article._metadata.summary is None

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que el artículo ahora tiene summary
        assert sample_article._metadata.summary is not None
        assert len(str(sample_article._metadata.summary)) > 0

    async def test_persiste_article_actualizado(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería persistir Article actualizado."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateGlobalSummaryCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se llamó a save con el artículo actualizado
        mock_article_repository.save.assert_called_once()
        saved_article = mock_article_repository.save.call_args[0][0]
        assert saved_article == sample_article
        assert saved_article._metadata.summary is not None

    async def test_retorna_error_cuando_no_hay_chunks(
        self,
        handler,
        mock_chunk_repository,
    ):
        """Debería retornar error cuando no hay chunks."""
        # Arrange
        article_id = str(uuid4())
        command = GenerateGlobalSummaryCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = []

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.article_id == article_id
        assert "No se encontraron chunks" in result.error_message

    async def test_retorna_error_cuando_chunks_sin_summaries(
        self,
        handler,
        mock_chunk_repository,
    ):
        """Debería retornar error cuando chunks no tienen summaries."""
        # Arrange
        article_id = str(uuid4())
        command = GenerateGlobalSummaryCommand(article_id=article_id)

        # Crear chunks sin summaries
        chunks = [
            ContentChunk(
                id=ChunkId.generate(),
                article_id=article_id,
                content="Contenido sin summary",
                position=0,
                start_char=0,
                end_char=100,
                token_count=TokenCount(value=50, encoding="cl100k_base"),
                source_url="https://example.com/article",
            )
        ]

        mock_chunk_repository.find_by_article_id.return_value = chunks

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.article_id == article_id
        assert "No se encontraron chunk summaries" in result.error_message

    async def test_retorna_error_cuando_articulo_no_encontrado(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        sample_chunks_with_summaries,
    ):
        """Debería retornar error cuando artículo no se encuentra."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateGlobalSummaryCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = None

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.article_id == article_id
        assert "Artículo no encontrado" in result.error_message

    async def test_retorna_error_cuando_summary_no_cumple_calidad(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        mock_summarization_service,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería retornar error cuando summary no cumple criterios de calidad."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateGlobalSummaryCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Configurar service para retornar summary inválido
        mock_summarization_service.validate_summary_quality.return_value = False

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.article_id == article_id
        assert "no cumple criterios de calidad" in result.error_message

    async def test_maneja_excepcion_de_service(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        mock_summarization_service,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería manejar excepción del summarization service."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateGlobalSummaryCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Configurar service para lanzar excepción
        mock_summarization_service.generate_global_summary.side_effect = Exception(
            "LLM service error"
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.article_id == article_id
        assert "Error generando summary global" in result.error_message
