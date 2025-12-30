"""Implementación en memoria del publicador para testing."""

from typing import Dict, List

from src.shared.kernel import IDomainEvent, IEventBus

# Type alias para compatibilidad
Event = IDomainEvent


class InMemoryEventPublisher(IEventBus):
    """
    Implementación en memoria del publicador para testing.

    Almacena todos los eventos en memoria para verificación en tests.
    """

    def __init__(self):
        self.published_events: List[Event] = []
        self.event_history: Dict[str, List[Event]] = {}

    # Métodos requeridos por IEventBus interface
    async def publish(self, event: IDomainEvent) -> None:
        """Publica un evento de dominio individual (método requerido por interface)."""
        await self.publish_event(event)

    async def publish_batch(self, events: List[IDomainEvent]) -> None:
        """Publica múltiples eventos de dominio en lote (método requerido por interface)."""
        await self.publish_events(events)

    async def publish_and_wait(
        self, event: IDomainEvent, timeout_seconds: float = 30.0
    ) -> None:
        """Publica un evento y espera confirmación (método requerido por interface)."""
        await self.publish_event(event)

    async def publish_all(self, events: List[IDomainEvent]) -> None:
        """Publica múltiples eventos de dominio en lote (método requerido por IEventBus)."""
        await self.publish_events(events)

    async def subscribe(self, event_type: type[IDomainEvent], handler) -> None:
        """
        Suscribe un handler a un tipo específico de evento.

        Nota: InMemoryEventPublisher no soporta handlers dinámicos.
        Este método está aquí para cumplir con la interface IEventBus.
        """
        pass  # No-op para testing

    async def unsubscribe(self, event_type: type[IDomainEvent], handler) -> None:
        """
        Desuscribe un handler de un tipo de evento.

        Nota: InMemoryEventPublisher no soporta handlers dinámicos.
        Este método está aquí para cumplir con la interface IEventBus.
        """
        pass  # No-op para testing

    async def publish_event(self, event: Event) -> None:
        """Publicar evento en memoria."""
        self.published_events.append(event)

        event_type = event.__class__.__name__
        if event_type not in self.event_history:
            self.event_history[event_type] = []
        self.event_history[event_type].append(event)

    async def publish_events(self, events: List[Event]) -> None:
        """Publicar múltiples eventos en memoria."""
        for event in events:
            await self.publish_event(event)

    async def publish_events_async(self, events: List[Event]) -> None:
        """Publicar eventos asíncronamente (mismo comportamiento para testing)."""
        await self.publish_events(events)

    def clear_events(self) -> None:
        """Limpiar todos los eventos (útil para testing)."""
        self.published_events.clear()
        self.event_history.clear()

    def get_events_of_type(self, event_type: type) -> List[Event]:
        """Obtener eventos de un tipo específico."""
        return [e for e in self.published_events if isinstance(e, event_type)]

    def count_events_of_type(self, event_type: type) -> int:
        """Contar eventos de un tipo específico."""
        return len(self.get_events_of_type(event_type))


# Legacy compatibility alias - DEPRECATED
InMemoryDomainEventPublisher = InMemoryEventPublisher
