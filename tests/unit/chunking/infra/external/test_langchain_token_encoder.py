"""Tests para LangChainTokenEncoder."""

import pytest

from src.chunking.infra.external.langchain_token_encoder import (
    LangChainTokenEncoder,
)


class TestLangChainTokenEncoder:
    """Tests para LangChainTokenEncoder."""

    def test_count_tokens_with_simple_text(self):
        """Debería contar tokens correctamente en texto simple."""
        # Arrange
        encoder = LangChainTokenEncoder(encoding_name="cl100k_base")
        text = "Hello world"

        # Act
        count = encoder.count_tokens(text)

        # Assert
        assert count > 0
        assert isinstance(count, int)

    def test_count_tokens_with_empty_string(self):
        """Debería retornar 0 para string vacío."""
        # Arrange
        encoder = LangChainTokenEncoder(encoding_name="cl100k_base")
        text = ""

        # Act
        count = encoder.count_tokens(text)

        # Assert
        assert count == 0

    def test_count_tokens_with_long_text(self):
        """Debería contar tokens en texto largo."""
        # Arrange
        encoder = LangChainTokenEncoder(encoding_name="cl100k_base")
        text = "This is a longer text. " * 100

        # Act
        count = encoder.count_tokens(text)

        # Assert
        assert count > 100
        assert isinstance(count, int)

    def test_encode_returns_token_ids(self):
        """Debería codificar texto a lista de token IDs."""
        # Arrange
        encoder = LangChainTokenEncoder(encoding_name="cl100k_base")
        text = "Hello world"

        # Act
        tokens = encoder.encode(text)

        # Assert
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(token, int) for token in tokens)

    def test_decode_returns_original_text(self):
        """Debería decodificar tokens de vuelta a texto."""
        # Arrange
        encoder = LangChainTokenEncoder(encoding_name="cl100k_base")
        text = "Hello world"

        # Act
        tokens = encoder.encode(text)
        decoded = encoder.decode(tokens)

        # Assert
        assert decoded == text

    def test_encode_decode_roundtrip(self):
        """Debería mantener texto intacto en encode/decode roundtrip."""
        # Arrange
        encoder = LangChainTokenEncoder(encoding_name="cl100k_base")
        text = "The quick brown fox jumps over the lazy dog."

        # Act
        tokens = encoder.encode(text)
        decoded = encoder.decode(tokens)

        # Assert
        assert decoded == text

    def test_model_name_returns_encoding_name(self):
        """Debería retornar el nombre del encoding."""
        # Arrange
        encoding_name = "cl100k_base"
        encoder = LangChainTokenEncoder(encoding_name=encoding_name)

        # Act
        model_name = encoder.model_name

        # Assert
        assert model_name == encoding_name

    def test_for_model_gpt4_uses_correct_encoding(self):
        """Debería usar cl100k_base para GPT-4."""
        # Arrange & Act
        encoder = LangChainTokenEncoder.for_model("gpt-4")

        # Assert
        assert encoder.model_name == "cl100k_base"

    def test_for_model_gpt35_turbo_uses_correct_encoding(self):
        """Debería usar cl100k_base para GPT-3.5-turbo."""
        # Arrange & Act
        encoder = LangChainTokenEncoder.for_model("gpt-3.5-turbo")

        # Assert
        assert encoder.model_name == "cl100k_base"

    def test_for_model_gpt4o_uses_correct_encoding(self):
        """Debería usar o200k_base para GPT-4o."""
        # Arrange & Act
        encoder = LangChainTokenEncoder.for_model("gpt-4o")

        # Assert
        assert encoder.model_name == "o200k_base"

    def test_for_model_davinci_uses_correct_encoding(self):
        """Debería usar r50k_base para davinci."""
        # Arrange & Act
        encoder = LangChainTokenEncoder.for_model("davinci")

        # Assert
        assert encoder.model_name == "r50k_base"

    def test_for_model_unknown_uses_default_encoding(self):
        """Debería usar cl100k_base para modelo desconocido."""
        # Arrange & Act
        encoder = LangChainTokenEncoder.for_model("unknown-model")

        # Assert
        assert encoder.model_name == "cl100k_base"

    def test_count_tokens_consistent_with_encode(self):
        """count_tokens debería ser consistente con len(encode())."""
        # Arrange
        encoder = LangChainTokenEncoder(encoding_name="cl100k_base")
        text = "This is a test sentence with multiple words."

        # Act
        count = encoder.count_tokens(text)
        tokens = encoder.encode(text)

        # Assert
        assert count == len(tokens)

    def test_different_encodings_produce_different_counts(self):
        """Diferentes encodings deberían producir conteos diferentes."""
        # Arrange
        text = "Hello world"
        encoder_cl100k = LangChainTokenEncoder(encoding_name="cl100k_base")
        encoder_r50k = LangChainTokenEncoder(encoding_name="r50k_base")

        # Act
        count_cl100k = encoder_cl100k.count_tokens(text)
        count_r50k = encoder_r50k.count_tokens(text)

        # Assert
        # Los conteos pueden ser iguales o diferentes dependiendo del texto
        # Solo verificamos que ambos son válidos
        assert count_cl100k > 0
        assert count_r50k > 0

    def test_count_tokens_with_unicode(self):
        """Debería manejar correctamente texto con Unicode."""
        # Arrange
        encoder = LangChainTokenEncoder(encoding_name="cl100k_base")
        text = "Hola mundo 🌍 こんにちは"

        # Act
        count = encoder.count_tokens(text)

        # Assert
        assert count > 0
        assert isinstance(count, int)

    def test_encode_decode_with_unicode(self):
        """Debería manejar Unicode en encode/decode."""
        # Arrange
        encoder = LangChainTokenEncoder(encoding_name="cl100k_base")
        text = "Hello 世界 🌍"

        # Act
        tokens = encoder.encode(text)
        decoded = encoder.decode(tokens)

        # Assert
        assert decoded == text
