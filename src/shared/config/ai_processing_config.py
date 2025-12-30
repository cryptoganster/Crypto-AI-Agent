"""Configuración para AI Processing Pipeline.

Este módulo define configuración específica para el pipeline de procesamiento AI,
incluyendo feature flags, límites de texto, retry logic y timeouts.

NOTA: Esta configuración complementa (no duplica) las configuraciones existentes:
- ChunkingConfig: chunk_size, chunk_overlap
- EmbeddingConfig: embedding_model, batch_size, dimension
- RAGConfig: llm_model, max_context_tokens, temperature
- ClusteringConfig: algorithm, n_clusters
- DeduplicationConfig: similarity_threshold

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 12.2
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AIProcessingConfig:
    """
    Configuración para AI Processing Pipeline.

    Esta configuración contiene parámetros específicos del pipeline de procesamiento
    AI que no pertenecen a bounded contexts individuales (chunking, embedding, rag).

    Attributes:
        # Feature Flags
        enable_global_summary: Si generar summary global del artículo (default: True)
        enable_tldr: Si generar TLDR fusionado (default: True)

        # Límites de Texto
        max_text_length_for_global_summary: Máximo de texto para global summary (default: 10000)
        max_chunk_summaries_for_tldr: Máximo de chunk summaries para TLDR (default: 10)

        # Retry Configuration
        max_retries: Máximo número de reintentos en caso de fallo (default: 3)
        retry_delay_seconds: Delay entre reintentos en segundos (default: 2.0)

        # Timeouts
        chunking_timeout_seconds: Timeout para operación de chunking (default: 30.0)
        embedding_timeout_seconds: Timeout para generación de embeddings (default: 60.0)
        summarization_timeout_seconds: Timeout para summarization (default: 120.0)

        # Batch Processing
        summary_batch_size: Tamaño de batch para generar summaries (default: 5)

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 12.2

    Examples:
        >>> config = AIProcessingConfig.from_env()
        >>> config.use_new_ai_processing_pipeline
        False
        >>> config.max_retries
        3

        >>> # Sobrescribir con variables de entorno
        >>> os.environ["AI_USE_NEW_PIPELINE"] = "true"
        >>> config = AIProcessingConfig.from_env()
        >>> config.use_new_ai_processing_pipeline
        True
    """

    # Feature Flags
    enable_global_summary: bool = True
    enable_tldr: bool = True

    # Límites de Texto
    max_text_length_for_global_summary: int = 10000
    max_chunk_summaries_for_tldr: int = 10

    # Retry Configuration
    max_retries: int = 3
    retry_delay_seconds: float = 2.0

    # Timeouts
    chunking_timeout_seconds: float = 30.0
    embedding_timeout_seconds: float = 60.0
    summarization_timeout_seconds: float = 120.0

    # Batch Processing
    summary_batch_size: int = 5

    def __post_init__(self):
        """
        Valida la configuración después de inicialización.

        Raises:
            ValueError: Si algún valor es inválido

        Requirements: 3.5
        """
        # Validar límites de texto
        if self.max_text_length_for_global_summary <= 0:
            raise ValueError(
                f"max_text_length_for_global_summary debe ser > 0, "
                f"recibido: {self.max_text_length_for_global_summary}"
            )

        if self.max_chunk_summaries_for_tldr <= 0:
            raise ValueError(
                f"max_chunk_summaries_for_tldr debe ser > 0, "
                f"recibido: {self.max_chunk_summaries_for_tldr}"
            )

        # Validar retry configuration
        if self.max_retries < 0:
            raise ValueError(f"max_retries debe ser >= 0, recibido: {self.max_retries}")

        if self.retry_delay_seconds < 0:
            raise ValueError(
                f"retry_delay_seconds debe ser >= 0, "
                f"recibido: {self.retry_delay_seconds}"
            )

        # Validar timeouts
        if self.chunking_timeout_seconds <= 0:
            raise ValueError(
                f"chunking_timeout_seconds debe ser > 0, "
                f"recibido: {self.chunking_timeout_seconds}"
            )

        if self.embedding_timeout_seconds <= 0:
            raise ValueError(
                f"embedding_timeout_seconds debe ser > 0, "
                f"recibido: {self.embedding_timeout_seconds}"
            )

        if self.summarization_timeout_seconds <= 0:
            raise ValueError(
                f"summarization_timeout_seconds debe ser > 0, "
                f"recibido: {self.summarization_timeout_seconds}"
            )

        # Validar batch processing
        if self.summary_batch_size <= 0:
            raise ValueError(
                f"summary_batch_size debe ser > 0, "
                f"recibido: {self.summary_batch_size}"
            )

    @classmethod
    def from_env(cls, env_prefix: str = "AI_") -> "AIProcessingConfig":
        """
        Crea configuración desde variables de entorno.

        Variables de entorno (con prefijo AI_):
        - AI_ENABLE_GLOBAL_SUMMARY: Si generar global summary (default: true)
        - AI_ENABLE_TLDR: Si generar TLDR (default: true)
        - AI_MAX_TEXT_LENGTH_GLOBAL_SUMMARY: Máximo texto para summary (default: 10000)
        - AI_MAX_CHUNK_SUMMARIES_TLDR: Máximo summaries para TLDR (default: 10)
        - AI_MAX_RETRIES: Máximo reintentos (default: 3)
        - AI_RETRY_DELAY_SECONDS: Delay entre reintentos (default: 2.0)
        - AI_CHUNKING_TIMEOUT: Timeout chunking en segundos (default: 30.0)
        - AI_EMBEDDING_TIMEOUT: Timeout embeddings en segundos (default: 60.0)
        - AI_SUMMARIZATION_TIMEOUT: Timeout summarization en segundos (default: 120.0)
        - AI_SUMMARY_BATCH_SIZE: Batch size para summaries (default: 5)

        Args:
            env_prefix: Prefijo para variables de entorno (default: "AI_")

        Returns:
            AIProcessingConfig con valores desde environment o defaults

        Raises:
            ValueError: Si algún valor de configuración es inválido

        Requirements: 3.5

        Examples:
            >>> config = AIProcessingConfig.from_env()
            >>> config.use_new_ai_processing_pipeline
            False

            >>> os.environ["AI_USE_NEW_PIPELINE"] = "true"
            >>> config = AIProcessingConfig.from_env()
            >>> config.use_new_ai_processing_pipeline
            True
        """
        # Feature Flags
        enable_global_summary = (
            os.getenv(f"{env_prefix}ENABLE_GLOBAL_SUMMARY", "true").lower() == "true"
        )

        enable_tldr = os.getenv(f"{env_prefix}ENABLE_TLDR", "true").lower() == "true"

        # Límites de Texto
        max_text_length_global_summary = int(
            os.getenv(f"{env_prefix}MAX_TEXT_LENGTH_GLOBAL_SUMMARY", "10000")
        )

        max_chunk_summaries_tldr = int(
            os.getenv(f"{env_prefix}MAX_CHUNK_SUMMARIES_TLDR", "10")
        )

        # Retry Configuration
        max_retries = int(os.getenv(f"{env_prefix}MAX_RETRIES", "3"))

        retry_delay_seconds = float(
            os.getenv(f"{env_prefix}RETRY_DELAY_SECONDS", "2.0")
        )

        # Timeouts
        chunking_timeout = float(os.getenv(f"{env_prefix}CHUNKING_TIMEOUT", "30.0"))

        embedding_timeout = float(os.getenv(f"{env_prefix}EMBEDDING_TIMEOUT", "60.0"))

        summarization_timeout = float(
            os.getenv(f"{env_prefix}SUMMARIZATION_TIMEOUT", "120.0")
        )

        # Batch Processing
        summary_batch_size = int(os.getenv(f"{env_prefix}SUMMARY_BATCH_SIZE", "5"))

        return cls(
            enable_global_summary=enable_global_summary,
            enable_tldr=enable_tldr,
            max_text_length_for_global_summary=max_text_length_global_summary,
            max_chunk_summaries_for_tldr=max_chunk_summaries_tldr,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            chunking_timeout_seconds=chunking_timeout,
            embedding_timeout_seconds=embedding_timeout,
            summarization_timeout_seconds=summarization_timeout,
            summary_batch_size=summary_batch_size,
        )

    @classmethod
    def for_testing(cls, **overrides) -> "AIProcessingConfig":
        """
        Crea configuración para testing con valores por defecto.

        Args:
            **overrides: Valores a sobrescribir

        Returns:
            AIProcessingConfig para testing

        Examples:
            >>> config = AIProcessingConfig.for_testing()
            >>> config.max_retries
            3

            >>> config = AIProcessingConfig.for_testing(max_retries=5)
            >>> config.max_retries
            5
        """
        defaults = {
            "enable_global_summary": True,
            "enable_tldr": True,
            "max_text_length_for_global_summary": 10000,
            "max_chunk_summaries_for_tldr": 10,
            "max_retries": 3,
            "retry_delay_seconds": 2.0,
            "chunking_timeout_seconds": 30.0,
            "embedding_timeout_seconds": 60.0,
            "summarization_timeout_seconds": 120.0,
            "summary_batch_size": 5,
        }

        defaults.update(overrides)

        return cls(**defaults)
