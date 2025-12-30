"""Implementación SQLAlchemy de ISemanticClusterWriteRepository."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clustering.domain.aggregates.semantic_cluster import SemanticCluster
from src.clustering.domain.interfaces.repositories import (
    ISemanticClusterWriteRepository,
)
from src.clustering.infra.persistence.mappers import SemanticClusterMapper
from src.clustering.infra.persistence.models import SemanticClusterModel


class SqlAlchemySemanticClusterWriteRepository(ISemanticClusterWriteRepository):
    """
    Implementación SQLAlchemy de ISemanticClusterWriteRepository.

    Responsabilidades:
    - Persistir SemanticCluster aggregates
    - Eliminar clusters
    - NO hacer commit (Unit of Work pattern)

    Attributes:
        _session: Sesión de SQLAlchemy
        _mapper: Mapper para conversión domain ↔ model
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa repository.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session
        self._mapper = SemanticClusterMapper()

    async def save(self, cluster: SemanticCluster) -> None:
        """
        Guarda o actualiza un cluster semántico.

        NO hace commit - el commit es responsabilidad del Unit of Work.

        Args:
            cluster: Cluster a guardar

        Examples:
            >>> cluster = SemanticCluster.create("Label", centroid)
            >>> await repository.save(cluster)
            >>> await session.flush()  # Flush, NO commit
        """
        # Buscar si existe
        stmt = select(SemanticClusterModel).where(
            SemanticClusterModel.id == str(cluster.id)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Actualizar existente
            self._mapper.update_model(existing, cluster)
        else:
            # Crear nuevo
            model = self._mapper.to_model(cluster)
            self._session.add(model)

        # Flush para detectar errores, pero NO commit
        await self._session.flush()

    async def delete(self, cluster_id: str) -> None:
        """
        Elimina un cluster semántico.

        NO hace commit - el commit es responsabilidad del Unit of Work.

        Args:
            cluster_id: ID del cluster a eliminar

        Examples:
            >>> await repository.delete("cluster-123")
            >>> await session.flush()  # Flush, NO commit
        """
        stmt = delete(SemanticClusterModel).where(SemanticClusterModel.id == cluster_id)
        await self._session.execute(stmt)

        # Flush para detectar errores, pero NO commit
        await self._session.flush()
