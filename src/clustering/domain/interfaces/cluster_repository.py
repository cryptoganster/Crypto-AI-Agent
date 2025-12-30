"""Repository interface para SemanticCluster."""

from typing import List, Optional, Protocol

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster


class IClusterReadRepository(Protocol):
    """
    Repository interface para operaciones de lectura de clusters.

    Responsabilidades:
    - Buscar clusters por ID
    - Listar todos los clusters
    - Filtrar clusters por tamaño
    """

    async def find_by_id(self, cluster_id: str) -> Optional[SemanticCluster]:
        """
        Busca cluster por ID.

        Args:
            cluster_id: ID del cluster

        Returns:
            SemanticCluster si existe, None si no
        """
        ...

    async def find_all(
        self,
        min_size: Optional[int] = None,
        order_by: str = "size",
        ascending: bool = False,
    ) -> List[SemanticCluster]:
        """
        Obtiene todos los clusters con filtros opcionales.

        Args:
            min_size: Tamaño mínimo del cluster (opcional)
            order_by: Campo para ordenar ("size", "updated_at", "label")
            ascending: Si ordenar ascendente

        Returns:
            Lista de SemanticCluster
        """
        ...

    async def count(self, min_size: Optional[int] = None) -> int:
        """
        Cuenta clusters con filtro opcional.

        Args:
            min_size: Tamaño mínimo del cluster (opcional)

        Returns:
            Número de clusters
        """
        ...


class IClusterWriteRepository(Protocol):
    """
    Repository interface para operaciones de escritura de clusters.

    Responsabilidades:
    - Guardar clusters
    - Eliminar clusters
    """

    async def save(self, cluster: SemanticCluster) -> None:
        """
        Guarda cluster.

        Args:
            cluster: Cluster a guardar
        """
        ...

    async def delete(self, cluster_id: str) -> None:
        """
        Elimina cluster.

        Args:
            cluster_id: ID del cluster a eliminar
        """
        ...
