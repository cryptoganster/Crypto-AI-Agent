"""Embedding Configuration.

Configuración para el bounded context Embedding usando Ollama local.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EmbeddingConfig:
    """
    Configuración para Embedding Service usando Ollama local.

    Usa Ollama que corre localmente sin necesidad de API key.

    Modelos recomendados en Ollama:
    - nomic-embed-text (768 dim) - Recomendado para embeddings
    - mxbai-embed-large (1024 dim) - Embeddings grandes
    - llama3 (4096 dim) - Modelo general (no recomendado para embeddings)

    Attributes:
        embedding_model: Nombre del modelo en Ollama
        ollama_base_url: URL del servidor Ollama
        embedding_dimension: Dimensión de los embeddings
        batch_size: Tamaño de batch para procesamiento

    Requirements: 10.2.5
    """

    embedding_model: str = "nomic-embed-text"
    ollama_base_url: str = "http://localhost:11434"
    embedding_dimension: int = 768
    batch_size: int = 32

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """
        Crea configuración desde variables de entorno.

        Environment Variables:
            EMBEDDING_MODEL: Modelo en Ollama (opcional, default: nomic-embed-text)
            OLLAMA_BASE_URL: URL de Ollama (opcional, default: http://localhost:11434)
            EMBEDDING_DIMENSION: Dimensión de embeddings (opcional, default: 768)
            EMBEDDING_BATCH_SIZE: Tamaño de batch (opcional, default: 32)

        Returns:
            EmbeddingConfig con valores desde environment

        Note:
            No requiere API key - Ollama corre localmente.
            Asegúrate de tener Ollama corriendo: ollama serve
            Descarga el modelo: ollama pull nomic-embed-text

        Requirements: 10.2.5
        """
        embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "768"))

        batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

        return cls(
            embedding_model=embedding_model,
            ollama_base_url=ollama_base_url,
            embedding_dimension=embedding_dimension,
            batch_size=batch_size,
        )

    def validate(self) -> None:
        """
        Valida la configuración.

        Raises:
            ValueError: Si la configuración es inválida

        Requirements: 10.2.5
        """
        if not self.embedding_model:
            raise ValueError("embedding_model is required")

        if not self.ollama_base_url:
            raise ValueError("ollama_base_url is required")

        if self.embedding_dimension <= 0:
            raise ValueError("embedding_dimension must be positive")

        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")

        # Modelos recomendados para embeddings en Ollama
        recommended_models = [
            "nomic-embed-text",
            "mxbai-embed-large",
            "all-minilm",
        ]

        if self.embedding_model not in recommended_models:
            # Solo advertencia, no error - permitir cualquier modelo en Ollama
            import warnings

            warnings.warn(
                f"Modelo {self.embedding_model} no está en la lista de recomendados para embeddings. "
                f"Modelos recomendados: {', '.join(recommended_models)}"
            )
