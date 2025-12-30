"""Query para obtener clusters de artículos."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GetArticleClustersQuery:
    """
    Query para obtener clusters de artículos.

    Attributes:
        min_size: Tamaño mínimo del cluster (opcional)
        order_by: Campo para ordenar ("size", "updated_at", "label")
        ascending: Si ordenar ascendente (default: False)
    """

    min_size: Optional[int] = None
    order_by: str = "size"
    ascending: bool = False

    def __post_init__(self):
        """Valida el query."""
        if self.min_size is not None and self.min_size < 1:
            raise ValueError("min_size debe ser mayor o igual a 1")

        valid_order_by = ["size", "updated_at", "label"]
        if self.order_by not in valid_order_by:
            raise ValueError(
                f"order_by debe ser uno de {valid_order_by}, "
                f"recibido: {self.order_by}"
            )
