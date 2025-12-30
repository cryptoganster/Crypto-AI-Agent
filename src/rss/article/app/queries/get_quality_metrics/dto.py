"""DTO de respuesta para métricas de calidad de artículos."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class QualityMetricsDTO:
    """
    DTO para respuesta de métricas de calidad.

    Contiene estadísticas agregadas sobre la calidad de artículos,
    incluyendo promedio, distribución y totales.

    Attributes:
        average_score: Score promedio de calidad (0.0-1.0)
        distribution: Distribución por rangos de calidad
                     {"excellent": 45, "good": 120, "average": 80, "poor": 15}
        total_articles: Número total de artículos analizados
        source_id: ID de la fuente filtrada (opcional)
    """

    average_score: float
    distribution: Dict[str, int]
    total_articles: int
    source_id: Optional[str] = None
