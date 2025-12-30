"""DTOs para GetArticleClusters query."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple


@dataclass
class ClusterDTO:
    """
    DTO para un cluster semántico.

    Attributes:
        cluster_id: ID del cluster
        label: Label descriptivo del cluster
        size: Número de artículos en el cluster
        article_ids: Lista de IDs de artículos
        top_terms: Términos más frecuentes (term, frequency)
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """

    cluster_id: str
    label: str
    size: int
    article_ids: List[str]
    top_terms: List[Tuple[str, float]]
    created_at: datetime
    updated_at: datetime


@dataclass
class GetArticleClustersResultDTO:
    """
    DTO para resultado de obtención de clusters.

    Attributes:
        clusters: Lista de clusters
        total_clusters: Total de clusters encontrados
        min_size_filter: Filtro de tamaño mínimo aplicado (opcional)
        order_by: Campo usado para ordenar
    """

    clusters: List[ClusterDTO]
    total_clusters: int
    min_size_filter: int | None
    order_by: str
