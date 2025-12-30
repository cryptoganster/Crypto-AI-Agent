"""Get Quality Metrics Query - CQRS Query Handler.

Este módulo implementa el query handler para obtener métricas de calidad
de artículos, siguiendo el patrón CQRS.
"""

from .dto import QualityMetricsDTO
from .handler import GetQualityMetricsHandler
from .query import GetQualityMetricsQuery

__all__ = [
    "GetQualityMetricsQuery",
    "QualityMetricsDTO",
    "GetQualityMetricsHandler",
]
