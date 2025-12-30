"""Chunking configuration."""

import os
from dataclasses import dataclass


@dataclass
class ChunkingConfig:
    """
    Configuración para el servicio de chunking.

    Parámetros:
    - chunk_size: Tamaño máximo del chunk en tokens (100-2000)
    - chunk_overlap: Overlap entre chunks en tokens (0 a chunk_size-1)

    Requirements: 4.1
    """

    chunk_size: int = 1400
    chunk_overlap: int = 150

    @classmethod
    def from_env(cls) -> "ChunkingConfig":
        """
        Crea configuración desde variables de entorno.

        Variables:
        - CHUNK_SIZE: Tamaño del chunk en tokens (default: 1400)
        - CHUNK_OVERLAP: Overlap en tokens (default: 150)

        Returns:
            ChunkingConfig con valores de entorno o defaults

        Raises:
            ValueError: Si los valores son inválidos
        """
        chunk_size = int(os.getenv("CHUNK_SIZE", "1400"))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))

        # Validar chunk_size
        if chunk_size < 100:
            raise ValueError(f"CHUNK_SIZE debe ser >= 100, recibido: {chunk_size}")
        if chunk_size > 2000:
            raise ValueError(f"CHUNK_SIZE debe ser <= 2000, recibido: {chunk_size}")

        # Validar chunk_overlap
        if chunk_overlap < 0:
            raise ValueError(f"CHUNK_OVERLAP debe ser >= 0, recibido: {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"CHUNK_OVERLAP ({chunk_overlap}) debe ser < CHUNK_SIZE ({chunk_size})"
            )

        return cls(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
