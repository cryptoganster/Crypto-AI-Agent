"""Configuración para RAG (Retrieval-Augmented Generation)."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RAGConfig:
    """
    Configuración para RAG bounded context.

    Attributes:
        llm_api_key: API key para el servicio LLM (OpenAI)
        llm_model: Modelo LLM a usar (default: gpt-4)
        max_context_tokens: Máximo de tokens en context pack (default: 4000)
        default_temperature: Temperatura por defecto para generación (default: 0.3)
        default_max_tokens: Máximo de tokens por defecto para respuesta (default: 1000)

    Requirements: 10.5.4
    """

    llm_api_key: str
    llm_model: str = "gpt-4"
    max_context_tokens: int = 4000
    default_temperature: float = 0.3
    default_max_tokens: int = 1000

    def __post_init__(self):
        """Valida la configuración."""
        # Validar API key
        if not self.llm_api_key or not self.llm_api_key.strip():
            raise ValueError("llm_api_key no puede estar vacío")

        # Validar modelo
        valid_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        if self.llm_model not in valid_models:
            raise ValueError(
                f"llm_model debe ser uno de {valid_models}, recibido: {self.llm_model}"
            )

        # Validar max_context_tokens
        if self.max_context_tokens <= 0:
            raise ValueError(
                f"max_context_tokens debe ser > 0, recibido: {self.max_context_tokens}"
            )

        if self.max_context_tokens > 8000:
            raise ValueError(
                f"max_context_tokens no puede exceder 8000, recibido: {self.max_context_tokens}"
            )

        # Validar temperature
        if not (0.0 <= self.default_temperature <= 2.0):
            raise ValueError(
                f"default_temperature debe estar entre 0.0 y 2.0, recibido: {self.default_temperature}"
            )

        # Validar max_tokens
        if self.default_max_tokens <= 0:
            raise ValueError(
                f"default_max_tokens debe ser > 0, recibido: {self.default_max_tokens}"
            )

        if self.default_max_tokens > 4000:
            raise ValueError(
                f"default_max_tokens no puede exceder 4000, recibido: {self.default_max_tokens}"
            )

    @classmethod
    def from_env(cls, env_prefix: str = "") -> "RAGConfig":
        """
        Crea configuración desde variables de entorno.

        Variables de entorno:
        - LLM_API_KEY: API key para OpenAI (requerido)
        - LLM_MODEL: Modelo a usar (default: gpt-4)
        - MAX_CONTEXT_TOKENS: Máximo de tokens en context pack (default: 4000)
        - DEFAULT_TEMPERATURE: Temperatura por defecto (default: 0.3)
        - DEFAULT_MAX_TOKENS: Máximo de tokens por defecto (default: 1000)

        Args:
            env_prefix: Prefijo para variables de entorno (opcional)

        Returns:
            RAGConfig configurado desde environment

        Raises:
            ValueError: Si la configuración es inválida

        Examples:
            >>> config = RAGConfig.from_env()
            >>> config.llm_model
            'gpt-4'
            >>> config.max_context_tokens
            4000
        """
        llm_api_key = os.getenv(f"{env_prefix}LLM_API_KEY", "")

        if not llm_api_key:
            raise ValueError(
                f"Variable de entorno {env_prefix}LLM_API_KEY es requerida"
            )

        llm_model = os.getenv(f"{env_prefix}LLM_MODEL", "gpt-4")

        max_context_tokens_str = os.getenv(f"{env_prefix}MAX_CONTEXT_TOKENS", "4000")
        max_context_tokens = int(max_context_tokens_str)

        default_temperature_str = os.getenv(f"{env_prefix}DEFAULT_TEMPERATURE", "0.3")
        default_temperature = float(default_temperature_str)

        default_max_tokens_str = os.getenv(f"{env_prefix}DEFAULT_MAX_TOKENS", "1000")
        default_max_tokens = int(default_max_tokens_str)

        return cls(
            llm_api_key=llm_api_key,
            llm_model=llm_model,
            max_context_tokens=max_context_tokens,
            default_temperature=default_temperature,
            default_max_tokens=default_max_tokens,
        )

    @classmethod
    def for_testing(
        cls,
        llm_api_key: Optional[str] = None,
        **overrides,
    ) -> "RAGConfig":
        """
        Crea configuración para testing.

        Args:
            llm_api_key: API key (default: "test-key")
            **overrides: Valores a sobrescribir

        Returns:
            RAGConfig para testing

        Examples:
            >>> config = RAGConfig.for_testing()
            >>> config.llm_api_key
            'test-key'
            >>> config.llm_model
            'gpt-4'
        """
        defaults = {
            "llm_api_key": llm_api_key or "test-key",
            "llm_model": "gpt-4",
            "max_context_tokens": 4000,
            "default_temperature": 0.3,
            "default_max_tokens": 1000,
        }

        defaults.update(overrides)

        return cls(**defaults)
