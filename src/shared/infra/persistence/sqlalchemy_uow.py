"""SQLAlchemy implementation of Unit of Work pattern."""

from typing import Any, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.kernel.errors import RepositoryException
from src.shared.kernel.logger import ILogger
from src.shared.kernel.uow import IUnitOfWork


class SqlAlchemyUnitOfWork(IUnitOfWork):
    """
    SQLAlchemy implementation of Unit of Work pattern.

    Garantiza que todas las operaciones de escritura dentro de un
    contexto se ejecuten como una transacción atómica.

    Uso:
        async with uow:
            await write_repository.save(aggregate)
            await uow.commit()
            # Commit explícito
            # Rollback automático si hay excepción

    Principios:
    - Transaction management centralizado
    - Commit explícito, rollback automático
    - Logging estructurado de transacciones
    - Clean Architecture compliance
    - Implementa IUnitOfWork del shared kernel
    """

    def __init__(
        self,
        session: AsyncSession,
        logger: Optional[ILogger] = None,
    ):
        """
        Inicializa Unit of Work.

        Args:
            session: Sesión AsyncIO de SQLAlchemy
            logger: Logger opcional para observabilidad
        """
        self._session = session
        self._logger = logger
        self._transaction_active = False

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        """Inicia contexto transaccional."""
        self._transaction_active = True
        self._log_debug("Transacción iniciada")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """
        Finaliza contexto transaccional.

        - Rollback automático si hay excepciones
        - Si no hay excepción pero no se hizo commit, también hace rollback
        """
        if not self._transaction_active:
            return

        try:
            if exc_type is not None:
                await self.rollback()
                self._log_error(
                    "Transacción revertida por excepción",
                    exc_type=str(exc_type),
                    exc_val=str(exc_val),
                )
        finally:
            self._transaction_active = False

    async def commit(self) -> None:
        """
        Commit explícito de la transacción.

        Persiste todos los cambios realizados en la sesión.

        Raises:
            RepositoryException: Si falla el commit
        """
        try:
            await self._session.commit()
            self._log_debug("Transacción confirmada exitosamente")
        except SQLAlchemyError as e:
            await self._session.rollback()
            self._log_error(
                "Error en commit, transacción revertida",
                error=str(e),
            )
            raise RepositoryException(f"Error en commit: {e}") from e

    async def rollback(self) -> None:
        """
        Rollback explícito de la transacción.

        Revierte todos los cambios realizados en la sesión.

        Raises:
            RepositoryException: Si falla el rollback
        """
        try:
            await self._session.rollback()
            self._log_debug("Transacción revertida exitosamente")
        except SQLAlchemyError as e:
            self._log_error(
                "Error en rollback",
                error=str(e),
            )
            raise RepositoryException(f"Error en rollback: {e}") from e

    async def flush(self) -> None:
        """
        Flush de cambios sin commit.

        Envía cambios a la BD pero mantiene transacción abierta.
        Útil para obtener IDs generados antes del commit.

        Raises:
            RepositoryException: Si falla el flush
        """
        try:
            await self._session.flush()
            self._log_debug("Flush ejecutado exitosamente")
        except SQLAlchemyError as e:
            self._log_error(
                "Error en flush",
                error=str(e),
            )
            raise RepositoryException(f"Error en flush: {e}") from e

    def _log_debug(self, message: str, **kwargs) -> None:
        """Helper para logging debug."""
        if self._logger:
            self._logger.debug(message, **kwargs)

    def _log_error(self, message: str, **kwargs) -> None:
        """Helper para logging de errores."""
        if self._logger:
            self._logger.error(message, **kwargs)


# Alias para backward compatibility
UnitOfWork = SqlAlchemyUnitOfWork
