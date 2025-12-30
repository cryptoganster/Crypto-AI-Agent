"""Tests para GenerateContentWithRAGHandler."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

pytestmark = pytest.mark.asyncio

import numpy as np

from src.chunking.domain.aggregates.content_chunk import ChunkStatus, ContentChunk
from src.chunking.domain.interfaces.services import IEmbeddingService
from src.chunking.domain.value_objects import TokenCount, VectorEmbedding
from src.rag.app.commands.generate_content_with_rag.command import (
    GenerateContentWithRAGCommand,
)
from src.rag.app.commands.generate_content_with_rag.handler import (
    GenerateContentWithRAGHandler,
)
from src.rag.app.commands.generate_content_with_rag.result import (
    GenerateContentWithRAGResult,
    GeneratedContent,
)
from src.rag.domain.aggregates.context_pack import ContextPack
from src.rag.domain.interfaces.llm_service import ILLMService
from src.rag.domain.services.context_assembly import RAGContextAssemblyService
from src.shared.kernel.logger import ILogger


class TestGenerateContentWithRAGHandler:
    """Tests para GenerateContentWithRAGHandler."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock para embedding service."""
        service = AsyncMock(spec=IEmbeddingService)

        # Mock embed_text para retornar embedding válido
        async def mock_embed_text(text: str):
            vector = np.random.rand(768).astype(np.float32)
            vector = vector / np.linalg.norm(vector)
            return VectorEmbedding(
                vector=vector,
                model="nomic-embed-text",
                dimension=768,
            )

        service.embed_text = mock_embed_text
        return service

    @pytest.fixture
    def mock_context_assembly_service(self):
        """Mock para context assembly service."""
        service = AsyncMock(spec=RAGContextAssemblyService)

        # Mock assemble_context_pack
        async def mock_assemble(query, query_embedding, top_k, filters):
            # Crear mock context pack
            pack = Mock(spec=ContextPack)
            pack.id = uuid4()
            pack.query = query
            pack.chunk_ids = [uuid4() for _ in range(5)]
            pack.sources = [
                "https://example.com/article1",
                "https://example.com/article2",
            ]
            pack.relevance_scores = [0.95, 0.90, 0.85, 0.80, 0.75]
            pack.total_tokens = 2000
            pack.get_chunk_count = Mock(return_value=5)
            pack.get_source_count = Mock(return_value=2)
            return pack

        service.assemble_context_pack = mock_assemble

        # Mock get_context_pack_summary
        async def mock_summary(pack):
            return {
                "chunk_count": 5,
                "source_count": 2,
                "average_relevance": 0.85,
                "sources": pack.sources,
            }

        service.get_context_pack_summary = mock_summary

        return service

    @pytest.fixture
    def mock_llm_service(self):
        """Mock para LLM service."""
        service = AsyncMock(spec=ILLMService)

        # Mock generate
        async def mock_generate(prompt, max_tokens, temperature, system_prompt=None):
            return """# Bitcoin ETF Regulation Analysis

## Executive Summary
Recent regulatory developments around Bitcoin ETFs have significant implications for the crypto market.

## Key Findings
- SEC approval process is progressing
- Major institutional interest increasing
- Market volatility expected

## Impact Analysis
The approval of Bitcoin ETFs could bring billions in institutional capital.

## Sources
1. https://example.com/article1
2. https://example.com/article2"""

        service.generate = mock_generate
        return service

    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        logger = Mock(spec=ILogger)
        logger.bind = Mock(return_value=logger)
        logger.info = Mock()
        logger.debug = Mock()
        logger.error = Mock()
        return logger

    @pytest.fixture
    def handler(
        self,
        mock_embedding_service,
        mock_context_assembly_service,
        mock_llm_service,
        mock_logger,
    ):
        """Handler con dependencias mockeadas."""
        return GenerateContentWithRAGHandler(
            embedding_service=mock_embedding_service,
            context_assembly_service=mock_context_assembly_service,
            llm_service=mock_llm_service,
            logger=mock_logger,
        )

    async def test_handle_successful_generation(self, handler):
        """Debería generar contenido exitosamente."""
        # Arrange
        command = GenerateContentWithRAGCommand(
            query="Bitcoin ETF regulation impact",
            top_k=10,
            content_type="analysis",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.generated_content is not None
        assert result.error is None
        assert result.query == command.query

        # Verificar contenido generado
        content = result.generated_content
        assert isinstance(content, GeneratedContent)
        assert len(content.content) > 0
        assert len(content.sources) > 0
        assert len(content.chunk_ids) > 0
        assert len(content.relevance_scores) > 0
        assert content.tokens_used > 0
        assert content.model is not None
        assert isinstance(content.generated_at, datetime)

    async def test_handle_includes_source_citations(self, handler):
        """Debería incluir citaciones de fuentes en el resultado."""
        # Arrange
        command = GenerateContentWithRAGCommand(
            query="Bitcoin regulation",
            top_k=5,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert len(result.generated_content.sources) > 0

        # Verificar que las fuentes son URLs válidas
        for source in result.generated_content.sources:
            assert source.startswith("http")

    async def test_handle_with_filters(self, handler):
        """Debería manejar filtros correctamente."""
        # Arrange
        command = GenerateContentWithRAGCommand(
            query="Bitcoin ETF",
            top_k=15,
            filters={
                "date_from": "2024-01-01",
                "topics": ["regulation", "etf"],
            },
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.generated_content is not None

    async def test_handle_different_content_types(self, handler):
        """Debería manejar diferentes tipos de contenido."""
        content_types = ["article", "analysis", "newsletter", "summary", "report"]

        for content_type in content_types:
            # Arrange
            command = GenerateContentWithRAGCommand(
                query="Bitcoin news",
                top_k=10,
                content_type=content_type,
            )

            # Act
            result = await handler.handle(command)

            # Assert
            assert result.success is True, f"Failed for content_type: {content_type}"
            assert result.generated_content is not None

    async def test_handle_with_custom_parameters(self, handler):
        """Debería respetar parámetros personalizados."""
        # Arrange
        command = GenerateContentWithRAGCommand(
            query="Ethereum upgrade",
            top_k=20,
            max_tokens=2000,
            temperature=0.3,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.generated_content.tokens_used == command.max_tokens

    async def test_handle_embedding_generation_error(
        self,
        mock_context_assembly_service,
        mock_llm_service,
        mock_logger,
    ):
        """Debería manejar error en generación de embedding."""
        # Arrange
        mock_embedding_service = AsyncMock(spec=IEmbeddingService)
        mock_embedding_service.embed_text.side_effect = Exception(
            "Embedding service error"
        )

        handler = GenerateContentWithRAGHandler(
            embedding_service=mock_embedding_service,
            context_assembly_service=mock_context_assembly_service,
            llm_service=mock_llm_service,
            logger=mock_logger,
        )

        command = GenerateContentWithRAGCommand(
            query="Bitcoin",
            top_k=10,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.error is not None
        assert "Embedding service error" in result.error
        assert result.generated_content is None

    async def test_handle_context_assembly_error(
        self,
        mock_embedding_service,
        mock_llm_service,
        mock_logger,
    ):
        """Debería manejar error en ensamblaje de contexto."""
        # Arrange
        mock_context_service = AsyncMock(spec=RAGContextAssemblyService)
        mock_context_service.assemble_context_pack.side_effect = Exception(
            "Context assembly error"
        )

        handler = GenerateContentWithRAGHandler(
            embedding_service=mock_embedding_service,
            context_assembly_service=mock_context_service,
            llm_service=mock_llm_service,
            logger=mock_logger,
        )

        command = GenerateContentWithRAGCommand(
            query="Bitcoin",
            top_k=10,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.error is not None
        assert "Context assembly error" in result.error

    async def test_handle_llm_generation_error(
        self,
        mock_embedding_service,
        mock_context_assembly_service,
        mock_logger,
    ):
        """Debería manejar error en generación LLM."""
        # Arrange
        mock_llm = AsyncMock(spec=ILLMService)
        mock_llm.generate.side_effect = Exception("LLM generation error")

        handler = GenerateContentWithRAGHandler(
            embedding_service=mock_embedding_service,
            context_assembly_service=mock_context_assembly_service,
            llm_service=mock_llm,
            logger=mock_logger,
        )

        command = GenerateContentWithRAGCommand(
            query="Bitcoin",
            top_k=10,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.error is not None
        assert "LLM generation error" in result.error

    async def test_handle_logs_operations(self, handler, mock_logger):
        """Debería loggear operaciones correctamente."""
        # Arrange
        command = GenerateContentWithRAGCommand(
            query="Bitcoin ETF",
            top_k=10,
        )

        # Act
        await handler.handle(command)

        # Assert
        # Verificar que se loggearon las operaciones principales
        assert mock_logger.info.called
        assert mock_logger.debug.called

        # Verificar llamadas específicas
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Iniciando generación" in call for call in info_calls)
        assert any("Context pack ensamblado" in call for call in info_calls)
        assert any("Contenido generado exitosamente" in call for call in info_calls)

    async def test_format_rag_prompt_includes_context(self, handler):
        """Debería formatear prompt con contexto recuperado."""
        # Arrange
        query = "Bitcoin ETF regulation"
        context_metadata = {
            "chunk_count": 10,
            "source_count": 3,
            "average_relevance": 0.85,
            "sources": [
                "https://example.com/article1",
                "https://example.com/article2",
            ],
        }

        # Act
        prompt = handler._format_rag_prompt(
            query=query,
            context_pack_metadata=context_metadata,
            content_type="article",
        )

        # Assert
        assert query in prompt
        assert "10" in prompt  # chunk_count
        assert "3" in prompt  # source_count
        assert "0.85" in prompt  # average_relevance
        assert "https://example.com/article1" in prompt
        assert "EXCLUSIVAMENTE" in prompt  # Instrucción importante
        assert "NO inventes" in prompt  # Instrucción importante

    async def test_get_system_prompt_returns_appropriate_prompt(self, handler):
        """Debería retornar system prompt apropiado por tipo de contenido."""
        # Test para cada tipo de contenido
        content_types = ["article", "analysis", "newsletter", "summary", "report"]

        for content_type in content_types:
            # Act
            system_prompt = handler._get_system_prompt(content_type)

            # Assert
            assert isinstance(system_prompt, str)
            assert len(system_prompt) > 0
            # Verificar que el prompt contiene "Eres" (inicio de todos los prompts)
            assert system_prompt.startswith("Eres")

    async def test_get_content_type_instructions_returns_specific_instructions(
        self,
        handler,
    ):
        """Debería retornar instrucciones específicas por tipo de contenido."""
        # Test para cada tipo de contenido
        content_types = ["article", "analysis", "newsletter", "summary", "report"]

        for content_type in content_types:
            # Act
            instructions = handler._get_content_type_instructions(content_type)

            # Assert
            assert isinstance(instructions, str)
            assert len(instructions) > 0

    async def test_format_sources_formats_correctly(self, handler):
        """Debería formatear fuentes correctamente."""
        # Arrange
        sources = [
            "https://example.com/article1",
            "https://example.com/article2",
            "https://example.com/article3",
        ]

        # Act
        formatted = handler._format_sources(sources)

        # Assert
        assert "1. https://example.com/article1" in formatted
        assert "2. https://example.com/article2" in formatted
        assert "3. https://example.com/article3" in formatted

    async def test_format_sources_limits_to_10(self, handler):
        """Debería limitar fuentes a 10 en el formato."""
        # Arrange
        sources = [f"https://example.com/article{i}" for i in range(15)]

        # Act
        formatted = handler._format_sources(sources)

        # Assert
        assert "10. https://example.com/article9" in formatted
        assert "... y 5 fuentes más" in formatted
        assert "11." not in formatted

    async def test_format_sources_handles_empty_list(self, handler):
        """Debería manejar lista vacía de fuentes."""
        # Arrange
        sources = []

        # Act
        formatted = handler._format_sources(sources)

        # Assert
        assert "No hay fuentes disponibles" in formatted

    async def test_handle_returns_context_pack_id(self, handler):
        """Debería retornar ID del context pack usado."""
        # Arrange
        command = GenerateContentWithRAGCommand(
            query="Bitcoin",
            top_k=10,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.context_pack_id is not None
        assert isinstance(result.context_pack_id, str)

    async def test_handle_preserves_query_in_result(self, handler):
        """Debería preservar query original en el resultado."""
        # Arrange
        query = "Bitcoin ETF regulation impact analysis"
        command = GenerateContentWithRAGCommand(
            query=query,
            top_k=10,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.query == query

    async def test_generated_content_includes_all_required_fields(self, handler):
        """Debería incluir todos los campos requeridos en GeneratedContent."""
        # Arrange
        command = GenerateContentWithRAGCommand(
            query="Bitcoin",
            top_k=10,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        content = result.generated_content
        assert content.content is not None
        assert isinstance(content.sources, list)
        assert isinstance(content.chunk_ids, list)
        assert isinstance(content.relevance_scores, list)
        assert content.tokens_used > 0
        assert content.model is not None
        assert isinstance(content.generated_at, datetime)

        # Verificar que las listas tienen el mismo tamaño
        assert len(content.chunk_ids) == len(content.relevance_scores)
