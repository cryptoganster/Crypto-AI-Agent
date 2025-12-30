"""Command para ejecutar clustering de artículos."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ClusterArticlesCommand:
    """
    Command para agrupar artículos en clusters semánticos.

    Este comando ejecuta clustering sobre embeddings de artículos
    para identificar temas trending y relacionar contenido similar.

    Attributes:
        algorithm: Algoritmo de clustering ("kmeans" o "dbscan")
        n_clusters: Número de clusters (solo para kmeans)
        min_articles: Mínimo de artículos para ejecutar clustering
        recalculate: Si recalcular clusters existentes
    """

    algorithm: str = "kmeans"  # "kmeans" or "dbscan"
    n_clusters: int = 10
    min_articles: Optional[int] = 20
    recalculate: bool = False
