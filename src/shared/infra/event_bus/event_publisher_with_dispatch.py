"""Event Publisher con automatic event handler dispatch."""

from typing import List

from src.shared.infra.event_bus.event_handler_registry import EventHandlerRegistry
from src.shared.infra.event_bus.event_publisher import EventPublisher
from src.shared.kernel import IDomainEvent, IEventBus
from src.shared.kernel.logger import ILogger


class EventPublisherWithDispatch(IEventBus):
    """
    Event Publisher que combina logging con event handler dispatch.

    Flujo:
    1. Publica evento via EventPublisher (persistencia/logging)
    2. Despacha evento a event handlers registrados (side effects)
    """

    def __init__(
        self,
        base_publisher: EventPublisher,
        event_handler_registry: EventHandlerRegistry,
        logger: ILogger,
    ):
        self._base_publisher = base_publisher
        self._event_handler_registry = event_handler_registry
        self._logger = logger.bind(component="EventPublisherWithDispatch")

    async def publish(self, event: IDomainEvent) -> None:
        """Publica un evento individual con handler dispatch."""
        # 1. Publicación base (logging/persistencia)
        await self._base_publisher.publish(event)

        # 2. Dispatch a event handlers
        try:
            await self._event_handler_registry.dispatch_event(event)
        except Exception as e:
            self._logger.error(
                "Error despachando evento a handlers",
                event_type=type(event).__name__,
                event_id=getattr(event, "event_id", None),
                error=str(e),
            )
            # Re-raise para mantener transaccionalidad
            raise

    async def publish_batch(self, events: List[IDomainEvent]) -> None:
        """Publica múltiples eventos con handler dispatch."""
        if not events:
            return

        # 1. Publicación base en lote
        await self._base_publisher.publish_batch(events)

        # 2. Dispatch a event handlers
        try:
            await self._event_handler_registry.dispatch_events(events)
        except Exception as e:
            self._logger.error(
                "Error despachando lote de eventos a handlers",
                events_count=len(events),
                error=str(e),
            )
            # Re-raise para mantener transaccionalidad
            raise

    async def publish_and_wait(
        self, event: IDomainEvent, timeout_seconds: float = 30.0
    ) -> None:
        """Publica evento y espera confirmación."""
        # Para esta implementación, simplemente publicamos
        # En futuras implementaciones con message brokers, aquí esperaríamos ACK
        await self.publish(event)

    async def publish_all(self, events: List[IDomainEvent]) -> None:
        """Publica múltiples eventos de dominio en lote (método requerido por IEventBus)."""
        await self.publish_batch(events)

    async def subscribe(self, event_type: type[IDomainEvent], handler) -> None:
        """
        Suscribe un handler a un tipo específico de evento.

        Delega al event handler registry para gestionar suscripciones.
        """
        self._event_handler_registry.register_handler(event_type, handler)

    async def unsubscribe(self, event_type: type[IDomainEvent], handler) -> None:
        """
        Desuscribe un handler de un tipo de evento.

        Nota: El registry actual no soporta desuscripción dinámica.
        Este método está aquí para cumplir con la interface IEventBus.
        """
        self._logger.warning(
            f"unsubscribe() llamado pero no implementado en EventHandlerRegistry. "
            f"Los handlers se registran al inicio y no se pueden desuscribir dinámicamente."
        )

    def get_statistics(self) -> dict:
        """Combina estadísticas del publisher base y registry."""
        base_stats = self._base_publisher.get_statistics()
        registry_stats = self._event_handler_registry.get_registry_stats()

        return {**base_stats, "event_handlers": registry_stats}


# Legacy compatibility alias - DEPRECATED
EnhancedDomainEventPublisher = EventPublisherWithDispatch
