"""
Módulo de eventos de infraestructura compartida.
"""

from src.shared.infra.event_bus.event_handler_registry import (
    EventHandlerRegistry,
    async_event_handler,
    event_handler,
    get_event_handler_registry,
    set_event_handler_registry,
)
from src.shared.infra.event_bus.event_publisher import (
    EventPublisher,
    create_event_publisher,
    get_event_publisher,
    set_event_publisher,
)
from src.shared.infra.event_bus.event_publisher_with_dispatch import (
    EventPublisherWithDispatch,
)
from src.shared.infra.event_bus.in_memory_event_publisher import (
    InMemoryEventPublisher,
)

__all__ = [
    # Event publishers
    "EventPublisher",
    "InMemoryEventPublisher",
    "EventPublisherWithDispatch",
    "create_event_publisher",
    "get_event_publisher",
    "set_event_publisher",
    # Event handler registry
    "EventHandlerRegistry",
    "get_event_handler_registry",
    "set_event_handler_registry",
    "event_handler",
    "async_event_handler",
]
