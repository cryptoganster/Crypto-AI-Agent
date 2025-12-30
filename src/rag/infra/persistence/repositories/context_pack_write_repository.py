"""
Implementación SQLAlchemy de IContextPackWriteRepository.

Este repositorio maneja operaciones de escritura para ContextPack.
"""

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.rag.domain.aggregates.context_pack import ContextPack
from src.rag.domain.interfaces.repositories.context_pack_write_repository import (
    IContextPackWriteRepository,
)
from src.rag.domain.value_objects.context_pack_id import ContextPackId
from src.rag.infra.persistence.mappers.context_pack_mapper import ContextPackMapper
from src.rag.infra.persistence.models.context_pack_model import ContextPackModel


class SqlAlchemyContextPackWriteRepository(IContextPackWriteRepository):
    """
    Implementación SQLAlchemy de IContextPackWriteRepository.

    Maneja persistencia de ContextPack aggregates.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa repositorio.

        Args:
            session: Sesión de SQLAlchemy
        """
        self._session = session
        self._mapper = ContextPackMapper()

    async def save(self, context_pack: ContextPack) -> None:
        """
        Guarda ContextPack.

        Si el ContextPack existe, lo actualiza.
        Si no existe, lo crea.

        Args:
            context_pack: ContextPack a guardar
        """
        # Buscar si existe
        stmt = select(ContextPackModel).where(
            ContextPackModel.id == str(context_pack.id)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Actualizar existente
            self._mapper.update_model(existing, context_pack)
        else:
            # Crear nuevo
            model = self._mapper.to_model(context_pack)
            self._session.add(model)

        await self._session.flush()

    async def delete(self, context_pack_id: ContextPackId) -> None:
        """
        Elimina ContextPack por ID.

        Args:
            context_pack_id: ID del ContextPack a eliminar
        """
        stmt = delete(ContextPackModel).where(
            ContextPackModel.id == str(context_pack_id)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def delete_by_article_id(self, article_id: str) -> None:
        """
        Elimina todos los ContextPacks de un artículo.

        Args:
            article_id: ID del artículo
        """
        stmt = delete(ContextPackModel).where(ContextPackModel.article_id == article_id)
        await self._session.execute(stmt)
        await self._session.flush()
