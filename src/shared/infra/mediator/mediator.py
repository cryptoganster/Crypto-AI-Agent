"""Implementación del Mediator pattern para CQRS."""

from typing import Any, Callable, Dict, Type

from src.shared.kernel import IEventBus, IMediator
from src.shared.kernel.logger import ILogger


class HandlerNotFoundError(Exception):
    """Excepción lanzada cuando no se encuentra un handler para un comando/query."""

    pass


class Mediator(IMediator):
    """
    Implementación del Mediator pattern para CQRS.

    Responsabilidades:
    - Enrutar comandos/queries a sus handlers
    - Resolver handlers del container dinámicamente
    - Aplicar cross-cutting concerns (logging, metrics)
    - Delegar publicación de eventos al Event Bus

    Example:
        >>> mediator = Mediator(handler_registry={}, event_bus=event_bus, logger=logger)
        >>> result = await mediator.send(MyCommand(param="value"))
    """

    def __init__(
        self,
        handler_registry: Dict[Type, Callable],
        event_bus: IEventBus,
        logger: ILogger,
    ):
        """
        Inicializa el Mediator.

        Args:
            handler_registry: Diccionario que mapea tipos de request a handlers
            event_bus: Event bus para publicar eventos de dominio
            logger: Logger para logging estructurado
        """
        self._handler_registry = handler_registry
        self._event_bus = event_bus
        self._logger = logger.bind(component="Mediator")

    async def send(self, request: object) -> object:
        """
        Envía un comando/query al handler apropiado.

        Args:
            request: Comando o query a procesar

        Returns:
            Resultado del handler

        Raises:
            HandlerNotFoundError: Si no hay handler registrado para el request
        """
        request_type = type(request)
        request_name = request_type.__name__

        # Verificar que existe un handler registrado
        if request_type not in self._handler_registry:
            self._logger.error(
                "No handler registered for request",
                request_type=request_name,
                available_handlers=list(
                    handler.__name__ for handler in self._handler_registry.keys()
                ),
            )
            raise HandlerNotFoundError(
                f"No handler registered for {request_name}. "
                f"Available handlers: {list(self._handler_registry.keys())}"
            )

        handler = self._handler_registry[request_type]

        # Log dispatch
        self._logger.debug(
            "Dispatching request",
            request_type=request_name,
            handler=handler.__class__.__name__,
        )

        try:
            # Ejecutar handler
            result = await handler.handle(request)

            self._logger.debug(
                "Request handled successfully",
                request_type=request_name,
                handler=handler.__class__.__name__,
            )

            return result

        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            self._logger.error(
                f"Error handling request | request_type={request_name} | handler={handler.__class__.__name__} | error={str(e)}\n{tb}"
            )
            raise

    async def publish(self, event: Any) -> None:
        """
        Publica un evento de dominio.

        Delega la publicación al Event Bus.

        Args:
            event: Evento de dominio a publicar
        """
        event_type = type(event).__name__

        self._logger.debug("Publishing event via Event Bus", event_type=event_type)

        try:
            await self._event_bus.publish(event)

            self._logger.debug("Event published successfully", event_type=event_type)

        except Exception as e:
            self._logger.error(
                "Error publishing event", event_type=event_type, error=str(e)
            )
            raise
