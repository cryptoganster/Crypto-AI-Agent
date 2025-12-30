"""Enum para estado de procesamiento de chunk."""

from enum import Enum


class ChunkStatus(str, Enum):
    """
    Enum para estado de procesamiento de chunk.

    Estados del ciclo de vida de un ContentChunk:
    - PENDING: Chunk creado, esperando embedding
    - EMBEDDED: Embedding generado, esperando summarización
    - SUMMARIZED: Summary generado, esperando completar
    - COMPLETED: Procesamiento completo
    - FAILED: Error en el procesamiento

    Examples:
        >>> status = ChunkStatus.PENDING
        >>> status.value
        'PENDING'
        >>> ChunkStatus.EMBEDDED == "EMBEDDED"
        True
    """

    PENDING = "PENDING"
    EMBEDDED = "EMBEDDED"
    SUMMARIZED = "SUMMARIZED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    def is_pending(self) -> bool:
        """Verifica si el chunk está pendiente de procesamiento."""
        return self == ChunkStatus.PENDING

    def is_embedded(self) -> bool:
        """Verifica si el chunk tiene embedding."""
        return self == ChunkStatus.EMBEDDED

    def is_summarized(self) -> bool:
        """Verifica si el chunk tiene summary."""
        return self == ChunkStatus.SUMMARIZED

    def is_completed(self) -> bool:
        """Verifica si el chunk está completamente procesado."""
        return self == ChunkStatus.COMPLETED

    def is_failed(self) -> bool:
        """Verifica si el procesamiento falló."""
        return self == ChunkStatus.FAILED

    def can_embed(self) -> bool:
        """Verifica si el chunk puede recibir embedding."""
        return self == ChunkStatus.PENDING

    def can_summarize(self) -> bool:
        """Verifica si el chunk puede ser summarizado."""
        return self == ChunkStatus.EMBEDDED

    def can_complete(self) -> bool:
        """Verifica si el chunk puede ser marcado como completado."""
        return self == ChunkStatus.SUMMARIZED

    def __str__(self) -> str:
        """Representación en string del status."""
        return self.value
