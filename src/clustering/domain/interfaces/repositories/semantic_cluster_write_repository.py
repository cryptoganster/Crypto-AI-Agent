"""Interface para SemanticCluster write repository."""

from typing import Protocol

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster


class ISemanticClusterWriteRepository(Protocol):
    """
    Interface para operaciones de escritura de SemanticCluster.

    Siguiendo CQRS, este repository solo maneja operaciones de escritura.
    NO hace commit (usa Unit of Work pattern).
    """

    async def save(self, cluster: SemanticCluster) -> None:
        """
        Guarda o actualiza un cluster semántico.

        NO hace commit - el commit es responsabilidad del Unit of Work.

        Args:
            cluster: Cluster a guardar

        Examples:
            >>> cluster = SemanticCluster.create("Label", centroid)
            >>> await repository.save(cluster)
            >>> # Commit se hace en el handler via UoW
        """
        ...

    async def delete(self, cluster_id: str) -> None:
        """
        Elimina un cluster semántico.

        NO hace commit - el commit es responsabilidad del Unit of Work.

        Args:
            cluster_id: ID del cluster a eliminar

        Examples:
            >>> await repository.delete("cluster-123")
            >>> # Commit se hace en el handler via UoW
        """
        ...
