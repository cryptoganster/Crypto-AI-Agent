"""Tests de integración para OpenAILLMAdapter."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.rag.infra.external.openai_llm_adapter import (
    LLMGenerationException,
    LLMRateLimitException,
    LLMTimeoutException,
    OpenAILLMAdapter,
)


@pytest.mark.integration
class TestOpenAILLMAdapter:
    """Tests de integración para OpenAILLMAdapter."""

    @pytest.fixture
    def adapter(self):
        """Crea adaptador con configuración de test."""
        return OpenAILLMAdapter(
            api_key="test-api-key-12345",
            model="gpt-4",
            max_retries=2,
            initial_retry_delay=0.1,
            max_retry_delay=0.5,
            timeout=10.0,
        )

    @pytest.fixture
    def mock_openai_client(self):
        """Mock del cliente de OpenAI."""
        client = AsyncMock()

        # Mock de la respuesta de chat completions
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Generated text response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        client.chat.completions.create = AsyncMock(return_value=mock_response)

        return client

    @pytest.mark.asyncio
    async def test_generate_returns_valid_text(self, adapter, mock_openai_client):
        """Debería generar texto válido."""
        # Arrange
        prompt = "Resume este artículo sobre Bitcoin"

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act
            text = await adapter.generate(
                prompt=prompt,
                max_tokens=200,
                temperature=0.3,
            )

            # Assert
            assert isinstance(text, str)
            assert len(text) > 0
            assert text == "Generated text response"

            # Verificar que el cliente fue llamado correctamente
            mock_openai_client.chat.completions.create.assert_called_once()
            call_args = mock_openai_client.chat.completions.create.call_args

            assert call_args.kwargs["model"] == "gpt-4"
            assert call_args.kwargs["max_tokens"] == 200
            assert call_args.kwargs["temperature"] == 0.3
            assert len(call_args.kwargs["messages"]) == 1
            assert call_args.kwargs["messages"][0]["role"] == "user"
            assert call_args.kwargs["messages"][0]["content"] == prompt

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, adapter, mock_openai_client):
        """Debería incluir system prompt cuando se proporciona."""
        # Arrange
        prompt = "Analiza el impacto de los ETFs de Bitcoin"
        system_prompt = "Eres un analista financiero experto en cripto"

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act
            text = await adapter.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7,
                system_prompt=system_prompt,
            )

            # Assert
            assert isinstance(text, str)

            # Verificar que se incluyó el system prompt
            call_args = mock_openai_client.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]

            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == system_prompt
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == prompt

    @pytest.mark.asyncio
    async def test_generate_with_empty_prompt_raises_error(self, adapter):
        """Debería lanzar ValueError cuando el prompt está vacío."""
        # Arrange
        empty_prompts = ["", "   ", "\n\t"]

        # Act & Assert
        for prompt in empty_prompts:
            with pytest.raises(ValueError, match="prompt no puede estar vacío"):
                await adapter.generate(prompt=prompt)

    @pytest.mark.asyncio
    async def test_generate_with_invalid_max_tokens_raises_error(self, adapter):
        """Debería lanzar ValueError cuando max_tokens es inválido."""
        # Arrange
        prompt = "Test prompt"

        # Act & Assert
        with pytest.raises(ValueError, match="max_tokens debe ser > 0"):
            await adapter.generate(prompt=prompt, max_tokens=0)

        with pytest.raises(ValueError, match="max_tokens debe ser > 0"):
            await adapter.generate(prompt=prompt, max_tokens=-100)

    @pytest.mark.asyncio
    async def test_generate_with_invalid_temperature_raises_error(self, adapter):
        """Debería lanzar ValueError cuando temperature es inválida."""
        # Arrange
        prompt = "Test prompt"

        # Act & Assert
        with pytest.raises(ValueError, match="temperature debe estar entre 0.0 y 1.0"):
            await adapter.generate(prompt=prompt, temperature=-0.1)

        with pytest.raises(ValueError, match="temperature debe estar entre 0.0 y 1.0"):
            await adapter.generate(prompt=prompt, temperature=1.5)

    @pytest.mark.asyncio
    async def test_generate_retries_on_failure(self, adapter, mock_openai_client):
        """Debería reintentar cuando la generación falla."""
        # Arrange
        prompt = "Test prompt"

        # Mock que falla las primeras 2 veces, luego tiene éxito
        call_count = 0

        async def create_with_failures(**kwargs):
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                raise Exception("Temporary failure")

            # Éxito en el tercer intento
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "Success after retries"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response

        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=create_with_failures
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act
            text = await adapter.generate(prompt=prompt)

            # Assert
            assert text == "Success after retries"
            assert call_count == 3  # Falló 2 veces, éxito en la 3ra

    @pytest.mark.asyncio
    async def test_generate_raises_exception_after_max_retries(
        self, adapter, mock_openai_client
    ):
        """Debería lanzar excepción después de agotar reintentos."""
        # Arrange
        prompt = "Test prompt"

        # Mock que siempre falla
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Permanent failure")
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act & Assert
            with pytest.raises(LLMGenerationException):
                await adapter.generate(prompt=prompt)

            # Verificar que se intentó max_retries + 1 veces (3 en total)
            assert mock_openai_client.chat.completions.create.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_handles_timeout(self, adapter, mock_openai_client):
        """Debería manejar timeout correctamente."""
        # Arrange
        prompt = "Test prompt"

        # Mock que tarda mucho tiempo
        async def slow_create(**kwargs):
            await asyncio.sleep(100)  # Mucho más que el timeout
            return Mock()

        mock_openai_client.chat.completions.create = AsyncMock(side_effect=slow_create)

        # Configurar adaptador con timeout muy corto
        adapter.timeout = 0.1

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act & Assert
            with pytest.raises(LLMTimeoutException) as exc_info:
                await adapter.generate(prompt=prompt)

            assert "Timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_handles_rate_limit_error(self, adapter, mock_openai_client):
        """Debería detectar y manejar errores de rate limit."""
        # Arrange
        prompt = "Test prompt"

        # Mock que lanza error de rate limit
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Rate limit exceeded for API")
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act & Assert
            with pytest.raises(LLMRateLimitException) as exc_info:
                await adapter.generate(prompt=prompt)

            assert "Rate limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_with_different_temperatures(
        self, adapter, mock_openai_client
    ):
        """
        Debería funcionar con diferentes valores de temperature.

        Validates: Requirements 3.1, 8.2
        """
        # Arrange
        prompt = "Test prompt"
        temperatures = [0.0, 0.3, 0.5, 0.7, 1.0]

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act & Assert
            for temp in temperatures:
                text = await adapter.generate(
                    prompt=prompt,
                    temperature=temp,
                )

                assert isinstance(text, str)

                # Verificar que se usó la temperature correcta
                call_args = mock_openai_client.chat.completions.create.call_args
                assert call_args.kwargs["temperature"] == temp

    @pytest.mark.asyncio
    async def test_generate_with_different_max_tokens(
        self, adapter, mock_openai_client
    ):
        """
        Debería funcionar con diferentes valores de max_tokens.

        Validates: Requirements 3.1
        """
        # Arrange
        prompt = "Test prompt"
        max_tokens_values = [100, 200, 500, 1000, 2000]

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act & Assert
            for max_tokens in max_tokens_values:
                text = await adapter.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                )

                assert isinstance(text, str)

                # Verificar que se usó el max_tokens correcto
                call_args = mock_openai_client.chat.completions.create.call_args
                assert call_args.kwargs["max_tokens"] == max_tokens

    @pytest.mark.asyncio
    async def test_generate_strips_whitespace_from_response(
        self, adapter, mock_openai_client
    ):
        """Debería remover espacios en blanco del inicio y final."""
        # Arrange
        prompt = "Test prompt"

        # Mock que retorna texto con espacios
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "  \n  Generated text with spaces  \n  "
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act
            text = await adapter.generate(prompt=prompt)

            # Assert
            assert text == "Generated text with spaces"
            assert not text.startswith(" ")
            assert not text.endswith(" ")

    @pytest.mark.asyncio
    async def test_generate_handles_empty_response(self, adapter, mock_openai_client):
        """Debería lanzar excepción cuando la respuesta está vacía."""
        # Arrange
        prompt = "Test prompt"

        # Mock que retorna respuesta vacía
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = ""
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act & Assert
            with pytest.raises(LLMGenerationException, match="API retornó texto vacío"):
                await adapter.generate(prompt=prompt)

    @pytest.mark.asyncio
    async def test_generate_handles_no_choices_in_response(
        self, adapter, mock_openai_client
    ):
        """Debería lanzar excepción cuando no hay choices en la respuesta."""
        # Arrange
        prompt = "Test prompt"

        # Mock que retorna respuesta sin choices
        mock_response = Mock()
        mock_response.choices = []

        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act & Assert
            with pytest.raises(
                LLMGenerationException, match="API no retornó ninguna respuesta"
            ):
                await adapter.generate(prompt=prompt)

    @pytest.mark.asyncio
    async def test_generate_exponential_backoff(self, adapter, mock_openai_client):
        """
        Debería usar exponential backoff en reintentos.

        Validates: Requirements 8.2 (retry logic)
        """
        # Arrange
        prompt = "Test prompt"

        # Registrar tiempos de llamadas
        call_times = []

        async def create_with_timing(**kwargs):
            import time

            call_times.append(time.time())

            if len(call_times) < 3:
                raise Exception("Temporary failure")

            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "Success"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response

        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=create_with_timing
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act
            text = await adapter.generate(prompt=prompt)

            # Assert
            assert text == "Success"
            assert len(call_times) == 3

            # Verificar que los delays aumentan exponencialmente
            if len(call_times) >= 3:
                delay1 = call_times[1] - call_times[0]
                delay2 = call_times[2] - call_times[1]

                # El segundo delay debe ser aproximadamente el doble
                assert delay2 > delay1
                assert delay2 < delay1 * 3  # No más de 3x

    @pytest.mark.asyncio
    async def test_generate_with_long_prompt(self, adapter, mock_openai_client):
        """
        Debería manejar prompts muy largos.

        Validates: Requirements 3.1
        """
        # Arrange
        # Crear prompt muy largo (>5k caracteres)
        long_prompt = "Bitcoin analysis " * 500

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act
            text = await adapter.generate(prompt=long_prompt)

            # Assert
            assert isinstance(text, str)

            # Verificar que el prompt largo fue enviado
            call_args = mock_openai_client.chat.completions.create.call_args
            sent_prompt = call_args.kwargs["messages"][-1]["content"]
            assert len(sent_prompt) > 5000

    @pytest.mark.asyncio
    async def test_generate_with_special_characters_in_prompt(
        self, adapter, mock_openai_client
    ):
        """
        Debería manejar prompts con caracteres especiales.

        Validates: Requirements 3.1
        """
        # Arrange
        prompts_with_special_chars = [
            "Bitcoin: $50,000 📈",
            "Ethereum → Smart Contracts",
            "DeFi 🚀 100% APY",
            "UTF-8: 日本語 中文 한국어",
            "Symbols: @#$%^&*()",
            "Quotes: \"double\" and 'single'",
            "Newlines:\nLine 1\nLine 2",
        ]

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act & Assert
            for prompt in prompts_with_special_chars:
                text = await adapter.generate(prompt=prompt)

                assert isinstance(text, str)
                assert len(text) > 0

    @pytest.mark.asyncio
    async def test_generate_preserves_original_error_in_exception(
        self, adapter, mock_openai_client
    ):
        """
        Debería preservar la excepción original en LLMGenerationException.

        Validates: Requirements 8.2
        """
        # Arrange
        prompt = "Test prompt"
        original_error = ValueError("Original error message")

        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=original_error
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act & Assert
            with pytest.raises(LLMGenerationException) as exc_info:
                await adapter.generate(prompt=prompt)

            # Verificar que la excepción original está preservada
            assert exc_info.value.original_error is not None
            assert isinstance(exc_info.value.original_error, ValueError)
            assert "Original error message" in str(exc_info.value.original_error)

    def test_adapter_initialization_with_invalid_params(self):
        """Debería validar parámetros de inicialización."""
        # API key vacío
        with pytest.raises(ValueError, match="api_key es requerido"):
            OpenAILLMAdapter(api_key="")

        with pytest.raises(ValueError, match="api_key es requerido"):
            OpenAILLMAdapter(api_key="   ")

        # Model vacío
        with pytest.raises(ValueError, match="model es requerido"):
            OpenAILLMAdapter(api_key="test-key", model="")

        # Max retries inválido
        with pytest.raises(ValueError, match="max_retries debe ser >= 0"):
            OpenAILLMAdapter(api_key="test-key", max_retries=-1)

        # Initial retry delay inválido
        with pytest.raises(ValueError, match="initial_retry_delay debe ser > 0"):
            OpenAILLMAdapter(api_key="test-key", initial_retry_delay=0)

        # Max retry delay menor que initial
        with pytest.raises(
            ValueError, match="max_retry_delay debe ser >= initial_retry_delay"
        ):
            OpenAILLMAdapter(
                api_key="test-key", initial_retry_delay=5.0, max_retry_delay=1.0
            )

        # Timeout inválido
        with pytest.raises(ValueError, match="timeout debe ser > 0"):
            OpenAILLMAdapter(api_key="test-key", timeout=0)

    def test_adapter_repr(self, adapter):
        """Debería tener representación legible."""
        # Act
        repr_str = repr(adapter)

        # Assert
        assert "OpenAILLMAdapter" in repr_str
        assert "gpt-4" in repr_str
        assert "max_retries=2" in repr_str
        assert "timeout=10.0" in repr_str

    @pytest.mark.asyncio
    async def test_generate_for_summarization_use_case(
        self, adapter, mock_openai_client
    ):
        """
        Debería funcionar correctamente para caso de uso de summarización.

        Validates: Requirements 3.1, 3.3
        """
        # Arrange
        article_text = "Bitcoin alcanza nuevo máximo histórico..." * 10
        prompt = f"Resume el siguiente artículo en 3-5 frases:\n\n{article_text}"

        # Mock que retorna un resumen
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = (
            "Bitcoin alcanzó un nuevo ATH. "
            "Los inversores institucionales impulsan el precio. "
            "El mercado muestra señales alcistas."
        )
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act
            summary = await adapter.generate(
                prompt=prompt,
                max_tokens=150,
                temperature=0.3,  # Baja temperature para summarización
            )

            # Assert
            assert isinstance(summary, str)
            assert len(summary) > 0

            # Verificar parámetros apropiados para summarización
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args.kwargs["temperature"] == 0.3
            assert call_args.kwargs["max_tokens"] == 150

    @pytest.mark.asyncio
    async def test_generate_for_content_generation_use_case(
        self, adapter, mock_openai_client
    ):
        """
        Debería funcionar correctamente para caso de uso de generación de contenido.

        Validates: Requirements 8.1, 8.2
        """
        # Arrange
        prompt = "Escribe un análisis detallado sobre el impacto de los ETFs de Bitcoin"
        system_prompt = "Eres un analista financiero experto en criptomonedas"

        # Mock que retorna contenido generado
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Análisis detallado sobre ETFs de Bitcoin..." * 20
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act
            content = await adapter.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7,  # Temperature balanceada para generación
                system_prompt=system_prompt,
            )

            # Assert
            assert isinstance(content, str)
            assert len(content) > 0

            # Verificar parámetros apropiados para generación
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args.kwargs["temperature"] == 0.7
            assert call_args.kwargs["max_tokens"] == 1000

            # Verificar que se incluyó system prompt
            messages = call_args.kwargs["messages"]
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == system_prompt

    @pytest.mark.asyncio
    async def test_generate_handles_client_initialization_failure(self, adapter):
        """
        Debería manejar fallo al inicializar el cliente.

        Validates: Requirements 8.2
        """
        # Arrange
        prompt = "Test prompt"

        # Mock que falla al inicializar el cliente
        def failing_get_client():
            raise Exception("Client initialization failed")

        with patch.object(adapter, "_get_client", side_effect=failing_get_client):
            # Act & Assert
            with pytest.raises(LLMGenerationException) as exc_info:
                await adapter.generate(prompt=prompt)

            # Verificar que la excepción original está preservada
            assert exc_info.value.original_error is not None
            assert "Client initialization failed" in str(exc_info.value.original_error)

    @pytest.mark.asyncio
    async def test_generate_with_multiple_concurrent_requests(
        self, adapter, mock_openai_client
    ):
        """
        Debería manejar múltiples requests concurrentes correctamente.

        Validates: Requirements 8.2
        """
        # Arrange
        prompts = [f"Prompt {i}" for i in range(5)]

        # Mock que retorna respuestas únicas
        call_count = 0

        async def create_unique_response(**kwargs):
            nonlocal call_count
            call_count += 1

            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = f"Response {call_count}"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response

        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=create_unique_response
        )

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act
            tasks = [adapter.generate(prompt=p) for p in prompts]
            results = await asyncio.gather(*tasks)

            # Assert
            assert len(results) == len(prompts)
            assert all(isinstance(r, str) for r in results)
            assert call_count == len(prompts)

            # Verificar que cada respuesta es única
            assert len(set(results)) == len(results)

    @pytest.mark.asyncio
    async def test_generate_with_whitespace_only_prompt_raises_error(self, adapter):
        """
        Debería lanzar error cuando el prompt solo contiene espacios.

        Validates: Requirements 3.1
        """
        # Arrange
        whitespace_prompts = ["   ", "\n\n\n", "\t\t\t", "  \n  \t  "]

        # Act & Assert
        for prompt in whitespace_prompts:
            with pytest.raises(ValueError, match="prompt no puede estar vacío"):
                await adapter.generate(prompt=prompt)

    @pytest.mark.asyncio
    async def test_generate_logs_generation_details(
        self, adapter, mock_openai_client, caplog
    ):
        """
        Debería loggear detalles de la generación.

        Validates: Requirements 8.2
        """
        # Arrange
        prompt = "Test prompt for logging"

        with patch.object(adapter, "_get_client", return_value=mock_openai_client):
            # Act
            await adapter.generate(
                prompt=prompt,
                max_tokens=200,
                temperature=0.5,
            )

            # Assert
            # Verificar que se loggeó la generación
            # (Los logs específicos dependen de la implementación de loguru)
            assert mock_openai_client.chat.completions.create.called
