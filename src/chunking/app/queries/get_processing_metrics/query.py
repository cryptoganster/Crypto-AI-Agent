"""Query para obtener métricas de procesamiento agregadas."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class GetProcessingMetricsQuery:
    """
    Query para obtener métricas agregadas de procesamiento AI.

    Este query calcula métricas de procesamiento a través de múltiples
    artículos sin modificar ningún estado. Permite filtrar por rango
    de fechas y estado.

    Attributes:
        start_date: Fecha de inicio del rango (opcional)
        end_date: Fecha de fin del rango (opcional)
        state_filter: Filtrar por estado específico (opcional)

    Example:
        >>> # Métricas de todos los artículos
        >>> query = GetProcessingMetricsQuery()
        >>> result = await handler.handle(query)
        >>> print(result.total_articles_processed)
        150
        >>>
        >>> # Métricas de la última semana
        >>> from datetime import datetime, timedelta
        >>> query = GetProcessingMetricsQuery(
        ...     start_date=datetime.now() - timedelta(days=7),
        ...     end_date=datetime.now()
        ... )
        >>>
        >>> # Métricas de artículos completados
        >>> query = GetProcessingMetricsQuery(state_filter="completed")
    """

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    state_filter: Optional[str] = None
