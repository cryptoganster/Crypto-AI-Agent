"""Interface para SemanticCluster read repository."""

from typing import List, Optional, Protocol

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster


class ISemanticClusterReadRepository(Protocol):
    """
    Interface para operaciones de lectura de SemanticCluster.

    Siguiendo CQRS, este repository solo maneja operaciones de lectura.
    """

    async def find_by_id(self, cluster_id: str) -> Optional[SemanticCluster]:
        """
        Busca cluster por ID.

        Args:
            cluster_id: ID del cluster a buscar

        Returns:
            SemanticCluster si existe, None en caso contrario

        Examples:
            >>> cluster = await repository.find_by_id("cluster-123")
            >>> if cluster:
            ...     print(cluster.label)
        """
        ...

    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[SemanticCluster]:
        """
        Obtiene todos los clusters con paginación opcional.

        Args:
            limit: Número máximo de clusters a retornar
            offset: Número de clusters a saltar

        Returns:
            Lista de clusters

        Examples:
            >>> clusters = await repository.find_all(limit=10, offset=0)
            >>> len(clusters) <= 10
            True
        """
        ...

    async def find_by_article_id(self, article_id: str) -> Optional[SemanticCluster]:
        """
        Busca cluster que contiene un artículo específico.

        Args:
            article_id: ID del artículo a buscar

        Returns:
            SemanticCluster que contiene el artículo, None si no existe

        Examples:
            >>> cluster = await repository.find_by_article_id("article-123")
            >>> if cluster:
            ...     assert "article-123" in cluster.article_ids
        """
        ...

    async def count(self) -> int:
        """
        Cuenta el total de clusters.

        Returns:
            Número total de clusters

        Examples:
            >>> total = await repository.count()
            >>> total >= 0
            True
        """
        ...

    async def exists(self, cluster_id: str) -> bool:
        """
        Verifica si existe un cluster.

        Args:
            cluster_id: ID del cluster a verificar

        Returns:
            True si existe, False en caso contrario

        Examples:
            >>> exists = await repository.exists("cluster-123")
            >>> isinstance(exists, bool)
            True
        """
        ...
