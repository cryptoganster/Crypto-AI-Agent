"""Source Bounded Context Container.

Container de inversión de dependencias para el bounded context Source.
Sigue Clean Architecture + DDD + CQRS.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.container import SharedContainer


class RssFeedContainer:
    """
    Container del bounded context Source.

    Responsabilidades:
    - Factory: SourceFactory
    - Repository: SourceWriteRepository, SourceReadRepository
    - Services: SourceHealthService, SourceValidationService
    - Commands: CreateSource, ActivateSource, RemoveSource
    - Queries: SourceQueries (CQRS Read Side)
    """

    def __init__(self, shared: "SharedContainer"):
        self._shared = shared

        # Lazy loading
        self._source_factory = None
        self._source_write_repository = None
        self._source_read_repository = None

        # Domain Services
        self._source_health_service = None
        self._source_validation_service = None

    # === UNIT OF WORK ===

    def get_uow(self):
        """
        Unit of Work para manejar transacciones.

        Usado por Command Handlers para:
        - Transacciones atómicas
        - Commit explícito
        - Rollback automático en errores

        IMPORTANTE: Cada invocación crea un nuevo UoW con nueva sesión.
        """
        from src.shared.kernel.uow import SqlAlchemyUnitOfWork

        return SqlAlchemyUnitOfWork(
            session=self._shared.session_factory(),
            logger=self._shared.logger,
        )

    # === FACTORY ===

    def get_source_factory(self):
        """SourceFactory para crear Source aggregates."""
        if self._source_factory is None:
            from src.rss.feed.domain.factories import SourceFactory

            self._source_factory = SourceFactory()
        return self._source_factory

    # === REPOSITORIES ===

    def get_source_write_repository(self):
        """SourceWriteRepository para persistir Source aggregates."""
        if self._source_write_repository is None:
            from src.rss.feed.infra.persistence.repositories.rss_feed_write_repository import (
                RssFeedWriteRepository,
            )

            self._source_write_repository = RssFeedWriteRepository(
                session=self._shared.session_factory(),
                logger=self._shared.logger,
            )
        return self._source_write_repository

    def get_source_read_repository(self):
        """SourceReadRepository para queries de lectura."""
        if self._source_read_repository is None:
            from src.rss.feed.infra.persistence.repositories.rss_feed_read_repository import (
                RssFeedReadRepository,
            )

            self._source_read_repository = RssFeedReadRepository(
                session=self._shared.session_factory(),
                logger=self._shared.logger,
            )
        return self._source_read_repository

    # === DOMAIN SERVICES ===

    def get_source_health_service(self):
        """SourceHealthService - Evalúa salud de sources."""
        if self._source_health_service is None:
            from src.rss.feed.domain.services import SourceHealthService

            self._source_health_service = SourceHealthService(
                time_provider=self._shared.time_provider,
            )
        return self._source_health_service

    def get_source_validation_service(self):
        """SourceValidationService - Valida sources."""
        if self._source_validation_service is None:
            from src.rss.feed.domain.services import SourceValidationService

            self._source_validation_service = SourceValidationService()
        return self._source_validation_service

    # === HANDLER REGISTRATION ===

    def register_handlers(self) -> None:
        """
        Registra todos los handlers del bounded context Source.

        Incluye:
        - Command handlers en Mediator
        """
        self._register_command_handlers()

        self._shared.logger.info(
            "SourceContainer: handlers registrados",
        )

    def _register_command_handlers(self) -> None:
        """Registra command handlers en el Mediator."""
        # TODO: Registrar command handlers cuando se migren
        # from src.rss.feed.app.commands import ...
        # self._shared.register_handler(Command, handler)
        pass


# Alias para compatibilidad
SourceContainer = RssFeedContainer
