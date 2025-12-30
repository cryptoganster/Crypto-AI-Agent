"""Tests para GenerateTLDRHandler."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.chunking.app.commands.generate_tldr.command import GenerateTLDRCommand
from src.chunking.app.commands.generate_tldr.handler import GenerateTLDRHandler
from src.chunking.app.commands.generate_tldr.result import GenerateTLDRResult
from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects import (
    ChunkId,
    ChunkSummary,
    TokenCount,
    VectorEmbedding,
)

pytestmark = pytest.mark.asyncio


class TestGenerateTLDRHandler:
    """Tests para GenerateTLDRHandler."""

    @pytest.fixture
    def mock_summarization_service(self):
        """Mock para summarization service."""
        service = Mock()
        service.fuse_into_tldr.return_value = (
            "- Punto clave 1: Información importante del artículo\n"
            "- Punto clave 2: Datos relevantes y conclusiones\n"
            "- Punto clave 3: Implicaciones y contexto adicional"
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
        mock_logger,
    ):
        """Handler con dependencias mockeadas."""
        return GenerateTLDRHandler(
            summarization_service=mock_summarization_service,
            chunk_repository=mock_chunk_repository,
            article_repository=mock_article_repository,
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

    async def test_genera_tldr_correctamente(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        mock_summarization_service,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería generar TLDR correctamente."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateTLDRCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.article_id == article_id
        assert result.tldr is not None
        assert len(result.tldr) > 0
        assert result.chunks_used == 3
        assert result.bullet_count == 3

        # Verificar que se llamó al service correctamente
        mock_summarization_service.fuse_into_tldr.assert_called_once()
        call_args = mock_summarization_service.fuse_into_tldr.call_args
        assert len(call_args.kwargs["chunk_summaries"]) == 3
        assert call_args.kwargs["article_title"] == str(sample_article._metadata.title)

        # Verificar que se validó la calidad
        mock_summarization_service.validate_summary_quality.assert_called_once()

        # Verificar que se persistió el artículo
        mock_article_repository.save.assert_called_once_with(sample_article)

    async def test_fusiona_summaries_de_chunks(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        mock_summarization_service,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería fusionar summaries de chunks correctamente."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateTLDRCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se pasaron todos los chunk summaries al service
        call_args = mock_summarization_service.fuse_into_tldr.call_args
        chunk_summaries = call_args.kwargs["chunk_summaries"]
        assert len(chunk_summaries) == 3
        for i, summary in enumerate(chunk_summaries):
            assert f"Summary del chunk {i}" in summary

    async def test_actualiza_article_aggregate(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería actualizar Article aggregate con tldr."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateTLDRCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Agregar método update_tldr al mock si no existe
        if not hasattr(sample_article, "update_tldr"):
            sample_article.update_tldr = Mock()

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se llamó a update_tldr (si existe)
        if hasattr(sample_article, "update_tldr") and callable(
            sample_article.update_tldr
        ):
            sample_article.update_tldr.assert_called_once()

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
        command = GenerateTLDRCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se llamó a save con el artículo
        mock_article_repository.save.assert_called_once()
        saved_article = mock_article_repository.save.call_args[0][0]
        assert saved_article == sample_article

    async def test_retorna_error_cuando_no_hay_chunks(
        self,
        handler,
        mock_chunk_repository,
    ):
        """Debería retornar error cuando no hay chunks."""
        # Arrange
        article_id = str(uuid4())
        command = GenerateTLDRCommand(article_id=article_id)

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
        command = GenerateTLDRCommand(article_id=article_id)

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
        command = GenerateTLDRCommand(article_id=article_id)

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

    async def test_retorna_error_cuando_tldr_no_cumple_calidad(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        mock_summarization_service,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería retornar error cuando TLDR no cumple criterios de calidad."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateTLDRCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Configurar service para retornar TLDR inválido
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
        command = GenerateTLDRCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Configurar service para lanzar excepción
        mock_summarization_service.fuse_into_tldr.side_effect = Exception(
            "LLM service error"
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.article_id == article_id
        assert "Error generando TLDR" in result.error_message

    async def test_cuenta_bullets_correctamente(
        self,
        handler,
        mock_chunk_repository,
        mock_article_repository,
        mock_summarization_service,
        sample_chunks_with_summaries,
        sample_article,
    ):
        """Debería contar bullets correctamente en el TLDR."""
        # Arrange
        article_id = sample_chunks_with_summaries[0].article_id
        command = GenerateTLDRCommand(article_id=article_id)

        mock_chunk_repository.find_by_article_id.return_value = (
            sample_chunks_with_summaries
        )
        mock_article_repository.find_by_id.return_value = sample_article

        # Configurar TLDR con 5 bullets
        mock_summarization_service.fuse_into_tldr.return_value = (
            "- Bullet 1\n" "- Bullet 2\n" "- Bullet 3\n" "- Bullet 4\n" "- Bullet 5"
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.bullet_count == 5
