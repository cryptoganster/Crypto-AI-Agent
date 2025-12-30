"""Shared Infrastructure Container.

Container de infraestructura compartida entre todos los bounded contexts.
Migrado desde src/bootstrap/containers/shared_infrastructure.py
"""

# asyncio.current_task no es necesario sin async_scoped_session
from typing import Callable, Type

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.shared.config import AppConfig
from src.shared.config.ai_processing_config import AIProcessingConfig
from src.shared.infra.event_bus import (
    EventHandlerRegistry,
    EventPublisher,
    EventPublisherWithDispatch,
)
from src.shared.infra.logger import LoguruService
from src.shared.infra.mediator import Mediator
from src.shared.kernel import (
    IEventBus,
    IMediator,
    ITimeProvider,
    SystemTimeProvider,
)
from src.shared.kernel.logger import ILogger


class SharedContainer:
    """
    Container de infraestructura compartida entre todos los bounded contexts.

    Contiene ÚNICAMENTE:
    - Database engine y session factory
    - Logger (LoguruService)
    - Event publisher y registry
    - Time provider
    - Mediator

    NO contiene:
    - Repositories (van en cada bounded context)
    - Domain Services (van en cada bounded context)
    - Query Adapters (van en cada bounded context)
    - Command Handlers (van en cada bounded context)
    """

    def __init__(self, config: AppConfig):
        """
        Inicializa la infraestructura compartida.

        Args:
            config: Configuración de la aplicación
        """
        self.config = config

        # === DATABASE ===
        # Usar QueuePool para reutilizar conexiones y mejorar performance
        # NullPool creaba una nueva conexión por cada operación (muy lento)
        self.engine = create_async_engine(
            config.database.connection_string,
            echo=config.debug,  # Logging SQL solo en debug
            future=True,
            # QueuePool con limits razonables
            pool_size=10,  # Conexiones en el pool
            max_overflow=20,  # Conexiones adicionales permitidas
            pool_timeout=30,  # Timeout para obtener conexión del pool
            pool_recycle=3600,  # Reciclar conexiones cada 1 hora
            pool_pre_ping=True,  # Verificar conexión antes de usar
            isolation_level="READ COMMITTED",  # Ver commits de otras transacciones
            connect_args={
                "server_settings": {"search_path": config.database.schema},
                # Removido command_timeout porque causaba TimeoutError en INSERT
                # asyncpg usará su timeout por defecto
            },
        )

        # Usar async_sessionmaker directamente (sin scoped session)
        # para evitar problemas de aislamiento entre sesiones
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Event listener para configurar search_path en cada sesión
        from sqlalchemy import event
        from sqlalchemy.ext.asyncio import AsyncConnection

        @event.listens_for(self.engine.sync_engine, "connect")
        def set_search_path(dbapi_connection, connection_record):
            """Configura search_path en cada conexión nueva."""
            cursor = dbapi_connection.cursor()
            cursor.execute(f"SET search_path TO {config.database.schema}")
            cursor.close()

        # === LOGGING ===
        self.logger: ILogger = LoguruService(config.logging)

        # === AI PROCESSING CONFIG ===
        self.ai_processing_config: AIProcessingConfig = AIProcessingConfig.from_env()

        # === TIME PROVIDER ===
        self.time_provider: ITimeProvider = SystemTimeProvider()

        # === EVENT INFRASTRUCTURE ===
        self.event_handler_registry = EventHandlerRegistry(logger=self.logger)

        self.event_publisher: IEventBus = EventPublisherWithDispatch(
            base_publisher=EventPublisher(logger=self.logger),
            event_handler_registry=self.event_handler_registry,
            logger=self.logger,
        )

        # === MEDIATOR ===
        self.mediator: IMediator = self._create_mediator()

    def _create_mediator(self) -> IMediator:
        """Crea el Mediator con handler registry vacío."""
        handler_registry = {}

        mediator = Mediator(
            handler_registry=handler_registry,
            event_bus=self.event_publisher,
            logger=self.logger,
        )

        self.logger.info("Mediator inicializado")

        return mediator

    def register_handler(self, command_type: Type, handler: Callable) -> None:
        """
        Registra un handler en el Mediator.

        Args:
            command_type: Tipo del comando/query (clase)
            handler: Handler que procesa el comando/query
        """
        self.mediator._handler_registry[command_type] = handler

        self.logger.debug(
            "Handler registrado",
            command_type=command_type.__name__,
            handler=handler.__class__.__name__,
        )

    def log_registered_handlers_summary(self) -> None:
        """Loggea resumen de handlers registrados."""
        registered_handlers = self.mediator._handler_registry
        handler_count = len(registered_handlers)
        handler_names = [cmd.__name__ for cmd in registered_handlers.keys()]

        self.logger.info(
            "Handlers registrados en Mediator",
            count=handler_count,
            handlers=handler_names,
        )

    async def dispose(self):
        """Libera recursos de infraestructura."""
        if self.engine:
            await self.engine.dispose()
