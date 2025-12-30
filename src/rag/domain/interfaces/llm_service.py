"""Interface para servicio de LLM."""

from typing import Optional, Protocol


class ILLMService(Protocol):
    """
    Interface para servicio de LLM.

    Esta interface define el contrato para servicios de generación de texto
    usando Large Language Models (LLMs). Sigue el Dependency Inversion Principle,
    permitiendo que el dominio dependa de abstracciones en lugar de implementaciones
    concretas.

    Implementaciones:
    - OpenAILLMAdapter (GPT-4)
    - LlamaLLMAdapter (Llama 3.x)
    - OllamaLLMAdapter (local)

    Responsabilidades:
    - Generar texto basado en prompts
    - Configurar parámetros de generación (temperature, max_tokens)
    - Manejar system prompts opcionales

    Ejemplo:
        >>> llm_service = OpenAILLMAdapter(api_key="...")
        >>> text = await llm_service.generate(
        ...     prompt="Resume este artículo en 3 frases",
        ...     max_tokens=200,
        ...     temperature=0.3,
        ... )
    """

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Genera texto usando LLM.

        Args:
            prompt: Prompt para el LLM. Debe ser claro y específico.
            max_tokens: Máximo de tokens a generar. Default: 500.
                       Valores típicos:
                       - Summaries cortos: 100-200
                       - Summaries largos: 300-500
                       - Contenido generado: 1000-2000
            temperature: Temperature para sampling (0.0-1.0). Default: 0.7.
                        - 0.0-0.3: Determinístico, ideal para summaries
                        - 0.4-0.7: Balanceado
                        - 0.8-1.0: Creativo, ideal para contenido nuevo
            system_prompt: System prompt opcional para configurar el comportamiento
                          del LLM. Útil para definir rol, tono, formato.

        Returns:
            Texto generado por el LLM.

        Raises:
            LLMGenerationException: Si la generación falla
            LLMTimeoutException: Si la generación excede el timeout
            LLMRateLimitException: Si se excede el rate limit de la API

        Example:
            >>> # Summarización con temperature baja
            >>> summary = await llm.generate(
            ...     prompt="Resume: Bitcoin alcanza nuevo ATH...",
            ...     max_tokens=150,
            ...     temperature=0.3,
            ... )

            >>> # Generación creativa con system prompt
            >>> content = await llm.generate(
            ...     prompt="Escribe análisis sobre ETFs de Bitcoin",
            ...     max_tokens=1000,
            ...     temperature=0.7,
            ...     system_prompt="Eres un analista financiero experto en cripto",
            ... )
        """
        ...
