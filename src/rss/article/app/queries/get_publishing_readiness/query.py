"""Query DTO para preparación de publicación de artículos."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class GetPublishingReadinessQuery:
    """Query para obtener información de preparación de publicación.

    Este query puede usarse de tres formas:
    1. Con article_id: Verifica preparación de un artículo específico
    2. Con operation='ready': Obtiene artículos listos para publicar
    3. Con operation='summary': Obtiene resumen de preparación
    4. Con operation='pending': Obtiene artículos pendientes
    5. Con operation='needs_work': Obtiene artículos que necesitan mejoras
    """

    article_id: Optional[UUID] = None
    operation: Optional[str] = None  # 'ready', 'summary', 'pending', 'needs_work'
    limit: int = 10
