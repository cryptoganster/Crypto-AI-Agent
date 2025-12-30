"""Implementación SQLAlchemy de ISemanticClusterReadRepository."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.interfaces.repositories import ISemanticClusterReadRepository
from src.clustering.infra.persistence.mappers import SemanticClusterMapper
from src.clustering.infra.persistence.models import (
    ClusterMemberModel,
    SemanticClusterModel,
)


class SqlAlchemySemanticClusterReadRepository(ISemanticClusterReadRepository):
    """
    Implementación SQLAlchemy de ISemanticClusterReadRepository.

    Responsabilidades:
    - Buscar clusters por ID
    - Listar clusters con paginación
    - Buscar cluster por article_id
    - Contar clusters

    Attributes:
        _session: Sesión de SQLAlchemy
        _mapper: Mapper para conversión model → domain
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa repository.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session
        self._mapper = SemanticClusterMapper()

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
        stmt = select(SemanticClusterModel).where(SemanticClusterModel.id == cluster_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._mapper.to_domain(model)

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
            Lista de clusters ordenados por created_at desc

        Examples:
            >>> clusters = await repository.find_all(limit=10, offset=0)
            >>> len(clusters) <= 10
            True
        """
        stmt = select(SemanticClusterModel).order_by(
            SemanticClusterModel.created_at.desc()
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in models]

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
        # Join con cluster_members para buscar por article_id
        stmt = (
            select(SemanticClusterModel)
            .join(ClusterMemberModel)
            .where(ClusterMemberModel.article_id == article_id)
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._mapper.to_domain(model)

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
        stmt = select(func.count()).select_from(SemanticClusterModel)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

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
        stmt = select(
            select(SemanticClusterModel.id)
            .where(SemanticClusterModel.id == cluster_id)
            .exists()
        )
        result = await self._session.execute(stmt)
        return result.scalar() or False
