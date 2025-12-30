"""
Implementación SQLAlchemy de IContextPackReadRepository.

Este repositorio maneja operaciones de lectura para ContextPack.
"""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.rag.domain.aggregates.context_pack import ContextPack
from src.rag.domain.interfaces.repositories.context_pack_read_repository import (
    IContextPackReadRepository,
)
from src.rag.domain.value_objects.context_pack_id import ContextPackId
from src.rag.infra.persistence.mappers.context_pack_mapper import ContextPackMapper
from src.rag.infra.persistence.models.context_pack_model import ContextPackModel


class SqlAlchemyContextPackReadRepository(IContextPackReadRepository):
    """
    Implementación SQLAlchemy de IContextPackReadRepository.

    Maneja consultas de ContextPack aggregates.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa repositorio.

        Args:
            session: Sesión de SQLAlchemy
        """
        self._session = session
        self._mapper = ContextPackMapper()

    async def find_by_id(self, context_pack_id: ContextPackId) -> Optional[ContextPack]:
        """
        Busca ContextPack por ID.

        Args:
            context_pack_id: ID del ContextPack

        Returns:
            ContextPack si existe, None si no
        """
        stmt = select(ContextPackModel).where(
            ContextPackModel.id == str(context_pack_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._mapper.to_domain(model)

    async def find_by_article_id(
        self,
        article_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ContextPack]:
        """
        Busca ContextPacks por article_id.

        Args:
            article_id: ID del artículo
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de ContextPacks
        """
        stmt = select(ContextPackModel).where(ContextPackModel.article_id == article_id)

        # Ordenar por fecha de creación (más recientes primero)
        stmt = stmt.order_by(ContextPackModel.created_at.desc())

        if offset is not None:
            stmt = stmt.offset(offset)

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in models]

    async def exists(self, context_pack_id: ContextPackId) -> bool:
        """
        Verifica si existe un ContextPack.

        Args:
            context_pack_id: ID del ContextPack

        Returns:
            True si existe, False si no
        """
        stmt = select(
            select(ContextPackModel.id)
            .where(ContextPackModel.id == str(context_pack_id))
            .exists()
        )
        result = await self._session.execute(stmt)
        return result.scalar()

    async def count_by_article_id(self, article_id: str) -> int:
        """
        Cuenta ContextPacks de un artículo.

        Args:
            article_id: ID del artículo

        Returns:
            Número de ContextPacks
        """
        stmt = (
            select(func.count())
            .select_from(ContextPackModel)
            .where(ContextPackModel.article_id == article_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def find_recent(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> List[ContextPack]:
        """
        Busca ContextPacks recientes.

        Args:
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de ContextPacks recientes
        """
        stmt = (
            select(ContextPackModel)
            .order_by(ContextPackModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in models]
