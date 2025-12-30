"""Query DTO para obtener métricas de calidad de artículos."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class GetQualityMetricsQuery:
    """
    Query para obtener métricas de calidad de artículos.

    Este query permite filtrar métricas por fuente y por tiempo,
    retornando estadísticas agregadas de calidad.

    Attributes:
        source_id: Filtrar por fuente específica (opcional)
        hours: Filtrar por artículos recientes (últimas N horas) (opcional)
    """

    source_id: Optional[UUID] = None
    hours: Optional[int] = None
