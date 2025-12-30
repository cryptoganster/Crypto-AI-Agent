"""Implementación del registry de event handlers con decorators para auto-registration."""

import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List, Type

from src.shared.kernel import IDomainEvent
from src.shared.kernel.event_handler import (
    IAsyncEventHandler,
    IEventHandler,
    IEventHandlerRegistry,
)
from src.shared.kernel.logger import ILogger


class EventHandlerRegistry(IEventHandlerRegistry):
    """
    Registry centralizado para gestionar event handlers.

    Soporta:
    - Registro automático via decorators
    - Dispatch síncrono y asíncrono
    - Múltiples handlers por evento
    - Error handling y retry logic
    """

    def __init__(self, logger: ILogger):
        self._handlers: Dict[Type[IDomainEvent], List[IEventHandler]] = defaultdict(
            list
        )
        self._async_handlers: Dict[Type[IDomainEvent], List[IAsyncEventHandler]] = (
            defaultdict(list)
        )
        self._logger = logger.bind(component="EventHandlerRegistry")

    def register_handler(
        self, event_type: Type[IDomainEvent], handler: IEventHandler
    ) -> None:
        """Registra un handler síncrono."""
        self._handlers[event_type].append(handler)
        self._logger.debug(
            f"Event handler registrado: {type(handler).__name__} -> {event_type.__name__}",
            event_type=event_type.__name__,
            handler_type=type(handler).__name__,
        )

    def register_async_handler(
        self, event_type: Type[IDomainEvent], handler: IAsyncEventHandler
    ) -> None:
        """Registra un handler asíncrono."""
        self._async_handlers[event_type].append(handler)
        self._logger.debug(
            f"Async event handler registrado: {type(handler).__name__} -> {event_type.__name__}",
            event_type=event_type.__name__,
            handler_type=type(handler).__name__,
        )

    def get_handlers(self, event_type: Type[IDomainEvent]) -> List[IEventHandler]:
        """Obtiene handlers síncronos para un tipo de evento."""
        return self._handlers.get(event_type, [])

    def get_async_handlers(
        self, event_type: Type[IDomainEvent]
    ) -> List[IAsyncEventHandler]:
        """Obtiene handlers asíncronos para un tipo de evento."""
        return self._async_handlers.get(event_type, [])

    async def dispatch_event(self, event: IDomainEvent) -> None:
        """
        Despacha un evento a todos sus handlers registrados.

        Ejecuta primero handlers síncronos (bloquean transacción)
        y luego handlers asíncronos (background).
        """
        event_type = type(event)

        # 1. Ejecutar handlers síncronos (críticos para consistencia)
        sync_handlers = self.get_handlers(event_type)
        if sync_handlers:
            self._logger.info(
                "Ejecutando handlers síncronos",
                event_type=event_type.__name__,
                handlers_count=len(sync_handlers),
            )

            for handler in sync_handlers:
                try:
                    await handler.handle(event)
                    self._logger.debug(
                        "Handler síncrono ejecutado exitosamente",
                        event_type=event_type.__name__,
                        handler_type=type(handler).__name__,
                    )
                except Exception as e:
                    self._logger.error(
                        "Error en handler síncrono",
                        event_type=event_type.__name__,
                        handler_type=type(handler).__name__,
                        error=str(e),
                    )
                    # Los handlers síncronos fallan la transacción si hay errores
                    raise

        # 2. Ejecutar handlers asíncronos (no bloquean)
        async_handlers = self.get_async_handlers(event_type)
        if async_handlers:
            self._logger.info(
                "Programando handlers asíncronos",
                event_type=event_type.__name__,
                handlers_count=len(async_handlers),
            )

            # Ejecutar en background sin bloquear
            for handler in async_handlers:
                asyncio.create_task(self._execute_async_handler(handler, event))

    async def dispatch_events(self, events: List[IDomainEvent]) -> None:
        """Despacha múltiples eventos en lote."""
        if not events:
            return

        self._logger.info(
            "Despachando lote de eventos",
            events_count=len(events),
            event_types=[type(event).__name__ for event in events],
        )

        for event in events:
            await self.dispatch_event(event)

    async def _execute_async_handler(
        self, handler: IAsyncEventHandler, event: IDomainEvent
    ) -> None:
        """Ejecuta un handler asíncrono con retry logic."""
        max_retries = handler.max_retries

        for attempt in range(max_retries + 1):
            try:
                await handler.handle_async(event)
                self._logger.debug(
                    "Handler asíncrono ejecutado exitosamente",
                    event_type=type(event).__name__,
                    handler_type=type(handler).__name__,
                    attempt=attempt + 1,
                )
                return

            except Exception as e:
                self._logger.warning(
                    "Error en handler asíncrono",
                    event_type=type(event).__name__,
                    handler_type=type(handler).__name__,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                )

                if attempt < max_retries:
                    # Exponential backoff
                    await asyncio.sleep(2**attempt)
                else:
                    self._logger.error(
                        "Handler asíncrono falló después de todos los reintentos",
                        event_type=type(event).__name__,
                        handler_type=type(handler).__name__,
                        total_attempts=max_retries + 1,
                    )

    def get_registry_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del registry."""
        sync_handler_count = sum(len(handlers) for handlers in self._handlers.values())
        async_handler_count = sum(
            len(handlers) for handlers in self._async_handlers.values()
        )

        return {
            "sync_handlers": sync_handler_count,
            "async_handlers": async_handler_count,
            "event_types_with_sync_handlers": len(self._handlers),
            "event_types_with_async_handlers": len(self._async_handlers),
            "registered_event_types": list(
                set(list(self._handlers.keys()) + list(self._async_handlers.keys()))
            ),
        }


# Global registry instance
_registry: EventHandlerRegistry = None


def get_event_handler_registry() -> EventHandlerRegistry:
    """Obtiene instancia global del registry."""
    global _registry
    if _registry is None:
        from src.shared.config.logging_config import LoggingConfig
        from src.shared.infra.logger.loguru_service import LoguruService

        logger = LoguruService(LoggingConfig())
        _registry = EventHandlerRegistry(logger)
    return _registry


def set_event_handler_registry(registry: EventHandlerRegistry) -> None:
    """Configura registry global."""
    global _registry
    _registry = registry


# Decorators para auto-registration
def event_handler(event_type: Type[IDomainEvent]):
    """
    Decorator para registrar automáticamente un event handler.

    Usage:
        @event_handler(SourceCreated)
        class SourceCreatedHandler(IEventHandler[SourceCreated]):
            async def handle(self, event: SourceCreated) -> None:
                # Handle logic here
                pass
    """

    def decorator(handler_class: Type[IEventHandler]) -> Type[IEventHandler]:
        # Registrar en el registry global
        registry = get_event_handler_registry()
        handler_instance = handler_class()
        registry.register_handler(event_type, handler_instance)

        # Agregar metadatos para debugging
        handler_class._registered_event_type = event_type
        handler_class._auto_registered = True

        return handler_class

    return decorator


def async_event_handler(event_type: Type[IDomainEvent], max_retries: int = 3):
    """
    Decorator para registrar automáticamente un async event handler.

    Usage:
        @async_event_handler(SourceCreated, max_retries=5)
        class SourceCreatedNotifier(IAsyncEventHandler[SourceCreated]):
            async def handle_async(self, event: SourceCreated) -> None:
                # Send notifications, etc.
                pass
    """

    def decorator(handler_class: Type[IAsyncEventHandler]) -> Type[IAsyncEventHandler]:
        # Registrar en el registry global
        registry = get_event_handler_registry()
        handler_instance = handler_class()

        # Override max_retries property
        handler_instance._max_retries = max_retries

        registry.register_async_handler(event_type, handler_instance)

        # Agregar metadatos para debugging
        handler_class._registered_event_type = event_type
        handler_class._max_retries = max_retries
        handler_class._auto_registered = True

        return handler_class

    return decorator
