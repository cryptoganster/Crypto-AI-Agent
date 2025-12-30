"""Tests para LangChainMarkdownSplitter."""

from unittest.mock import Mock

import pytest

from src.chunking.domain.interfaces.external import ITokenEncoder
from src.chunking.infra.external.langchain_markdown_splitter import (
    LangChainMarkdownSplitter,
)


class TestLangChainMarkdownSplitter:
    """Tests para LangChainMarkdownSplitter."""

    @pytest.fixture
    def mock_encoder(self):
        """Mock para token encoder."""
        encoder = Mock(spec=ITokenEncoder)
        # Por defecto, simular que cada palabra es 1 token
        encoder.count_tokens.side_effect = lambda text: len(text.split())
        return encoder

    def test_find_split_point_with_markdown_headers(self, mock_encoder):
        """Debería dividir en límites de headers de Markdown."""
        # Arrange
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            chunk_size=50,
            chunk_overlap=10,
        )
        text = """# Main Title

This is the introduction.

## Section 1

Content of section 1.

## Section 2

Content of section 2."""
        max_tokens = 50

        # Act
        split_point = splitter.find_split_point(text, max_tokens, [])

        # Assert
        assert split_point > 0
        assert split_point <= len(text)

    def test_find_split_point_with_text_under_limit(self, mock_encoder):
        """Debería retornar longitud completa si texto cabe."""
        # Arrange
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            chunk_size=100,
            chunk_overlap=10,
        )
        text = "# Short Title\n\nShort content."
        max_tokens = 100

        # Act
        split_point = splitter.find_split_point(text, max_tokens, [])

        # Assert
        assert split_point == len(text)

    def test_find_split_point_with_empty_text(self, mock_encoder):
        """Debería manejar texto vacío."""
        # Arrange
        mock_encoder.count_tokens.return_value = 0
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            chunk_size=100,
            chunk_overlap=10,
        )
        text = ""
        max_tokens = 100

        # Act
        split_point = splitter.find_split_point(text, max_tokens, [])

        # Assert
        assert split_point == 0

    def test_initialization_with_default_headers(self, mock_encoder):
        """Debería inicializar con headers por defecto (H1, H2, H3)."""
        # Arrange & Act
        splitter = LangChainMarkdownSplitter(token_encoder=mock_encoder)

        # Assert
        assert splitter._headers_to_split_on == [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]

    def test_initialization_with_custom_headers(self, mock_encoder):
        """Debería inicializar con headers personalizados."""
        # Arrange
        custom_headers = [
            ("#", "Title"),
            ("##", "Section"),
        ]

        # Act
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            headers_to_split_on=custom_headers,
        )

        # Assert
        assert splitter._headers_to_split_on == custom_headers

    def test_find_split_point_with_nested_headers(self, mock_encoder):
        """Debería manejar headers anidados correctamente."""
        # Arrange
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            chunk_size=30,
            chunk_overlap=5,
        )
        text = """# Title

## Subsection 1

### Detail 1

Content here.

### Detail 2

More content."""
        max_tokens = 30

        # Act
        split_point = splitter.find_split_point(text, max_tokens, [])

        # Assert
        assert split_point > 0

    def test_find_split_point_with_no_headers(self, mock_encoder):
        """Debería usar fallback si no hay headers."""
        # Arrange
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            chunk_size=5,  # Muy pequeño para forzar división
            chunk_overlap=1,
        )
        text = "Plain text without any markdown headers or structure that is very long."
        max_tokens = 5

        # Act
        split_point = splitter.find_split_point(text, max_tokens, [])

        # Assert
        assert split_point > 0
        assert split_point < len(text)

    def test_find_split_point_uses_encoder_for_counting(self, mock_encoder):
        """Debería usar el encoder para contar tokens."""
        # Arrange
        mock_encoder.count_tokens.return_value = 5
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            chunk_size=100,
            chunk_overlap=10,
        )
        text = "# Test\n\nContent"

        # Act
        split_point = splitter.find_split_point(text, 100, [])

        # Assert
        mock_encoder.count_tokens.assert_called()

    def test_find_split_point_with_very_long_section(self, mock_encoder):
        """Debería subdividir secciones muy largas."""
        # Arrange
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            chunk_size=20,
            chunk_overlap=5,
        )
        # Sección con muchas palabras
        text = "# Title\n\n" + " ".join(["word"] * 100)
        max_tokens = 20

        # Act
        split_point = splitter.find_split_point(text, max_tokens, [])

        # Assert
        assert split_point > 0
        assert split_point < len(text)

    def test_find_split_point_returns_positive_value(self, mock_encoder):
        """Debería siempre retornar valor no negativo."""
        # Arrange
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            chunk_size=10,
            chunk_overlap=2,
        )
        text = "# Test\n\nSome content"
        max_tokens = 10

        # Act
        split_point = splitter.find_split_point(text, max_tokens, [])

        # Assert
        assert split_point >= 0

    def test_find_split_point_does_not_exceed_text_length(self, mock_encoder):
        """Debería nunca exceder la longitud del texto."""
        # Arrange
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            chunk_size=10,
            chunk_overlap=2,
        )
        text = "# Short\n\nText"
        max_tokens = 10

        # Act
        split_point = splitter.find_split_point(text, max_tokens, [])

        # Assert
        assert split_point <= len(text)

    def test_initialization_with_custom_parameters(self, mock_encoder):
        """Debería inicializar con parámetros personalizados."""
        # Arrange & Act
        splitter = LangChainMarkdownSplitter(
            token_encoder=mock_encoder,
            chunk_size=500,
            chunk_overlap=50,
            encoding_name="p50k_base",
        )

        # Assert
        assert splitter._chunk_size == 500
        assert splitter._chunk_overlap == 50
        assert splitter._encoding_name == "p50k_base"
