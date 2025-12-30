"""Tests para HuggingFaceTokenEncoder."""

from unittest.mock import Mock, patch

import pytest

from src.chunking.infra.external.huggingface_token_encoder import (
    HuggingFaceTokenEncoder,
)


class TestHuggingFaceTokenEncoder:
    """Tests para HuggingFaceTokenEncoder."""

    @pytest.fixture
    def mock_tokenizer(self):
        """Mock tokenizer de HuggingFace."""
        tokenizer = Mock()
        tokenizer.encode.return_value = [9906, 1917]
        tokenizer.decode.return_value = "Hello world"
        tokenizer.name_or_path = "Qwen/Qwen2-VL-7B-Instruct"
        return tokenizer

    @pytest.fixture
    def encoder(self, mock_tokenizer):
        """Encoder con tokenizer mockeado."""
        return HuggingFaceTokenEncoder(mock_tokenizer)

    def test_encode_returns_token_ids(self, encoder, mock_tokenizer):
        """Debería codificar texto a lista de token IDs."""
        # Act
        tokens = encoder.encode("Hello world")

        # Assert
        assert tokens == [9906, 1917]
        mock_tokenizer.encode.assert_called_once_with(
            "Hello world", add_special_tokens=False
        )

    def test_decode_returns_text(self, encoder, mock_tokenizer):
        """Debería decodificar tokens a texto."""
        # Act
        text = encoder.decode([9906, 1917])

        # Assert
        assert text == "Hello world"
        mock_tokenizer.decode.assert_called_once_with(
            [9906, 1917], skip_special_tokens=True
        )

    def test_count_tokens_returns_correct_count(self, encoder, mock_tokenizer):
        """Debería contar tokens correctamente."""
        # Act
        count = encoder.count_tokens("Hello world")

        # Assert
        assert count == 2
        mock_tokenizer.encode.assert_called_once()

    def test_model_name_returns_tokenizer_name(self, encoder):
        """Debería retornar nombre del modelo."""
        # Act
        name = encoder.model_name

        # Assert
        assert name == "Qwen/Qwen2-VL-7B-Instruct"

    def test_model_name_returns_none_when_not_available(self):
        """Debería retornar None si nombre no está disponible."""
        # Arrange
        tokenizer = Mock(spec=[])  # Sin name_or_path
        encoder = HuggingFaceTokenEncoder(tokenizer)

        # Act
        name = encoder.model_name

        # Assert
        assert name is None

    def test_encode_with_empty_string(self, encoder, mock_tokenizer):
        """Debería manejar string vacío."""
        # Arrange
        mock_tokenizer.encode.return_value = []

        # Act
        tokens = encoder.encode("")

        # Assert
        assert tokens == []

    def test_decode_with_empty_list(self, encoder, mock_tokenizer):
        """Debería manejar lista vacía."""
        # Arrange
        mock_tokenizer.decode.return_value = ""

        # Act
        text = encoder.decode([])

        # Assert
        assert text == ""

    def test_count_tokens_with_empty_string(self, encoder, mock_tokenizer):
        """Debería retornar 0 para string vacío."""
        # Arrange
        mock_tokenizer.encode.return_value = []

        # Act
        count = encoder.count_tokens("")

        # Assert
        assert count == 0


class TestHuggingFaceTokenEncoderForModel:
    """Tests para factory method for_model."""

    @patch("src.chunking.infra.external.huggingface_token_encoder.AutoTokenizer")
    def test_for_model_creates_encoder_successfully(self, mock_auto_tokenizer):
        """Debería crear encoder desde nombre de modelo."""
        # Arrange
        mock_tokenizer = Mock()
        mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer

        # Act
        encoder = HuggingFaceTokenEncoder.for_model("Qwen/Qwen2-VL-7B-Instruct")

        # Assert
        assert isinstance(encoder, HuggingFaceTokenEncoder)
        mock_auto_tokenizer.from_pretrained.assert_called_once_with(
            "Qwen/Qwen2-VL-7B-Instruct",
            trust_remote_code=True,
            use_fast=True,
        )

    @patch("src.chunking.infra.external.huggingface_token_encoder.AutoTokenizer")
    def test_for_model_with_custom_parameters(self, mock_auto_tokenizer):
        """Debería pasar parámetros personalizados."""
        # Arrange
        mock_tokenizer = Mock()
        mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer

        # Act
        encoder = HuggingFaceTokenEncoder.for_model(
            "meta-llama/Llama-2-7b-hf",
            trust_remote_code=False,
            use_fast=False,
        )

        # Assert
        assert isinstance(encoder, HuggingFaceTokenEncoder)
        mock_auto_tokenizer.from_pretrained.assert_called_once_with(
            "meta-llama/Llama-2-7b-hf",
            trust_remote_code=False,
            use_fast=False,
        )

    @patch("src.chunking.infra.external.huggingface_token_encoder.AutoTokenizer")
    def test_for_model_raises_on_invalid_model(self, mock_auto_tokenizer):
        """Debería lanzar ValueError si modelo no existe."""
        # Arrange
        mock_auto_tokenizer.from_pretrained.side_effect = Exception("Model not found")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            HuggingFaceTokenEncoder.for_model("invalid/model")

        assert "No se pudo cargar tokenizer" in str(exc_info.value)
        assert "invalid/model" in str(exc_info.value)

    @patch("src.chunking.infra.external.huggingface_token_encoder.AutoTokenizer")
    def test_for_model_qwen3_vl(self, mock_auto_tokenizer):
        """Debería crear encoder para Qwen3-VL."""
        # Arrange
        mock_tokenizer = Mock()
        mock_tokenizer.name_or_path = "Qwen/Qwen2-VL-7B-Instruct"
        mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer

        # Act
        encoder = HuggingFaceTokenEncoder.for_model("Qwen/Qwen2-VL-7B-Instruct")

        # Assert
        assert encoder.model_name == "Qwen/Qwen2-VL-7B-Instruct"


class TestHuggingFaceTokenEncoderIntegration:
    """Tests de integración con texto real."""

    def test_encode_decode_roundtrip(self):
        """Debería mantener texto después de encode/decode."""
        # Arrange
        mock_tokenizer = Mock()
        mock_tokenizer.encode.return_value = [1, 2, 3]
        mock_tokenizer.decode.return_value = "test text"
        encoder = HuggingFaceTokenEncoder(mock_tokenizer)

        # Act
        tokens = encoder.encode("test text")
        decoded = encoder.decode(tokens)

        # Assert
        assert decoded == "test text"

    def test_count_tokens_matches_encode_length(self):
        """Debería contar tokens igual que longitud de encode."""
        # Arrange
        mock_tokenizer = Mock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        encoder = HuggingFaceTokenEncoder(mock_tokenizer)

        # Act
        count = encoder.count_tokens("some text")
        tokens = encoder.encode("some text")

        # Assert
        assert count == len(tokens)
        assert count == 5
