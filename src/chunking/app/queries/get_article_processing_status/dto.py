"""DTO para el estado de procesamiento de artículos."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ArticleProcessingStatusDTO:
    """
    DTO con el estado de procesamiento AI de un artículo.

    Representa el estado actual del pipeline sin exponer
    detalles de implementación del Process Manager.

    Attributes:
        article_id: ID del artículo
        state: Estado actual del pipeline (pending, chunking, embedding, etc.)
        total_chunks: Número total de chunks
        chunks_created: Chunks creados
        chunks_embedded: Chunks con embeddings
        chunks_summarized: Chunks con summaries
        chunks_completed: Chunks completados (persistidos)
        chunks_failed: Chunks que fallaron
        started_at: Timestamp de inicio del procesamiento
        completed_at: Timestamp de completitud (si terminó)
        duration_seconds: Duración del procesamiento en segundos
        error_message: Mensaje de error si falló
        enable_global_summary: Si el global summary está habilitado
        enable_tldr: Si el TLDR está habilitado

    Example:
        >>> dto = ArticleProcessingStatusDTO(
        ...     article_id="art-123",
        ...     state="embedding",
        ...     total_chunks=10,
        ...     chunks_created=10,
        ...     chunks_embedded=5,
        ...     chunks_summarized=0,
        ...     chunks_completed=0,
        ...     chunks_failed=0,
        ...     started_at=datetime.now(),
        ...     completed_at=None,
        ...     duration_seconds=None,
        ...     error_message=None,
        ...     enable_global_summary=True,
        ...     enable_tldr=True,
        ... )
    """

    article_id: str
    state: str
    total_chunks: int
    chunks_created: int
    chunks_embedded: int
    chunks_summarized: int
    chunks_completed: int
    chunks_failed: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    error_message: Optional[str]
    enable_global_summary: bool
    enable_tldr: bool

    @property
    def is_in_progress(self) -> bool:
        """Indica si el procesamiento está en progreso."""
        return self.state not in ("completed", "failed", "pending")

    @property
    def is_completed(self) -> bool:
        """Indica si el procesamiento completó exitosamente."""
        return self.state == "completed"

    @property
    def is_failed(self) -> bool:
        """Indica si el procesamiento falló."""
        return self.state == "failed"

    @property
    def progress_percentage(self) -> float:
        """
        Calcula el porcentaje de progreso del procesamiento.

        Returns:
            Porcentaje de 0.0 a 100.0
        """
        if self.total_chunks == 0:
            return 0.0

        # Cada chunk pasa por 4 etapas: created, embedded, summarized, completed
        total_steps = self.total_chunks * 4
        completed_steps = (
            self.chunks_created
            + self.chunks_embedded
            + self.chunks_summarized
            + self.chunks_completed
        )

        return (completed_steps / total_steps) * 100.0
