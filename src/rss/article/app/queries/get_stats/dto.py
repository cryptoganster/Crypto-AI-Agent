"""DTO de respuesta para estadísticas de artículos."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class TimelineDataPoint:
    """
    Punto de datos en el timeline de publicaciones.

    Attributes:
        date: Fecha en formato ISO (YYYY-MM-DD)
        count: Número de artículos en esa fecha
    """

    date: str
    count: int


@dataclass(frozen=True)
class ArticleStatsDTO:
    """
    DTO para respuesta de estadísticas de artículos.

    Contiene estadísticas completas sobre la colección de artículos,
    incluyendo totales, promedios, distribución de calidad y timeline.

    Attributes:
        total_articles: Número total de artículos
        by_source: Estadísticas agrupadas por fuente {source_id: count}
        by_status: Estadísticas agrupadas por estado {status: count}
        average_quality: Score promedio de calidad (0.0-1.0)
        recent_count: Número de artículos en las últimas 24 horas
        quality_distribution: Distribución por rangos de calidad
                             {"high": 45, "medium": 120, "low": 15, "unscored": 5}
        publication_timeline: Timeline de publicaciones por fecha
        source_id: ID de la fuente filtrada (opcional)
    """

    total_articles: int
    by_source: Dict[str, int]
    by_status: Dict[str, int]
    average_quality: float
    recent_count: int
    quality_distribution: Dict[str, int]
    publication_timeline: List[TimelineDataPoint]
    source_id: Optional[str] = None
