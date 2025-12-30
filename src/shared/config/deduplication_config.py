"""Configuración para deduplicación semántica."""

from pydantic import Field
from pydantic_settings import BaseSettings


class DeduplicationConfig(BaseSettings):
    """
    Configuración para deduplicación semántica de artículos.

    Attributes:
        similarity_threshold: Threshold de similitud para considerar duplicado (0.0-1.0)
        max_results: Máximo número de duplicados a retornar por búsqueda
        enabled: Si la deduplicación está habilitada
    """

    similarity_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Threshold de similitud para duplicados (0.0-1.0)",
    )

    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Máximo número de duplicados a retornar",
    )

    enabled: bool = Field(
        default=True,
        description="Si la deduplicación semántica está habilitada",
    )

    model_config = {
        "env_prefix": "DEDUPLICATION_",
        "case_sensitive": False,
    }
