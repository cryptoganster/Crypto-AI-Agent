"""Adaptador para servicio de LLM usando OpenAI GPT-4."""

import asyncio
from typing import Optional

from loguru import logger

from src.rag.domain.interfaces.llm_service import ILLMService


class LLMGenerationException(Exception):
    """Excepción cuando la generación de texto falla."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Inicializa la excepción.

        Args:
            message: Mensaje de error
            original_error: Excepción original que causó el error
        """
        super().__init__(message)
        self.original_error = original_error


class LLMTimeoutException(LLMGenerationException):
    """Excepción cuando la generación excede el timeout."""

    pass


class LLMRateLimitException(LLMGenerationException):
    """Excepción cuando se excede el rate limit de la API."""

    pass


class OpenAILLMAdapter(ILLMService):
    """
    Adaptador para generar texto usando OpenAI GPT-4.

    Implementa ILLMService usando la API de OpenAI para generación de texto
    con GPT-4. Soporta configuración de temperature, max_tokens y system prompts.

    Features:
    - Integración con OpenAI API (GPT-4)
    - Retry logic con exponential backoff
    - Manejo de rate limits
    - Timeout configurable
    - Logging detallado
    - Soporte para system prompts

    Attributes:
        api_key: API key de OpenAI
        model: Modelo a usar (default: "gpt-4")
        max_retries: Número máximo de reintentos (3)
        initial_retry_delay: Delay inicial para retry en segundos (1.0)
        max_retry_delay: Delay máximo para retry en segundos (10.0)
        timeout: Timeout para operaciones en segundos (60.0)

    Examples:
        >>> adapter = OpenAILLMAdapter(api_key="sk-...")
        >>> text = await adapter.generate(
        ...     prompt="Resume este artículo en 3 frases",
        ...     max_tokens=200,
        ...     temperature=0.3,
        ... )
        >>>
        >>> # Con system prompt
        >>> text = await adapter.generate(
        ...     prompt="Analiza el impacto de los ETFs de Bitcoin",
        ...     max_tokens=1000,
        ...     temperature=0.7,
        ...     system_prompt="Eres un analista financiero experto en cripto",
        ... )

    Requirements:
        - 3.1: Generar texto usando LLM (GPT-4)
        - 8.2: Integración con OpenAI API
    """

    DEFAULT_MODEL = "gpt-4"
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_RETRY_DELAY = 1.0
    DEFAULT_MAX_RETRY_DELAY = 10.0
    DEFAULT_TIMEOUT = 60.0

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_retry_delay: float = DEFAULT_INITIAL_RETRY_DELAY,
        max_retry_delay: float = DEFAULT_MAX_RETRY_DELAY,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Inicializa el adaptador.

        Args:
            api_key: API key de OpenAI (requerido)
            model: Modelo a usar (default: "gpt-4")
            max_retries: Número máximo de reintentos (default: 3)
            initial_retry_delay: Delay inicial para retry en segundos (default: 1.0)
            max_retry_delay: Delay máximo para retry en segundos (default: 10.0)
            timeout: Timeout para operaciones en segundos (default: 60.0)

        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if not api_key or not api_key.strip():
            raise ValueError("api_key es requerido y no puede estar vacío")

        if not model or not model.strip():
            raise ValueError("model es requerido y no puede estar vacío")

        if max_retries < 0:
            raise ValueError(f"max_retries debe ser >= 0, recibido: {max_retries}")

        if initial_retry_delay <= 0:
            raise ValueError(
                f"initial_retry_delay debe ser > 0, recibido: {initial_retry_delay}"
            )

        if max_retry_delay < initial_retry_delay:
            raise ValueError(
                f"max_retry_delay debe ser >= initial_retry_delay, "
                f"recibido: {max_retry_delay} < {initial_retry_delay}"
            )

        if timeout <= 0:
            raise ValueError(f"timeout debe ser > 0, recibido: {timeout}")

        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.timeout = timeout

        # Lazy initialization del cliente
        self._client = None

        logger.info(
            "OpenAILLMAdapter inicializado",
            model=self.model,
            max_retries=self.max_retries,
            timeout=self.timeout,
        )

    def _get_client(self):
        """
        Obtiene el cliente de OpenAI (lazy initialization).

        Returns:
            Cliente de OpenAI

        Raises:
            ImportError: Si openai no está instalado
            LLMGenerationException: Si el cliente no se puede inicializar
        """
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                logger.info("Inicializando cliente de OpenAI")

                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    timeout=self.timeout,
                )

                logger.info("Cliente de OpenAI inicializado exitosamente")

            except ImportError as e:
                error_msg = (
                    "openai no está instalado. " "Instalar con: pip install openai"
                )
                logger.error(error_msg, error=str(e))
                raise ImportError(error_msg) from e

            except Exception as e:
                error_msg = f"Error inicializando cliente de OpenAI: {str(e)}"
                logger.error(error_msg, error=str(e))
                raise LLMGenerationException(error_msg, original_error=e)

        return self._client

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Genera texto usando GPT-4.

        Implementa retry logic con exponential backoff para manejar
        errores transitorios de la API (rate limits, timeouts, etc.).

        Args:
            prompt: Prompt para el LLM. Debe ser claro y específico.
            max_tokens: Máximo de tokens a generar. Default: 500.
            temperature: Temperature para sampling (0.0-1.0). Default: 0.7.
            system_prompt: System prompt opcional para configurar el comportamiento.

        Returns:
            Texto generado por GPT-4.

        Raises:
            ValueError: Si los parámetros son inválidos
            LLMGenerationException: Si la generación falla después de reintentos
            LLMTimeoutException: Si la generación excede el timeout
            LLMRateLimitException: Si se excede el rate limit de la API

        Examples:
            >>> adapter = OpenAILLMAdapter(api_key="sk-...")
            >>>
            >>> # Summarización con temperature baja
            >>> summary = await adapter.generate(
            ...     prompt="Resume: Bitcoin alcanza nuevo ATH...",
            ...     max_tokens=150,
            ...     temperature=0.3,
            ... )
            >>>
            >>> # Generación creativa con system prompt
            >>> content = await adapter.generate(
            ...     prompt="Escribe análisis sobre ETFs de Bitcoin",
            ...     max_tokens=1000,
            ...     temperature=0.7,
            ...     system_prompt="Eres un analista financiero experto en cripto",
            ... )
        """
        # Validar entrada
        if not prompt or not prompt.strip():
            raise ValueError("prompt no puede estar vacío")

        if max_tokens <= 0:
            raise ValueError(f"max_tokens debe ser > 0, recibido: {max_tokens}")

        if not (0.0 <= temperature <= 1.0):
            raise ValueError(
                f"temperature debe estar entre 0.0 y 1.0, recibido: {temperature}"
            )

        logger.debug(
            "Generando texto con LLM",
            model=self.model,
            prompt_length=len(prompt),
            max_tokens=max_tokens,
            temperature=temperature,
            has_system_prompt=system_prompt is not None,
        )

        # Implementar retry logic con exponential backoff
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Generar texto con timeout
                text = await asyncio.wait_for(
                    self._generate_internal(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system_prompt=system_prompt,
                    ),
                    timeout=self.timeout,
                )

                logger.debug(
                    "Texto generado exitosamente",
                    model=self.model,
                    prompt_length=len(prompt),
                    response_length=len(text),
                    attempt=attempt + 1,
                )

                return text

            except asyncio.TimeoutError as e:
                error_msg = (
                    f"Timeout generando texto (intento {attempt + 1}/{self.max_retries + 1}): "
                    f"operación excedió {self.timeout}s"
                )
                logger.warning(error_msg)
                last_exception = LLMTimeoutException(error_msg, original_error=e)

            except Exception as e:
                # Detectar rate limit errors
                error_str = str(e).lower()
                if "rate" in error_str and "limit" in error_str:
                    error_msg = (
                        f"Rate limit excedido (intento {attempt + 1}/{self.max_retries + 1}): "
                        f"{str(e)}"
                    )
                    logger.warning(error_msg)
                    last_exception = LLMRateLimitException(error_msg, original_error=e)
                else:
                    error_msg = (
                        f"Error generando texto (intento {attempt + 1}/{self.max_retries + 1}): "
                        f"{str(e)}"
                    )
                    logger.warning(error_msg, error=str(e))
                    last_exception = LLMGenerationException(error_msg, original_error=e)

            # Si no es el último intento, esperar antes de reintentar
            if attempt < self.max_retries:
                # Exponential backoff: delay = initial * 2^attempt
                delay = min(
                    self.initial_retry_delay * (2**attempt), self.max_retry_delay
                )

                logger.info(
                    "Reintentando generación de texto",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    delay_seconds=delay,
                )

                await asyncio.sleep(delay)

        # Si llegamos aquí, todos los reintentos fallaron
        error_msg = f"Error generando texto después de {self.max_retries + 1} intentos"
        logger.error(error_msg, last_error=str(last_exception))

        # Re-raise la última excepción específica
        raise last_exception

    async def _generate_internal(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
    ) -> str:
        """
        Genera texto internamente (sin retry logic).

        Args:
            prompt: Prompt para el LLM
            max_tokens: Máximo de tokens a generar
            temperature: Temperature para sampling
            system_prompt: System prompt opcional

        Returns:
            Texto generado

        Raises:
            Exception: Si la generación falla
        """
        client = self._get_client()

        # Construir mensajes
        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        # Llamar a la API de OpenAI
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Extraer texto generado
        if not response.choices:
            raise LLMGenerationException("API no retornó ninguna respuesta")

        generated_text = response.choices[0].message.content

        if not generated_text:
            raise LLMGenerationException("API retornó texto vacío")

        return generated_text.strip()

    def __repr__(self) -> str:
        """Representación del adaptador."""
        return (
            f"OpenAILLMAdapter("
            f"model={self.model}, "
            f"max_retries={self.max_retries}, "
            f"timeout={self.timeout})"
        )
