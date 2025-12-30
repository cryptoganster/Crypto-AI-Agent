"""Interface para Unit of Work pattern."""

from abc import ABC, abstractmethod
from typing import Any, AsyncContextManager


class IUnitOfWork(ABC):
    """
    Interface para Unit of Work pattern.

    El Unit of Work mantiene una lista de objetos afectados por una
    transacción de negocio y coordina la escritura de cambios y
    resolución de problemas de concurrencia.

    Beneficios:
    - Agrupa múltiples operaciones en una transacción
    - Garantiza consistencia transaccional
    - Reduce round-trips a la base de datos
    - Simplifica manejo de transacciones
    - Facilita rollback en caso de error

    Principios:
    - Una UoW por request/comando
    - Commit explícito al final
    - Rollback automático en caso de error
    - Maneja transacciones de base de datos

    Flujo típico:
    1. Iniciar UoW (begin transaction)
    2. Ejecutar operaciones (save, delete)
    3. Commit si todo OK
    4. Rollback si hay error

    Example:
        >>> # Uso básico
        >>> async with uow:
        ...     article = await article_repo.find_by_id("123")
        ...     article.publish()
        ...     await article_repo.save(article)
        ...
        ...     source = await source_repo.find_by_id(article.source_id)
        ...     source.increment_published_count()
        ...     await source_repo.save(source)
        ...
        ...     await uow.commit()  # Commit ambos cambios
        >>>
        >>> # En un command handler
        >>> class PublishArticleHandler:
        ...     def __init__(
        ...         self,
        ...         article_repo: IArticleRepository,
        ...         source_repo: ISourceRepository,
        ...         uow: IUnitOfWork,
        ...         event_bus: IEventBus
        ...     ):
        ...         self._article_repo = article_repo
        ...         self._source_repo = source_repo
        ...         self._uow = uow
        ...         self._event_bus = event_bus
        ...
        ...     async def handle(self, command: PublishArticleCommand):
        ...         async with self._uow:
        ...             # Cargar aggregate
        ...             article = await self._article_repo.find_by_id(command.article_id)
        ...             if not article:
        ...                 raise NotFoundException("Article", command.article_id)
        ...
        ...             # Ejecutar lógica de negocio
        ...             article.publish()
        ...
        ...             # Persistir cambios
        ...             await self._article_repo.save(article)
        ...
        ...             # Commit transacción
        ...             await self._uow.commit()
        ...
        ...             # Publicar eventos (fuera de transacción)
        ...             events = article.get_uncommitted_events()
        ...             await self._event_bus.publish_all(events)
        ...             article.mark_events_as_committed()
        ...
        ...             return PublishArticleResult.success(article)
    """

    @abstractmethod
    async def commit(self) -> None:
        """
        Confirma todos los cambios de la transacción actual.

        Persiste todos los cambios realizados durante la UoW
        a la base de datos de forma atómica.

        Raises:
            RepositoryException: Si falla el commit
            ConcurrencyException: Si hay conflicto de versión

        Example:
            >>> async with uow:
            ...     await repository.save(article)
            ...     await uow.commit()
        """
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """
        Revierte todos los cambios de la transacción actual.

        Descarta todos los cambios realizados durante la UoW.
        Generalmente se llama automáticamente en caso de error.

        Example:
            >>> async with uow:
            ...     try:
            ...         await repository.save(article)
            ...         await uow.commit()
            ...     except Exception:
            ...         await uow.rollback()
            ...         raise
        """
        pass

    async def __aenter__(self) -> "IUnitOfWork":
        """
        Inicia la Unit of Work (context manager).

        Comienza una nueva transacción de base de datos.

        Returns:
            La instancia de UoW para uso en el contexto
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """
        Finaliza la Unit of Work (context manager).

        Si hay excepción, hace rollback automáticamente.
        Si no hay excepción y no se hizo commit, también hace rollback.

        Args:
            exc_type: Tipo de excepción (si hay)
            exc_val: Valor de excepción (si hay)
            exc_tb: Traceback de excepción (si hay)
        """
        if exc_type is not None:
            await self.rollback()


class IUnitOfWorkFactory(ABC):
    """
    Factory para crear instancias de Unit of Work.

    Útil cuando se necesita crear múltiples UoWs en un mismo
    request o cuando se usa dependency injection.

    Example:
        >>> class SqlAlchemyUnitOfWorkFactory(IUnitOfWorkFactory):
        ...     def __init__(self, session_factory):
        ...         self._session_factory = session_factory
        ...
        ...     def create(self) -> IUnitOfWork:
        ...         session = self._session_factory()
        ...         return SqlAlchemyUnitOfWork(session)
        >>>
        >>> # En un handler
        >>> class MyHandler:
        ...     def __init__(self, uow_factory: IUnitOfWorkFactory):
        ...         self._uow_factory = uow_factory
        ...
        ...     async def handle(self, command):
        ...         async with self._uow_factory.create() as uow:
        ...             # Usar UoW
        ...             await uow.commit()
    """

    @abstractmethod
    def create(self) -> IUnitOfWork:
        """
        Crea una nueva instancia de Unit of Work.

        Returns:
            Nueva instancia de UoW lista para usar
        """
        pass


class ITransactionalUnitOfWork(IUnitOfWork):
    """
    Interface extendida para UoW con soporte transaccional avanzado.

    Agrega funcionalidades adicionales para manejo de transacciones
    más complejas como savepoints y nested transactions.

    Example:
        >>> async with uow:
        ...     await repository.save(article1)
        ...
        ...     # Crear savepoint
        ...     savepoint = await uow.create_savepoint()
        ...
        ...     try:
        ...         await repository.save(article2)
        ...         await uow.commit()
        ...     except Exception:
        ...         # Rollback solo hasta el savepoint
        ...         await uow.rollback_to_savepoint(savepoint)
        ...         # article1 se mantiene, article2 se descarta
    """

    @abstractmethod
    async def create_savepoint(self) -> str:
        """
        Crea un savepoint en la transacción actual.

        Permite rollback parcial a un punto específico sin
        descartar toda la transacción.

        Returns:
            ID del savepoint creado
        """
        pass

    @abstractmethod
    async def rollback_to_savepoint(self, savepoint_id: str) -> None:
        """
        Hace rollback hasta un savepoint específico.

        Args:
            savepoint_id: ID del savepoint al que volver
        """
        pass

    @abstractmethod
    async def release_savepoint(self, savepoint_id: str) -> None:
        """
        Libera un savepoint (ya no se puede volver a él).

        Args:
            savepoint_id: ID del savepoint a liberar
        """
        pass


# ============================================================================
# IMPLEMENTACIÓN SQLALCHEMY
# ============================================================================


from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.kernel.logger import ILogger


class SqlAlchemyUnitOfWork(IUnitOfWork):
    """
    Implementación de Unit of Work usando SQLAlchemy.

    Maneja transacciones de SQLAlchemy de forma segura y consistente.

    Características:
    - Commit explícito requerido
    - Rollback automático si no hay commit
    - Rollback automático en caso de excepción
    - Logging detallado de operaciones

    Example:
        >>> session = session_factory()
        >>> uow = SqlAlchemyUnitOfWork(session, logger)
        >>>
        >>> async with uow:
        ...     article = await article_repo.find_by_id("123")
        ...     article.publish()
        ...     await article_repo.save(article)
        ...     await uow.commit()  # Commit explícito
        >>>
        >>> # Si hay excepción, rollback automático
        >>> async with uow:
        ...     article = await article_repo.find_by_id("123")
        ...     article.publish()
        ...     await article_repo.save(article)
        ...     raise ValueError("Error!")  # Rollback automático
    """

    def __init__(self, session: AsyncSession, logger: ILogger):
        """
        Inicializa Unit of Work.

        Args:
            session: SQLAlchemy async session
            logger: Logger para registrar operaciones
        """
        self._session = session
        self._logger = logger.bind(component="SqlAlchemyUnitOfWork")
        self._committed = False

    async def commit(self) -> None:
        """
        Commit the current transaction.

        Marca la transacción como committed para evitar rollback automático.

        Raises:
            Exception: Si falla el commit
        """
        try:
            await self._session.commit()
            self._committed = True
            self._logger.debug("Transaction committed successfully")
        except Exception as e:
            self._logger.error("Failed to commit transaction", error=str(e))
            await self.rollback()
            raise

    async def rollback(self) -> None:
        """
        Rollback the current transaction.

        Se llama automáticamente si no se hace commit explícito.

        Raises:
            Exception: Si falla el rollback
        """
        try:
            await self._session.rollback()
            self._logger.debug("Transaction rolled back")
        except Exception as e:
            self._logger.error("Failed to rollback transaction", error=str(e))
            raise

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        """
        Enter async context.

        Inicia la transacción implícitamente.

        Returns:
            La instancia de UoW
        """
        self._committed = False
        self._logger.debug("Unit of Work context entered")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """
        Exit async context.

        Si hubo excepción o no se hizo commit → rollback automático.
        Si se hizo commit → no hace nada.

        Args:
            exc_type: Tipo de excepción (si hubo)
            exc_val: Valor de excepción (si hubo)
            exc_tb: Traceback de excepción (si hubo)
        """
        if exc_type is not None:
            # Hubo excepción → rollback
            # Log COMPLETO con traceback para debugging
            import traceback

            tb_str = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))

            # Usar logging simple sin f-string anidado para evitar problemas con loguru
            error_msg = (
                "❌ EXCEPCIÓN en Unit of Work - Haciendo rollback\n"
                f"Tipo: {exc_type.__name__}\n"
                f"Mensaje: {str(exc_val)}\n"
                f"Traceback completo:\n{tb_str}"
            )

            self._logger.error(
                error_msg,
                exc_type=exc_type.__name__,
                exc_val=str(exc_val),
            )
            await self.rollback()
        elif not self._committed:
            # No hubo commit explícito → rollback
            self._logger.warning("⚠️ Unit of Work exited without commit, rolling back")
            await self.rollback()
        else:
            # Commit exitoso → no hacer nada
            self._logger.debug("✅ Unit of Work context exited successfully")


class SqlAlchemyUnitOfWorkFactory(IUnitOfWorkFactory):
    """
    Factory para crear instancias de SqlAlchemyUnitOfWork.

    Útil para dependency injection y testing.

    Example:
        >>> factory = SqlAlchemyUnitOfWorkFactory(session_factory, logger)
        >>>
        >>> # En un handler
        >>> class MyHandler:
        ...     def __init__(self, uow_factory: IUnitOfWorkFactory):
        ...         self._uow_factory = uow_factory
        ...
        ...     async def handle(self, command):
        ...         async with self._uow_factory.create() as uow:
        ...             await repository.save(aggregate)
        ...             await uow.commit()
    """

    def __init__(self, session_factory, logger: ILogger):
        """
        Inicializa factory.

        Args:
            session_factory: Factory para crear AsyncSession
            logger: Logger para UoW
        """
        self._session_factory = session_factory
        self._logger = logger

    def create(self) -> IUnitOfWork:
        """
        Crea una nueva instancia de SqlAlchemyUnitOfWork.

        Returns:
            Nueva instancia de UoW lista para usar
        """
        session = self._session_factory()
        return SqlAlchemyUnitOfWork(session, self._logger)
