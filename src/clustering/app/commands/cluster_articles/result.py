"""Result object para ClusterArticlesCommand."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ClusterInfo:
    """Información de un cluster creado."""

    cluster_id: str
    label: str
    size: int
    article_ids: List[str]


@dataclass
class ClusterArticlesResult:
    """
    Result object para ClusterArticlesCommand.

    Attributes:
        success: Si el clustering fue exitoso
        clusters: Lista de clusters creados
        total_articles: Total de artículos procesados
        outliers: Artículos que no pertenecen a ningún cluster
        error: Mensaje de error si falló
    """

    success: bool
    clusters: List[ClusterInfo]
    total_articles: int
    outliers: List[str]
    error: Optional[str] = None

    @classmethod
    def success_result(
        cls,
        clusters: List[ClusterInfo],
        total_articles: int,
        outliers: List[str],
    ) -> "ClusterArticlesResult":
        """Crea resultado exitoso."""
        return cls(
            success=True,
            clusters=clusters,
            total_articles=total_articles,
            outliers=outliers,
            error=None,
        )

    @classmethod
    def failure(cls, error: str) -> "ClusterArticlesResult":
        """Crea resultado fallido."""
        return cls(
            success=False,
            clusters=[],
            total_articles=0,
            outliers=[],
            error=error,
        )
