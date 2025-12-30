"""Unit tests para SummarizationService."""

from unittest.mock import AsyncMock, Mock

import pytest

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.value_objects.chunk_summary import ChunkSummary
from src.chunking.domain.value_objects.tldr import TLDR
from src.rag.domain.interfaces.llm_service import ILLMService
from src.rag.domain.services import SummarizationService


class TestSummarizationService:
    """Tests para SummarizationService."""

    @pytest.fixture
    def mock_llm_service(self):
        """Mock para LLM service."""
        return AsyncMock(spec=ILLMService)

    @pytest.fixture
    def service(self, mock_llm_service):
        """Service con LLM mockeado."""
        return SummarizationService(llm_service=mock_llm_service)

    @pytest.fixture
    def sample_chunk(self):
        """Sample chunk para testing."""
        return Mock(
            spec=ContentChunk,
            content="Bitcoin alcanzó un nuevo máximo histórico de $100,000 el lunes. "
            "Los analistas atribuyen el aumento a la aprobación de ETFs de Bitcoin. "
            "El volumen de trading aumentó 300% en las últimas 24 horas. "
            "Instituciones como BlackRock y Fidelity están comprando agresivamente.",
        )

    # Test chunk summarization

    @pytest.mark.asyncio
    async def test_summarize_chunk_generates_summary(
        self,
        service,
        mock_llm_service,
        sample_chunk,
    ):
        """Debería generar summary para chunk."""
        # Arrange
        mock_llm_service.generate.return_value = (
            "Bitcoin alcanzó $100,000. "
            "ETFs de Bitcoin fueron aprobados. "
            "El volumen de trading aumentó 300%. "
            "Instituciones están comprando."
        )

        # Act
        result = await service.summarize_chunk(sample_chunk)

        # Assert
        assert isinstance(result, ChunkSummary)
        assert result.content == mock_llm_service.generate.return_value
        assert result.sentence_count == 4

        # Verificar que se llamó al LLM con parámetros correctos
        mock_llm_service.generate.assert_called_once()
        call_args = mock_llm_service.generate.call_args
        assert call_args.kwargs["max_tokens"] == 200
        assert call_args.kwargs["temperature"] == 0.3
        assert sample_chunk.content in call_args.kwargs["prompt"]

    @pytest.mark.asyncio
    async def test_summarize_chunk_counts_sentences_correctly(
        self,
        service,
        mock_llm_service,
        sample_chunk,
    ):
        """Debería contar frases correctamente."""
        # Arrange
        mock_llm_service.generate.return_value = (
            "Primera frase. Segunda frase. Tercera frase."
        )

        # Act
        result = await service.summarize_chunk(sample_chunk)

        # Assert
        assert result.sentence_count == 3

    @pytest.mark.asyncio
    async def test_summarize_chunk_handles_empty_sentences(
        self,
        service,
        mock_llm_service,
        sample_chunk,
    ):
        """Debería ignorar frases vacías al contar."""
        # Arrange
        mock_llm_service.generate.return_value = (
            "Primera frase. . Segunda frase.  . Tercera frase."
        )

        # Act
        result = await service.summarize_chunk(sample_chunk)

        # Assert
        # Solo debe contar frases no vacías
        assert result.sentence_count == 3

    @pytest.mark.asyncio
    async def test_summarize_chunk_includes_chunk_content_in_prompt(
        self,
        service,
        mock_llm_service,
        sample_chunk,
    ):
        """Debería incluir contenido del chunk en el prompt."""
        # Arrange
        mock_llm_service.generate.return_value = (
            "Primera frase del summary. Segunda frase. Tercera frase."
        )

        # Act
        await service.summarize_chunk(sample_chunk)

        # Assert
        call_args = mock_llm_service.generate.call_args
        prompt = call_args.kwargs["prompt"]
        assert sample_chunk.content in prompt
        assert "Resume el siguiente texto" in prompt
        assert "3-5 frases" in prompt

    # Test global summary generation

    @pytest.mark.asyncio
    async def test_generate_global_summary_creates_summary(
        self,
        service,
        mock_llm_service,
    ):
        """Debería generar summary global."""
        # Arrange
        full_text = "Este es un artículo largo sobre Bitcoin. " * 100
        mock_llm_service.generate.return_value = (
            "Resumen global del artículo sobre Bitcoin."
        )

        # Act
        result = await service.generate_global_summary(full_text)

        # Assert
        assert result == "Resumen global del artículo sobre Bitcoin."
        mock_llm_service.generate.assert_called_once()
        call_args = mock_llm_service.generate.call_args
        assert call_args.kwargs["max_tokens"] == 300
        assert call_args.kwargs["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_generate_global_summary_limits_text_length(
        self,
        service,
        mock_llm_service,
    ):
        """Debería limitar texto a 4000 caracteres."""
        # Arrange
        full_text = "A" * 10000  # Texto muy largo
        mock_llm_service.generate.return_value = "Summary"

        # Act
        await service.generate_global_summary(full_text)

        # Assert
        call_args = mock_llm_service.generate.call_args
        prompt = call_args.kwargs["prompt"]
        # El prompt debe contener solo los primeros 4000 caracteres
        assert "A" * 4000 in prompt
        assert len(prompt) < 5000  # Prompt completo no debe ser mucho más largo

    @pytest.mark.asyncio
    async def test_generate_global_summary_includes_existing_summary(
        self,
        service,
        mock_llm_service,
    ):
        """Debería incluir summary extractivo existente si se proporciona."""
        # Arrange
        full_text = "Texto del artículo."
        existing_summary = "Summary extractivo previo."
        mock_llm_service.generate.return_value = "Global summary"

        # Act
        await service.generate_global_summary(full_text, existing_summary)

        # Assert
        call_args = mock_llm_service.generate.call_args
        prompt = call_args.kwargs["prompt"]
        assert existing_summary in prompt
        assert "Resumen extractivo existente" in prompt

    @pytest.mark.asyncio
    async def test_generate_global_summary_without_existing_summary(
        self,
        service,
        mock_llm_service,
    ):
        """Debería funcionar sin summary extractivo."""
        # Arrange
        full_text = "Texto del artículo."
        mock_llm_service.generate.return_value = "Global summary"

        # Act
        await service.generate_global_summary(full_text, existing_summary=None)

        # Assert
        call_args = mock_llm_service.generate.call_args
        prompt = call_args.kwargs["prompt"]
        assert "Resumen extractivo existente" not in prompt

    # Test TLDR fusion

    @pytest.mark.asyncio
    async def test_fuse_into_tldr_creates_tldr(
        self,
        service,
        mock_llm_service,
    ):
        """Debería fusionar summaries en TLDR."""
        # Arrange
        global_summary = "Summary global del artículo."
        chunk_summaries = [
            ChunkSummary(content="Summary chunk 1.", sentence_count=3),
            ChunkSummary(content="Summary chunk 2.", sentence_count=4),
            ChunkSummary(content="Summary chunk 3.", sentence_count=3),
        ]
        metadata = {
            "source": "CoinDesk",
            "date": "2024-12-10",
            "tokens": ["BTC", "ETH"],
        }

        mock_llm_service.generate.return_value = """- Bitcoin alcanzó $100,000
- ETFs aprobados por la SEC
- Instituciones comprando agresivamente
- Volumen de trading aumentó 300%"""

        # Act
        result = await service.fuse_into_tldr(
            global_summary,
            chunk_summaries,
            metadata,
        )

        # Assert
        assert isinstance(result, TLDR)
        assert len(result.bullets) == 4
        assert "Bitcoin alcanzó $100,000" in result.bullets
        assert "ETFs aprobados por la SEC" in result.bullets

    @pytest.mark.asyncio
    async def test_fuse_into_tldr_includes_all_data_in_prompt(
        self,
        service,
        mock_llm_service,
    ):
        """Debería incluir todos los datos en el prompt."""
        # Arrange
        global_summary = "Global summary."
        chunk_summaries = [
            ChunkSummary(
                content="Chunk summary one. Second sentence. Third sentence.",
                sentence_count=3,
            ),
        ]
        metadata = {
            "source": "CoinDesk",
            "date": "2024-12-10",
            "tokens": ["BTC"],
        }

        mock_llm_service.generate.return_value = (
            "- Bitcoin price increased\n" "- ETFs approved\n" "- Market volume up"
        )

        # Act
        await service.fuse_into_tldr(global_summary, chunk_summaries, metadata)

        # Assert
        call_args = mock_llm_service.generate.call_args
        prompt = call_args.kwargs["prompt"]

        assert global_summary in prompt
        assert "Chunk summary one" in prompt
        assert "CoinDesk" in prompt
        assert "2024-12-10" in prompt
        assert "BTC" in prompt

    @pytest.mark.asyncio
    async def test_fuse_into_tldr_parses_bullets_correctly(
        self,
        service,
        mock_llm_service,
    ):
        """Debería parsear bullets correctamente."""
        # Arrange
        global_summary = "Summary."
        chunk_summaries = []
        metadata = {"source": "Test", "date": "2024-12-10", "tokens": []}

        mock_llm_service.generate.return_value = """- Primera línea
- Segunda línea
Texto sin bullet
- Tercera línea
- Cuarta línea"""

        # Act
        result = await service.fuse_into_tldr(
            global_summary,
            chunk_summaries,
            metadata,
        )

        # Assert
        assert len(result.bullets) == 4
        assert "Primera línea" in result.bullets
        assert "Segunda línea" in result.bullets
        assert "Tercera línea" in result.bullets
        assert "Cuarta línea" in result.bullets
        assert "Texto sin bullet" not in result.bullets

    @pytest.mark.asyncio
    async def test_fuse_into_tldr_strips_bullet_markers(
        self,
        service,
        mock_llm_service,
    ):
        """Debería remover marcadores de bullet."""
        # Arrange
        global_summary = "Summary."
        chunk_summaries = []
        metadata = {"source": "Test", "date": "2024-12-10", "tokens": []}

        mock_llm_service.generate.return_value = """- Bullet con espacios  
-Bullet sin espacio
-  Bullet con múltiples espacios"""

        # Act
        result = await service.fuse_into_tldr(
            global_summary,
            chunk_summaries,
            metadata,
        )

        # Assert
        # Todos los bullets deben estar limpios sin "- " al inicio
        for bullet in result.bullets:
            assert not bullet.startswith("-")
            assert bullet == bullet.strip()

    @pytest.mark.asyncio
    async def test_fuse_into_tldr_uses_correct_llm_parameters(
        self,
        service,
        mock_llm_service,
    ):
        """Debería usar parámetros correctos del LLM."""
        # Arrange
        global_summary = "Summary."
        chunk_summaries = []
        metadata = {"source": "Test", "date": "2024-12-10", "tokens": []}

        mock_llm_service.generate.return_value = (
            "- Bitcoin price increased significantly\n"
            "- ETFs were approved by SEC\n"
            "- Market volume up 300 percent"
        )

        # Act
        await service.fuse_into_tldr(global_summary, chunk_summaries, metadata)

        # Assert
        call_args = mock_llm_service.generate.call_args
        assert call_args.kwargs["max_tokens"] == 250
        assert call_args.kwargs["temperature"] == 0.3

    # Test sentence/bullet counting

    @pytest.mark.asyncio
    async def test_sentence_counting_with_various_formats(
        self,
        service,
        mock_llm_service,
        sample_chunk,
    ):
        """Debería contar frases con varios formatos."""
        # Arrange - Solo casos válidos que cumplan con las restricciones de ChunkSummary
        test_cases = [
            ("Primera frase. Segunda frase. Tercera frase.", 3),
            ("Primera. Segunda. Tercera. Cuarta.", 4),
            ("Primera. Segunda. Tercera. Cuarta. Quinta.", 5),
        ]

        for text, expected_count in test_cases:
            # Arrange
            mock_llm_service.generate.return_value = text

            # Act
            result = await service.summarize_chunk(sample_chunk)

            # Assert
            assert (
                result.sentence_count == expected_count
            ), f"Failed for text: '{text}', expected {expected_count}, got {result.sentence_count}"

    @pytest.mark.asyncio
    async def test_bullet_counting_with_various_formats(
        self,
        service,
        mock_llm_service,
    ):
        """Debería contar bullets con varios formatos."""
        # Arrange
        global_summary = "Summary."
        chunk_summaries = []
        metadata = {"source": "Test", "date": "2024-12-10", "tokens": []}

        # Solo casos válidos que cumplan con las restricciones de TLDR (3-5 bullets, min 10 chars)
        test_cases = [
            ("- Bitcoin price increased\n- ETFs approved\n- Volume up 300%", 3),
            (
                "- First bullet point\n- Second bullet\n- Third bullet\n- Fourth bullet",
                4,
            ),
            (
                "- Bullet one here\n- Bullet two here\n- Bullet three\n- Bullet four\n- Bullet five",
                5,
            ),
        ]

        for text, expected_count in test_cases:
            # Arrange
            mock_llm_service.generate.return_value = text

            # Act
            result = await service.fuse_into_tldr(
                global_summary,
                chunk_summaries,
                metadata,
            )

            # Assert
            assert (
                len(result.bullets) == expected_count
            ), f"Failed for text: '{text}', expected {expected_count}, got {len(result.bullets)}"
