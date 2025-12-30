"""Scraping Write Repository - CQRS Command Side.

Este repositorio pertenece al bounded context Scraping e implementa
IScrapingWriteRepository para operaciones de escritura del aggregate Scraping.
"""

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.interfaces.repositories import IScrapingWriteRepository
from src.scraping.domain.value_objects import ScrapingIdentity
from src.scraping.infra.persistence.mappers import ScrapingMapper
from src.scraping.infra.persistence.models import ScrapingModel
from src.shared.kernel import IEventBus
from src.shared.kernel.logger import ILogger


class ScrapingRepositoryException(Exception):
    """Excepción base para errores del repositorio Scraping."""

    pass


class ScrapingWriteRepository(IScrapingWriteRepository):
    """
    Implementación del Write Repository para Scraping aggregate.

    CQRS Command Side - Solo operaciones de escritura.

    Principios implementados:
    - Solo Commands (save, delete, exists)
    - NO commit interno (delegado a Unit of Work)
    - Automatic event publishing
    - Clean Architecture + DDD + CQRS + SRP

    Transaction management:
    - flush() para persistir cambios en sesión
    - commit/rollback manejados por Unit of Work pattern
    """

    def __init__(
        self,
        session: AsyncSession,
        logger: Optional[ILogger] = None,
        event_publisher: Optional[IEventBus] = None,
    ):
        """
        Inicializa el Write Repository.

        Args:
            session: Sesión AsyncIO de SQLAlchemy
            logger: Logger opcional para observabilidad
            event_publisher: Publisher para eventos de dominio (opcional)
        """
        self._session = session
        self._logger = logger
        self._event_publisher = event_publisher

    async def save(self, scraping: Scraping) -> None:
        """
        Persiste o actualiza Scraping aggregate.

        - Automatic event publishing si hay event_publisher
        - Solo flush(), NO commit (delegado a Unit of Work)
        - Crea nuevo o actualiza existente automáticamente
        """
        pending_events = list(scraping.domain_events)

        try:
            self._log_debug(
                "Guardando Scraping aggregate",
                scraping_id=str(scraping.id),
                status=str(scraping.scraping_state),
                events_count=len(pending_events),
            )

            scraping_id_value = self._extract_id_value(scraping.id)

            # Verificar si ya existe
            existing = await self._session.execute(
                select(ScrapingModel).where(ScrapingModel.id == scraping_id_value)
            )
            existing_model = existing.scalar_one_or_none()

            if existing_model:
                # Actualizar existente
                ScrapingMapper.update_model_from_domain(existing_model, scraping)
                await self._session.merge(existing_model)
                self._log_debug(
                    "Scraping actualizado",
                    scraping_id=str(scraping.id),
                )
            else:
                # Crear nuevo
                model = ScrapingMapper.to_model(scraping)
                self._session.add(model)
                self._log_debug(
                    "Nuevo Scraping agregado",
                    scraping_id=str(scraping.id),
                )

            # Flush para persistir en sesión (sin commit)
            await self._session.flush()

            # Automatic event publishing
            if self._event_publisher and pending_events:
                await self._event_publisher.publish_batch(pending_events)
                self._log_info(
                    "Eventos publicados automáticamente",
                    scraping_id=str(scraping.id),
                    events_count=len(pending_events),
                    event_types=[type(event).__name__ for event in pending_events],
                )
                scraping.mark_events_as_committed()

            self._log_debug(
                "Scraping guardado exitosamente",
                scraping_id=str(scraping.id),
            )

        except SQLAlchemyError as e:
            self._log_error(
                "Error guardando Scraping",
                scraping_id=str(scraping.id),
                error=str(e),
            )
            raise ScrapingRepositoryException(f"Error guardando Scraping: {e}") from e

    async def delete(self, scraping_id: ScrapingIdentity) -> bool:
        """
        Elimina Scraping por ID.

        - Solo flush(), NO commit (delegado a Unit of Work)
        - Retorna True si eliminó, False si no existía
        """
        try:
            self._log_debug(
                "Eliminando Scraping",
                scraping_id=str(scraping_id),
            )

            scraping_id_value = self._extract_id_value(scraping_id)

            result = await self._session.execute(
                delete(ScrapingModel).where(ScrapingModel.id == scraping_id_value)
            )

            deleted = result.rowcount > 0

            # Flush para persistir cambios (sin commit)
            await self._session.flush()

            self._log_debug(
                "Scraping eliminado",
                scraping_id=str(scraping_id),
                deleted=deleted,
            )

            return deleted

        except SQLAlchemyError as e:
            self._log_error(
                "Error eliminando Scraping",
                scraping_id=str(scraping_id),
                error=str(e),
            )
            raise ScrapingRepositoryException(f"Error eliminando Scraping: {e}") from e

    async def exists(self, scraping_id: ScrapingIdentity) -> bool:
        """Verifica si existe Scraping con el ID dado."""
        try:
            scraping_id_value = self._extract_id_value(scraping_id)

            result = await self._session.execute(
                select(ScrapingModel.id).where(ScrapingModel.id == scraping_id_value)
            )

            return result.scalar_one_or_none() is not None

        except SQLAlchemyError as e:
            self._log_error(
                "Error verificando existencia",
                scraping_id=str(scraping_id),
                error=str(e),
            )
            raise ScrapingRepositoryException(
                f"Error verificando existencia: {e}"
            ) from e

    # ==================== HELPER METHODS ====================

    def _extract_id_value(self, scraping_id: ScrapingIdentity) -> str:
        """Extrae el valor string de ScrapingIdentity VO."""
        if hasattr(scraping_id, "value"):
            return str(scraping_id.value)
        return str(scraping_id)

    def _log_debug(self, message: str, **kwargs) -> None:
        """Helper para logging debug consistente."""
        if self._logger:
            self._logger.debug(message, **kwargs)

    def _log_info(self, message: str, **kwargs) -> None:
        """Helper para logging info consistente."""
        if self._logger:
            self._logger.info(message, **kwargs)

    def _log_error(self, message: str, **kwargs) -> None:
        """Helper para logging de errores consistente."""
        if self._logger:
            self._logger.error(message, **kwargs)
