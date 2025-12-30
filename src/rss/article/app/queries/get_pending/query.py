"""Query para obtener artículos pendientes de procesamiento."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GetPendingArticlesQuery:
    """
    Query para obtener artículos que necesitan procesamiento.

    CQRS Read Side: Solo lectura.

    Criterios:
    - Sin markdown_content O
    - Sin plaintext_content O
    - Creados recientemente

    Args:
        limit: Límite de resultados (opcional, default 10)
    """

    limit: Optional[int] = 10

    def __post_init__(self):
        """Validación básica."""
        if self.limit is not None and self.limit <= 0:
            raise ValueError("limit debe ser mayor a 0")
        if self.limit is not None and self.limit > 100:
            raise ValueError("limit no puede exceder 100")
