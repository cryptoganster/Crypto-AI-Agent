"""DTO para métricas de procesamiento."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ProcessingMetricsDTO:
    """
    DTO con métricas agregadas de procesamiento AI.

    Representa métricas calculadas a través de múltiples artículos
    sin exponer detalles de implementación del Process Manager.

    Attributes:
        total_articles_processed: Número total de artículos procesados
        articles_completed: Artículos completados exitosamente
        articles_failed: Artículos que fallaron
        articles_in_progress: Artículos actualmente en procesamiento
        total_chunks_created: Total de chunks creados
        total_chunks_embedded: Total de chunks con embeddings
        total_chunks_summarized: Total de chunks con summaries
        total_chunks_completed: Total de chunks completados
        total_chunks_failed: Total de chunks que fallaron
        average_chunks_per_article: Promedio de chunks por artículo
        average_processing_time_seconds: Tiempo promedio de procesamiento
        success_rate: Tasa de éxito (0.0 a 1.0)
        failure_rate: Tasa de fallo (0.0 a 1.0)
        articles_by_state: Distribución de artículos por estado

    Example:
        >>> dto = ProcessingMetricsDTO(
        ...     total_articles_processed=150,
        ...     articles_completed=140,
        ...     articles_failed=5,
        ...     articles_in_progress=5,
        ...     total_chunks_created=1500,
        ...     total_chunks_embedded=1450,
        ...     total_chunks_summarized=1400,
        ...     total_chunks_completed=1400,
        ...     total_chunks_failed=50,
        ...     average_chunks_per_article=10.0,
        ...     average_processing_time_seconds=45.5,
        ...     success_rate=0.933,
        ...     failure_rate=0.033,
        ...     articles_by_state={
        ...         "completed": 140,
        ...         "failed": 5,
        ...         "embedding": 3,
        ...         "summarizing": 2
        ...     }
        ... )
        >>> dto.success_rate_percentage
        93.3
    """

    total_articles_processed: int
    articles_completed: int
    articles_failed: int
    articles_in_progress: int
    total_chunks_created: int
    total_chunks_embedded: int
    total_chunks_summarized: int
    total_chunks_completed: int
    total_chunks_failed: int
    average_chunks_per_article: float
    average_processing_time_seconds: float
    success_rate: float
    failure_rate: float
    articles_by_state: Dict[str, int]

    @property
    def success_rate_percentage(self) -> float:
        """
        Retorna la tasa de éxito como porcentaje.

        Returns:
            Porcentaje de 0.0 a 100.0
        """
        return self.success_rate * 100.0

    @property
    def failure_rate_percentage(self) -> float:
        """
        Retorna la tasa de fallo como porcentaje.

        Returns:
            Porcentaje de 0.0 a 100.0
        """
        return self.failure_rate * 100.0

    @property
    def chunk_completion_rate(self) -> float:
        """
        Calcula la tasa de completitud de chunks.

        Returns:
            Porcentaje de 0.0 a 100.0
        """
        if self.total_chunks_created == 0:
            return 0.0

        return (self.total_chunks_completed / self.total_chunks_created) * 100.0

    @property
    def chunk_failure_rate(self) -> float:
        """
        Calcula la tasa de fallo de chunks.

        Returns:
            Porcentaje de 0.0 a 100.0
        """
        if self.total_chunks_created == 0:
            return 0.0

        return (self.total_chunks_failed / self.total_chunks_created) * 100.0

    @property
    def has_failures(self) -> bool:
        """Indica si hay artículos o chunks que fallaron."""
        return self.articles_failed > 0 or self.total_chunks_failed > 0

    @property
    def is_healthy(self) -> bool:
        """
        Indica si el sistema está saludable (success rate > 95%).

        Returns:
            True si la tasa de éxito es mayor a 95%
        """
        return self.success_rate >= 0.95
