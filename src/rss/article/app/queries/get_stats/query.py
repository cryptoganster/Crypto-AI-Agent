"""Query DTO para obtener estadísticas de artículos."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class GetArticleStatsQuery:
    """
    Query para obtener estadísticas de artículos.

    Este query permite obtener estadísticas generales o filtradas
    por fuente, incluyendo distribución de calidad y timeline de publicaciones.

    Attributes:
        source_id: Filtrar por fuente específica (opcional)
        timeline_days: Número de días para el timeline (opcional, default 30)
    """

    source_id: Optional[UUID] = None
    timeline_days: int = 30
