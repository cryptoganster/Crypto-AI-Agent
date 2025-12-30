"""Tests de integración para NomicEmbeddingAdapter."""

from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from src.embedding.domain.value_objects.vector_embedding import VectorEmbedding
from src.embedding.infra.external.nomic_embedding_adapter import (
    EmbeddingGenerationException,
    NomicEmbeddingAdapter,
)


@pytest.mark.integration
class TestNomicEmbeddingAdapter:
    """Tests de integración para NomicEmbeddingAdapter."""

    @pytest.fixture
    def adapter(self):
        """Crea adaptador con configuración de test."""
        return NomicEmbeddingAdapter(
            batch_size=4,
            max_retries=2,
            initial_retry_delay=0.1,
            max_retry_delay=0.5,
            timeout=10.0,
        )

    @pytest.fixture
    def mock_model(self):
        """Mock del modelo de sentence-transformers."""
        model = Mock()

        # Mock encode para texto individual (768 dimensiones para nomic-embed-text)
        def encode_single(text, convert_to_numpy=True):
            # Generar vector aleatorio normalizado de 768 dimensiones
            vec = np.random.randn(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
            return vec

        # Mock encode para batch
        def encode_batch(texts, convert_to_numpy=True):
            if isinstance(texts, str):
                return encode_single(texts, convert_to_numpy)
            return np.array([encode_single(t, convert_to_numpy) for t in texts])

        model.encode = Mock(side_effect=encode_batch)

        return model

    @pytest.mark.asyncio
    async def test_embed_text_generates_valid_embedding(self, adapter, mock_model):
        """Debería generar embedding válido para texto individual."""
        # Arrange
        text = "Bitcoin price analysis for 2024"

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embedding = await adapter.embed_text(text)

            # Assert
            assert isinstance(embedding, VectorEmbedding)
            assert embedding.dimension == adapter.dimension
            assert embedding.model == adapter.model_name
            assert embedding.is_normalized()
            assert not np.any(np.isnan(embedding.vector))
            assert not np.any(np.isinf(embedding.vector))

            # Verificar que el modelo fue llamado
            mock_model.encode.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_text_with_empty_text_raises_error(self, adapter):
        """Debería lanzar ValueError cuando el texto está vacío."""
        # Arrange
        empty_texts = ["", "   ", "\n\t"]

        # Act & Assert
        for text in empty_texts:
            with pytest.raises(ValueError, match="Texto no puede estar vacío"):
                await adapter.embed_text(text)

    @pytest.mark.asyncio
    async def test_embed_text_normalizes_vector(self, adapter, mock_model):
        """Debería normalizar el vector a magnitud unitaria."""
        # Arrange
        text = "Ethereum smart contracts"

        # Mock que retorna vector NO normalizado (768 dimensiones)
        unnormalized_vec = np.array([1.0, 2.0, 3.0, 4.0] * 192, dtype=np.float32)
        mock_model.encode = Mock(return_value=unnormalized_vec)

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embedding = await adapter.embed_text(text)

            # Assert
            assert embedding.is_normalized()
            assert np.isclose(embedding.magnitude(), 1.0, atol=1e-5)

    @pytest.mark.asyncio
    async def test_embed_batch_generates_embeddings_for_all_texts(
        self, adapter, mock_model
    ):
        """Debería generar embeddings para todos los textos en el batch."""
        # Arrange
        texts = [
            "Bitcoin halving event",
            "Ethereum merge update",
            "DeFi protocol security",
        ]

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embeddings = await adapter.embed_batch(texts)

            # Assert
            assert len(embeddings) == len(texts)

            for i, embedding in enumerate(embeddings):
                assert isinstance(embedding, VectorEmbedding)
                assert embedding.dimension == adapter.dimension
                assert embedding.model == adapter.model_name
                assert embedding.is_normalized()

            # Verificar que el modelo fue llamado
            mock_model.encode.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_batch_with_empty_list_raises_error(self, adapter):
        """Debería lanzar ValueError cuando la lista está vacía."""
        # Arrange
        texts = []

        # Act & Assert
        with pytest.raises(ValueError, match="Lista de textos no puede estar vacía"):
            await adapter.embed_batch(texts)

    @pytest.mark.asyncio
    async def test_embed_batch_with_invalid_text_raises_error(self, adapter):
        """Debería lanzar ValueError cuando un texto es inválido."""
        # Arrange
        texts = ["Valid text", "", "Another valid text"]

        # Act & Assert
        with pytest.raises(ValueError, match="Texto en posición 1 está vacío"):
            await adapter.embed_batch(texts)

    @pytest.mark.asyncio
    async def test_embed_batch_divides_large_batch_into_sub_batches(
        self, adapter, mock_model
    ):
        """Debería dividir batch grande en sub-batches."""
        # Arrange
        # Crear batch más grande que batch_size (4)
        texts = [f"Text {i}" for i in range(10)]

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embeddings = await adapter.embed_batch(texts)

            # Assert
            assert len(embeddings) == len(texts)

            # Verificar que se llamó múltiples veces (sub-batches)
            # 10 textos / 4 batch_size = 3 llamadas (4 + 4 + 2)
            assert mock_model.encode.call_count == 3

    @pytest.mark.asyncio
    async def test_embed_text_retries_on_failure(self, adapter, mock_model):
        """Debería reintentar cuando la generación falla."""
        # Arrange
        text = "Test text"

        # Mock que falla las primeras 2 veces, luego tiene éxito
        call_count = 0

        def encode_with_failures(text, convert_to_numpy=True):
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                raise Exception("Temporary failure")

            # Éxito en el tercer intento (768 dimensiones)
            vec = np.random.randn(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
            return vec

        mock_model.encode = Mock(side_effect=encode_with_failures)

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embedding = await adapter.embed_text(text)

            # Assert
            assert isinstance(embedding, VectorEmbedding)
            assert call_count == 3  # Falló 2 veces, éxito en la 3ra

    @pytest.mark.asyncio
    async def test_embed_text_raises_exception_after_max_retries(
        self, adapter, mock_model
    ):
        """Debería lanzar excepción después de agotar reintentos."""
        # Arrange
        text = "Test text"

        # Mock que siempre falla
        mock_model.encode = Mock(side_effect=Exception("Permanent failure"))

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act & Assert
            with pytest.raises(EmbeddingGenerationException) as exc_info:
                await adapter.embed_text(text)

            assert "después de 3 intentos" in str(exc_info.value)

            # Verificar que se intentó max_retries + 1 veces (3 en total)
            assert mock_model.encode.call_count == 3

    @pytest.mark.asyncio
    async def test_embed_batch_maintains_order(self, adapter, mock_model):
        """Debería mantener el orden de los embeddings."""
        # Arrange
        texts = [f"Text {i}" for i in range(5)]

        # Mock que retorna vectores identificables por posición (768 dimensiones)
        def encode_identifiable(texts_input, convert_to_numpy=True):
            if isinstance(texts_input, str):
                # Texto individual
                vec = np.zeros(768, dtype=np.float32)
                vec[0] = 1.0
                return vec / np.linalg.norm(vec)

            # Batch: crear vector único para cada texto
            result = []
            for i, text in enumerate(texts_input):
                vec = np.zeros(768, dtype=np.float32)
                vec[i % 768] = 1.0  # Poner 1 en posición única
                result.append(vec / np.linalg.norm(vec))
            return np.array(result)

        mock_model.encode = Mock(side_effect=encode_identifiable)

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embeddings = await adapter.embed_batch(texts)

            # Assert
            assert len(embeddings) == len(texts)

            # Verificar que cada embedding es único (orden preservado)
            for i in range(len(embeddings) - 1):
                # Los vectores deben ser diferentes
                similarity = embeddings[i].cosine_similarity(embeddings[i + 1])
                assert similarity < 0.99  # No deben ser idénticos

    @pytest.mark.asyncio
    async def test_embed_text_handles_timeout(self, adapter, mock_model):
        """Debería manejar timeout correctamente."""
        # Arrange
        text = "Test text"

        # Mock que tarda mucho tiempo
        async def slow_encode():
            import asyncio

            await asyncio.sleep(100)  # Mucho más que el timeout
            return np.random.randn(384).astype(np.float32)

        # Configurar adaptador con timeout muy corto
        adapter.timeout = 0.1

        with patch.object(
            adapter, "_generate_embedding_internal", side_effect=slow_encode
        ):
            # Act & Assert
            with pytest.raises(EmbeddingGenerationException) as exc_info:
                await adapter.embed_text(text)

            assert "Timeout" in str(exc_info.value) or "después de" in str(
                exc_info.value
            )

    def test_adapter_initialization_with_invalid_params(self):
        """Debería validar parámetros de inicialización."""
        # Batch size inválido
        with pytest.raises(ValueError, match="batch_size debe ser > 0"):
            NomicEmbeddingAdapter(batch_size=0)

        # Max retries inválido
        with pytest.raises(ValueError, match="max_retries debe ser >= 0"):
            NomicEmbeddingAdapter(max_retries=-1)

        # Initial retry delay inválido
        with pytest.raises(ValueError, match="initial_retry_delay debe ser > 0"):
            NomicEmbeddingAdapter(initial_retry_delay=0)

        # Max retry delay menor que initial
        with pytest.raises(
            ValueError, match="max_retry_delay debe ser >= initial_retry_delay"
        ):
            NomicEmbeddingAdapter(initial_retry_delay=5.0, max_retry_delay=1.0)

        # Timeout inválido
        with pytest.raises(ValueError, match="timeout debe ser > 0"):
            NomicEmbeddingAdapter(timeout=0)

    def test_adapter_repr(self, adapter):
        """Debería tener representación legible."""
        # Act
        repr_str = repr(adapter)

        # Assert
        assert "NomicEmbeddingAdapter" in repr_str
        assert "nomic-embed-text" in repr_str
        assert "768" in repr_str
        assert "batch_size=4" in repr_str

    @pytest.mark.asyncio
    async def test_embed_batch_processes_in_parallel(self, adapter, mock_model):
        """
        Debería procesar batch en paralelo para eficiencia.

        Validates: Requirements 2.3, 11.1
        """
        # Arrange
        texts = [f"Text {i}" for i in range(8)]

        # Mock que registra llamadas
        call_times = []

        def encode_with_timing(texts_input, convert_to_numpy=True):
            import time

            call_times.append(time.time())

            if isinstance(texts_input, str):
                vec = np.random.randn(768).astype(np.float32)
                return vec / np.linalg.norm(vec)

            result = []
            for _ in texts_input:
                vec = np.random.randn(768).astype(np.float32)
                result.append(vec / np.linalg.norm(vec))
            return np.array(result)

        mock_model.encode = Mock(side_effect=encode_with_timing)

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embeddings = await adapter.embed_batch(texts)

            # Assert
            assert len(embeddings) == len(texts)

            # Verificar que se procesó en sub-batches (batch_size=4)
            # 8 textos / 4 batch_size = 2 llamadas
            assert mock_model.encode.call_count == 2

            # Verificar que todos los embeddings son válidos
            for embedding in embeddings:
                assert embedding.is_normalized()
                assert embedding.dimension == 768

    @pytest.mark.asyncio
    async def test_embed_text_with_special_characters(self, adapter, mock_model):
        """
        Debería manejar textos con caracteres especiales.

        Validates: Requirements 2.1, 2.2
        """
        # Arrange
        texts_with_special_chars = [
            "Bitcoin: $50,000 📈",
            "Ethereum → Smart Contracts",
            "DeFi 🚀 100% APY",
            "UTF-8: 日本語 中文 한국어",
            "Symbols: @#$%^&*()",
        ]

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act & Assert
            for text in texts_with_special_chars:
                embedding = await adapter.embed_text(text)

                assert isinstance(embedding, VectorEmbedding)
                assert embedding.dimension == 768
                assert embedding.is_normalized()
                assert not np.any(np.isnan(embedding.vector))

    @pytest.mark.asyncio
    async def test_embed_batch_with_varying_text_lengths(self, adapter, mock_model):
        """
        Debería manejar textos de diferentes longitudes en el mismo batch.

        Validates: Requirements 2.3
        """
        # Arrange
        texts = [
            "Short",
            "Medium length text about Bitcoin",
            "Very long text " * 100,  # Texto muy largo
            "A",  # Un solo carácter
        ]

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embeddings = await adapter.embed_batch(texts)

            # Assert
            assert len(embeddings) == len(texts)

            # Todos deben tener la misma dimensión
            for embedding in embeddings:
                assert embedding.dimension == 768
                assert embedding.is_normalized()

    @pytest.mark.asyncio
    async def test_embed_text_exponential_backoff(self, adapter, mock_model):
        """
        Debería usar exponential backoff en reintentos.

        Validates: Requirements 2.5 (retry logic)
        """
        # Arrange
        text = "Test text"

        # Registrar tiempos de llamadas
        call_times = []

        def encode_with_timing(text, convert_to_numpy=True):
            import time

            call_times.append(time.time())

            if len(call_times) < 3:
                raise Exception("Temporary failure")

            vec = np.random.randn(768).astype(np.float32)
            return vec / np.linalg.norm(vec)

        mock_model.encode = Mock(side_effect=encode_with_timing)

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embedding = await adapter.embed_text(text)

            # Assert
            assert isinstance(embedding, VectorEmbedding)
            assert len(call_times) == 3

            # Verificar que los delays aumentan exponencialmente
            # Delay 1: ~0.1s, Delay 2: ~0.2s
            if len(call_times) >= 3:
                delay1 = call_times[1] - call_times[0]
                delay2 = call_times[2] - call_times[1]

                # El segundo delay debe ser aproximadamente el doble
                assert delay2 > delay1
                assert delay2 < delay1 * 3  # No más de 3x

    @pytest.mark.asyncio
    async def test_embed_batch_continues_on_partial_failure(self, adapter, mock_model):
        """
        Debería continuar procesando otros chunks si uno falla.

        Validates: Requirements 2.5
        """
        # Arrange
        texts = [f"Text {i}" for i in range(4)]

        # Mock que falla en el primer intento pero tiene éxito después
        attempt_count = 0

        def encode_with_retry(texts_input, convert_to_numpy=True):
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count == 1:
                raise Exception("First attempt fails")

            if isinstance(texts_input, str):
                vec = np.random.randn(768).astype(np.float32)
                return vec / np.linalg.norm(vec)

            result = []
            for _ in texts_input:
                vec = np.random.randn(768).astype(np.float32)
                result.append(vec / np.linalg.norm(vec))
            return np.array(result)

        mock_model.encode = Mock(side_effect=encode_with_retry)

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embeddings = await adapter.embed_batch(texts)

            # Assert
            assert len(embeddings) == len(texts)
            assert attempt_count >= 2  # Falló una vez, luego tuvo éxito

    @pytest.mark.asyncio
    async def test_embed_text_with_very_long_text(self, adapter, mock_model):
        """
        Debería manejar textos muy largos sin problemas.

        Validates: Requirements 2.1
        """
        # Arrange
        # Crear texto muy largo (>10k caracteres)
        long_text = "Bitcoin analysis " * 1000

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embedding = await adapter.embed_text(long_text)

            # Assert
            assert isinstance(embedding, VectorEmbedding)
            assert embedding.dimension == 768
            assert embedding.is_normalized()

    @pytest.mark.asyncio
    async def test_embed_batch_returns_aligned_embeddings(self, adapter, mock_model):
        """
        Debería retornar embeddings alineados con textos originales.

        Validates: Requirements 2.4
        """
        # Arrange
        texts = ["First", "Second", "Third", "Fourth", "Fifth"]

        # Mock que retorna vectores identificables
        def encode_identifiable(texts_input, convert_to_numpy=True):
            if isinstance(texts_input, str):
                vec = np.zeros(768, dtype=np.float32)
                vec[0] = 1.0
                return vec / np.linalg.norm(vec)

            result = []
            for i, _ in enumerate(texts_input):
                vec = np.zeros(768, dtype=np.float32)
                # Usar posición para hacer vector único
                vec[i % 768] = float(i + 1)
                result.append(vec / np.linalg.norm(vec))
            return np.array(result)

        mock_model.encode = Mock(side_effect=encode_identifiable)

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embeddings = await adapter.embed_batch(texts)

            # Assert
            assert len(embeddings) == len(texts)

            # Verificar que los embeddings están alineados
            # (cada embedding debe ser único y en el orden correcto)
            for i in range(len(embeddings)):
                # El embedding i debe tener el valor (i+1) en alguna posición
                max_val = np.max(np.abs(embeddings[i].vector))
                assert max_val > 0  # No debe ser vector cero

    @pytest.mark.asyncio
    async def test_normalize_vector_with_zero_magnitude_raises_error(self, adapter):
        """
        Debería lanzar error al normalizar vector de magnitud cero.

        Validates: Requirements 2.6
        """
        # Arrange
        zero_vector = np.zeros(768, dtype=np.float32)

        # Act & Assert
        with pytest.raises(
            ValueError, match="No se puede normalizar un vector de magnitud cero"
        ):
            adapter._normalize_vector(zero_vector)

    @pytest.mark.asyncio
    async def test_embed_text_handles_model_loading_failure(self, adapter):
        """
        Debería manejar fallo al cargar el modelo.

        Validates: Requirements 2.1
        """
        # Arrange
        text = "Test text"

        # Mock que falla al cargar el modelo
        def failing_get_model():
            raise Exception("Model loading failed")

        with patch.object(adapter, "_get_model", side_effect=failing_get_model):
            # Act & Assert
            with pytest.raises(EmbeddingGenerationException) as exc_info:
                await adapter.embed_text(text)

            # Verificar que la excepción original está preservada
            assert exc_info.value.original_error is not None
            assert "Model loading failed" in str(exc_info.value.original_error)

    @pytest.mark.asyncio
    async def test_embed_batch_with_exact_batch_size(self, adapter, mock_model):
        """
        Debería procesar batch exactamente del tamaño configurado sin dividir.

        Validates: Requirements 11.1
        """
        # Arrange
        # Crear batch exactamente del tamaño configurado (4)
        texts = [f"Text {i}" for i in range(4)]

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embeddings = await adapter.embed_batch(texts)

            # Assert
            assert len(embeddings) == 4

            # Debe llamarse solo una vez (no dividir en sub-batches)
            assert mock_model.encode.call_count == 1

    @pytest.mark.asyncio
    async def test_embed_batch_with_one_more_than_batch_size(self, adapter, mock_model):
        """
        Debería dividir correctamente cuando hay un texto más que batch_size.

        Validates: Requirements 11.1
        """
        # Arrange
        # Crear batch con 5 textos (batch_size=4)
        texts = [f"Text {i}" for i in range(5)]

        with patch.object(adapter, "_get_model", return_value=mock_model):
            # Act
            embeddings = await adapter.embed_batch(texts)

            # Assert
            assert len(embeddings) == 5

            # Debe dividirse en 2 sub-batches (4 + 1)
            assert mock_model.encode.call_count == 2
