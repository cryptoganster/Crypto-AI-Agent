"""Read model para estado de procesamiento de artículo."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ArticleProcessingStatus:
    """
    Read model para estado de procesamiento de artículo.

    NO es aggregate. Se actualiza mediante event handlers.
    Provee vista materializada del estado de procesamiento.

    Este read model trackea el progreso del procesamiento de AI
    para un artículo a través de múltiples bounded contexts:
    - Chunking: División del texto
    - Embedding: Generación de vectores
    - Summarization: Generación de resúmenes
    - Clustering: Agrupación semántica

    Attributes:
        article_id: ID del artículo siendo procesado
        total_chunks: Número total de chunks creados
        chunks_embedded: Número de chunks con embeddings
        chunks_summarized: Número de chunks con summaries
        chunks_completed: Número de chunks completamente procesados
        has_global_summary: Si tiene summary global del artículo
        has_tldr: Si tiene TLDR (resumen ultra-conciso)
        cluster_id: ID del cluster semántico (opcional)
        status: Estado general del procesamiento
        started_at: Timestamp de inicio del procesamiento
        completed_at: Timestamp de finalización (opcional)
    """

    article_id: str
    total_chunks: int
    chunks_embedded: int
    chunks_summarized: int
    chunks_completed: int
    has_global_summary: bool
    has_tldr: bool
    cluster_id: Optional[str]
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    started_at: datetime
    completed_at: Optional[datetime]

    @property
    def is_completed(self) -> bool:
        """
        Verifica si el procesamiento está completo.

        El procesamiento se considera completo cuando:
        - Hay al menos un chunk creado
        - Todos los chunks están completados
        - Existe un summary global
        - Existe un TLDR

        Returns:
            True si el procesamiento está completo, False en caso contrario
        """
        return (
            self.total_chunks > 0
            and self.chunks_completed == self.total_chunks
            and self.has_global_summary
            and self.has_tldr
        )

    @property
    def progress_percentage(self) -> float:
        """
        Calcula porcentaje de progreso del procesamiento.

        El progreso se calcula basándose en el número de chunks
        completados respecto al total de chunks.

        Returns:
            Porcentaje de progreso (0.0 - 100.0)
        """
        if self.total_chunks == 0:
            return 0.0
        return (self.chunks_completed / self.total_chunks) * 100
