"""DTOs para GetProcessingStatus query."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ProcessingStatusDTO:
    """
    DTO para estado de procesamiento de artículo.

    Attributes:
        article_id: ID del artículo
        status: Estado del procesamiento ("PENDING", "PROCESSING", "COMPLETED", "FAILED")
        total_chunks: Total de chunks creados
        chunks_embedded: Chunks con embeddings
        chunks_summarized: Chunks con summaries
        chunks_completed: Chunks completamente procesados
        has_global_summary: Si tiene summary global
        has_tldr: Si tiene TLDR
        cluster_id: ID del cluster asignado (opcional)
        started_at: Fecha de inicio del procesamiento (opcional)
        completed_at: Fecha de completado (opcional)
        progress_percentage: Porcentaje de progreso (0-100)
        is_completed: Si el procesamiento está completo
    """

    article_id: str
    status: str
    total_chunks: int
    chunks_embedded: int
    chunks_summarized: int
    chunks_completed: int
    has_global_summary: bool
    has_tldr: bool
    cluster_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress_percentage: float
    is_completed: bool
