"""Implementación de ISourceReadRepository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.rss.feed.domain.aggregates.rss_feed import RssFeed as Source
from src.rss.feed.domain.interfaces.repositories.rss_feed_read_repository import (
    IRssFeedReadRepository,
)
from src.rss.feed.infra.persistence.mappers import SourceMapper
from src.rss.feed.infra.persistence.models import SourceModel
from src.shared.kernel.logger import ILogger


class RssFeedReadRepository(IRssFeedReadRepository):
    """
    Implementación de IRssFeedReadRepository.

    Proporciona operaciones de lectura para Source aggregates
    usando SQLAlchemy async y PostgreSQL.
    """

    def __init__(self, session: AsyncSession, logger: ILogger):
        """
        Inicializa repository.

        Args:
            session: Sesión async de SQLAlchemy
            logger: Logger para observabilidad
        """
        self._session = session
        self._logger = logger
        self._mapper = SourceMapper()

    # ========================================================================
    # Búsqueda por ID
    # ========================================================================

    async def find_by_id(self, source_id: UUID) -> Optional[Source]:
        """Busca source por ID."""
        self._logger.debug("Buscando source por ID", source_id=str(source_id))

        stmt = select(SourceModel).where(SourceModel.id == source_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            self._logger.debug("Source no encontrado", source_id=str(source_id))
            return None

        source = self._mapper.to_domain(model)
        self._logger.debug(
            "Source encontrado",
            source_id=str(source_id),
            name=str(source.name),
        )
        return source

    async def exists(self, source_id: UUID) -> bool:
        """Verifica si existe un source."""
        self._logger.debug("Verificando existencia de source", source_id=str(source_id))

        stmt = (
            select(func.count())
            .select_from(SourceModel)
            .where(SourceModel.id == source_id)
        )
        result = await self._session.execute(stmt)
        count = result.scalar()

        exists = count > 0
        self._logger.debug(
            "Verificación de existencia completada",
            source_id=str(source_id),
            exists=exists,
        )
        return exists

    # ========================================================================
    # Búsqueda por URL
    # ========================================================================

    async def find_by_url(self, url: str) -> Optional[Source]:
        """Busca source por URL."""
        self._logger.debug("Buscando source por URL", url=url)

        stmt = select(SourceModel).where(SourceModel.url == url)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            self._logger.debug("Source no encontrado por URL", url=url)
            return None

        source = self._mapper.to_domain(model)
        self._logger.debug(
            "Source encontrado por URL",
            url=url,
            source_id=str(source.id),
        )
        return source

    async def get_id_by_url(self, url: str) -> Optional[UUID]:
        """Obtiene solo el ID de un source por URL (optimizado)."""
        self._logger.debug("Obteniendo ID por URL", url=url)

        stmt = select(SourceModel.id).where(SourceModel.url == url)
        result = await self._session.execute(stmt)
        source_id = result.scalar_one_or_none()

        if source_id:
            self._logger.debug(
                "ID encontrado por URL", url=url, source_id=str(source_id)
            )
        else:
            self._logger.debug("ID no encontrado por URL", url=url)

        return source_id

    # ========================================================================
    # Búsqueda por nombre
    # ========================================================================

    async def find_by_name(
        self,
        name: str,
        exclude_source_id: Optional[UUID] = None,
    ) -> List[Source]:
        """Busca sources por nombre exacto."""
        self._logger.debug("Buscando sources por nombre", name=name)

        stmt = select(SourceModel).where(SourceModel.name == name)

        if exclude_source_id:
            stmt = stmt.where(SourceModel.id != exclude_source_id)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        sources = [self._mapper.to_domain(m) for m in models]
        self._logger.debug(
            "Búsqueda por nombre completada",
            name=name,
            count=len(sources),
        )
        return sources

    # ========================================================================
    # Búsqueda por dominio
    # ========================================================================

    async def find_by_domain(
        self,
        domain: str,
        exclude_source_id: Optional[UUID] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Source]:
        """Busca sources por dominio."""
        self._logger.debug("Buscando sources por dominio", domain=domain)

        stmt = select(SourceModel).where(SourceModel.domain == domain)

        if exclude_source_id:
            stmt = stmt.where(SourceModel.id != exclude_source_id)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        sources = [self._mapper.to_domain(m) for m in models]
        self._logger.debug(
            "Búsqueda por dominio completada",
            domain=domain,
            count=len(sources),
        )
        return sources

    async def count_by_domain(self, domain: str) -> int:
        """Cuenta sources de un dominio."""
        self._logger.debug("Contando sources por dominio", domain=domain)

        stmt = (
            select(func.count())
            .select_from(SourceModel)
            .where(SourceModel.domain == domain)
        )
        result = await self._session.execute(stmt)
        count = result.scalar()

        self._logger.debug(
            "Conteo por dominio completado",
            domain=domain,
            count=count,
        )
        return count

    # ========================================================================
    # Listado y paginación
    # ========================================================================

    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Source]:
        """Obtiene todas las sources con paginación."""
        self._logger.debug("Obteniendo todas las sources", limit=limit, offset=offset)

        stmt = select(SourceModel).order_by(SourceModel.created_at.desc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        sources = [self._mapper.to_domain(m) for m in models]
        self._logger.debug("Sources obtenidas", count=len(sources))
        return sources

    async def find_active(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Source]:
        """Obtiene sources activas."""
        self._logger.debug("Obteniendo sources activas", limit=limit, offset=offset)

        stmt = (
            select(SourceModel)
            .where(SourceModel.status == "active")
            .order_by(SourceModel.created_at.desc())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        sources = [self._mapper.to_domain(m) for m in models]
        self._logger.debug("Sources activas obtenidas", count=len(sources))
        return sources

    async def find_by_status(
        self,
        status: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Source]:
        """Busca sources por status."""
        self._logger.debug("Buscando sources por status", status=status)

        stmt = (
            select(SourceModel)
            .where(SourceModel.status == status)
            .order_by(SourceModel.created_at.desc())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        sources = [self._mapper.to_domain(m) for m in models]
        self._logger.debug(
            "Búsqueda por status completada",
            status=status,
            count=len(sources),
        )
        return sources

    # ========================================================================
    # Conteo
    # ========================================================================

    async def count(self) -> int:
        """Cuenta total de sources."""
        self._logger.debug("Contando total de sources")

        stmt = select(func.count()).select_from(SourceModel)
        result = await self._session.execute(stmt)
        count = result.scalar()

        self._logger.debug("Conteo total completado", count=count)
        return count

    async def count_active(self) -> int:
        """Cuenta sources activas."""
        self._logger.debug("Contando sources activas")

        stmt = (
            select(func.count())
            .select_from(SourceModel)
            .where(SourceModel.status == "active")
        )
        result = await self._session.execute(stmt)
        count = result.scalar()

        self._logger.debug("Conteo de activas completado", count=count)
        return count

    # ========================================================================
    # Búsqueda de duplicados
    # ========================================================================

    async def find_duplicates_by_url(
        self,
        url: str,
        exclude_source_id: Optional[UUID] = None,
    ) -> List[Source]:
        """Encuentra duplicados por URL exacta."""
        self._logger.debug("Buscando duplicados por URL", url=url)

        stmt = select(SourceModel).where(SourceModel.url == url)

        if exclude_source_id:
            stmt = stmt.where(SourceModel.id != exclude_source_id)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        sources = [self._mapper.to_domain(m) for m in models]
        self._logger.debug(
            "Búsqueda de duplicados completada",
            url=url,
            count=len(sources),
        )
        return sources

    async def find_similar_by_url(
        self,
        url: str,
        threshold: float = 0.8,
        exclude_source_id: Optional[UUID] = None,
    ) -> List[Source]:
        """
        Encuentra sources similares por URL.

        Usa similitud de strings para encontrar URLs parecidas.
        Implementación básica usando LIKE pattern matching.
        Para similitud más avanzada, considerar pg_trgm extension.
        """
        self._logger.debug(
            "Buscando sources similares por URL",
            url=url,
            threshold=threshold,
        )

        # Extraer dominio de la URL para búsqueda básica
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
        except Exception:
            domain = ""

        if not domain:
            self._logger.warning("No se pudo extraer dominio de URL", url=url)
            return []

        # Buscar sources del mismo dominio (similitud básica)
        stmt = select(SourceModel).where(SourceModel.domain == domain)

        if exclude_source_id:
            stmt = stmt.where(SourceModel.id != exclude_source_id)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        sources = [self._mapper.to_domain(m) for m in models]
        self._logger.debug(
            "Búsqueda de similares completada",
            url=url,
            domain=domain,
            count=len(sources),
        )
        return sources
