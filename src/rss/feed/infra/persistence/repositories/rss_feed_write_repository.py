"""Implementación de ISourceWriteRepository."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.rss.feed.domain.aggregates.rss_feed import RssFeed as Source
from src.rss.feed.domain.interfaces.repositories.rss_feed_write_repository import (
    IRssFeedWriteRepository,
)
from src.rss.feed.infra.persistence.mappers import SourceMapper
from src.rss.feed.infra.persistence.models import SourceModel
from src.shared.kernel.logger import ILogger


class RssFeedWriteRepository(IRssFeedWriteRepository):
    """
    Implementación de IRssFeedWriteRepository.

    Proporciona operaciones de escritura para Source aggregates
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

    async def save(self, source: Source) -> None:
        """
        Guarda un source (create o update).

        Si el source existe (por ID), lo actualiza.
        Si no existe, lo crea.
        """
        self._logger.info(
            "Guardando source",
            source_id=str(source.id),
            name=str(source.name),
        )

        try:
            # Verificar si existe
            stmt = select(SourceModel).where(SourceModel.id == source.id.value)
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Actualizar existente
                self._logger.debug(
                    "Actualizando source existente",
                    source_id=str(source.id),
                )
                self._mapper.update_model_from_domain(existing, source)
            else:
                # Crear nuevo
                self._logger.debug(
                    "Creando nuevo source",
                    source_id=str(source.id),
                )
                model = self._mapper.to_model(source)
                self._session.add(model)

            # Flush para detectar errores antes de commit
            await self._session.flush()

            self._logger.info(
                "Source guardado exitosamente",
                source_id=str(source.id),
                name=str(source.name),
            )

        except Exception as e:
            self._logger.error(
                "Error guardando source",
                source_id=str(source.id),
                error=str(e),
            )
            raise

    async def delete(self, source_id: UUID) -> None:
        """Elimina un source por ID."""
        self._logger.info("Eliminando source", source_id=str(source_id))

        try:
            # Verificar que existe
            stmt = select(SourceModel).where(SourceModel.id == source_id)
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                self._logger.warning(
                    "Source no encontrado para eliminar",
                    source_id=str(source_id),
                )
                raise ValueError(f"Source {source_id} no encontrado")

            # Eliminar
            delete_stmt = delete(SourceModel).where(SourceModel.id == source_id)
            await self._session.execute(delete_stmt)
            await self._session.flush()

            self._logger.info(
                "Source eliminado exitosamente",
                source_id=str(source_id),
            )

        except ValueError:
            # Re-lanzar ValueError (source no encontrado)
            raise
        except Exception as e:
            self._logger.error(
                "Error eliminando source",
                source_id=str(source_id),
                error=str(e),
            )
            raise

    async def delete_by_url(self, url: str) -> None:
        """Elimina un source por URL."""
        self._logger.info("Eliminando source por URL", url=url)

        try:
            # Verificar que existe
            stmt = select(SourceModel).where(SourceModel.url == url)
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                self._logger.warning(
                    "Source no encontrado para eliminar por URL",
                    url=url,
                )
                raise ValueError(f"Source con URL {url} no encontrado")

            # Eliminar
            delete_stmt = delete(SourceModel).where(SourceModel.url == url)
            await self._session.execute(delete_stmt)
            await self._session.flush()

            self._logger.info(
                "Source eliminado exitosamente por URL",
                url=url,
                source_id=str(existing.source_id),
            )

        except ValueError:
            # Re-lanzar ValueError (source no encontrado)
            raise
        except Exception as e:
            self._logger.error(
                "Error eliminando source por URL",
                url=url,
                error=str(e),
            )
            raise
