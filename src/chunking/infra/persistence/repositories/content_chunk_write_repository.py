"""Write repository implementation for ContentChunk aggregate."""

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.chunking.domain.aggregates.content_chunk import ContentChunk
from src.chunking.domain.interfaces.repositories.content_chunk_write_repository import (
    IContentChunkWriteRepository,
)
from src.chunking.infra.persistence.mappers.content_chunk_mapper import (
    ContentChunkMapper,
)
from src.chunking.infra.persistence.models.content_chunk_model import (
    ContentChunkModel,
)
from src.knowledge.domain.value_objects.source_reference import SourceReference


class SqlAlchemyContentChunkWriteRepository(IContentChunkWriteRepository):
    """
    Implementación SQLAlchemy de IContentChunkWriteRepository.

    Responsabilidades:
    - Persistir ContentChunk aggregates
    - NO hacer commit (usa Unit of Work pattern)
    - Usar mapper para conversión domain ↔ ORM
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa repository.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._mapper = ContentChunkMapper()

    async def save(self, aggregate: ContentChunk) -> None:
        """
        Guarda ContentChunk aggregate.

        Si el aggregate ya existe, actualiza.
        Si no existe, crea nuevo.

        NO hace commit - usa Unit of Work pattern.

        Args:
            aggregate: ContentChunk aggregate a guardar
        """
        # Verificar si existe
        stmt = select(ContentChunkModel).where(
            ContentChunkModel.id == str(aggregate.id)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Actualizar existente
            self._mapper.update_model(existing, aggregate)
        else:
            # Crear nuevo
            model = self._mapper.to_model(aggregate)
            self._session.add(model)

        # Flush para detectar errores, pero NO commit
        await self._session.flush()

    async def delete(self, chunk_id: str) -> None:
        """
        Elimina ContentChunk por ID.

        NO hace commit - usa Unit of Work pattern.

        Args:
            chunk_id: ID del ContentChunk a eliminar
        """
        stmt = delete(ContentChunkModel).where(ContentChunkModel.id == chunk_id)
        await self._session.execute(stmt)

        # Flush para detectar errores, pero NO commit
        await self._session.flush()

    async def delete_by_source(self, source: SourceReference) -> None:
        """
        Elimina todos los chunks de una fuente.

        NO hace commit - usa Unit of Work pattern.

        Args:
            source: SourceReference (source_id + source_type)
        """
        stmt = delete(ContentChunkModel).where(
            and_(
                ContentChunkModel.source_id == source.source_id,
                ContentChunkModel.source_type == source.source_type,
            )
        )
        await self._session.execute(stmt)

        # Flush para detectar errores, pero NO commit
        await self._session.flush()

    async def delete_by_article_id(self, article_id: str) -> None:
        """
        DEPRECATED: Usar delete_by_source() en su lugar.

        Elimina todos los chunks de un artículo.

        NO hace commit - usa Unit of Work pattern.

        Args:
            article_id: ID del artículo
        """
        stmt = delete(ContentChunkModel).where(
            ContentChunkModel.article_id == article_id
        )
        await self._session.execute(stmt)

        # Flush para detectar errores, pero NO commit
        await self._session.flush()
