"""Interface base para Domain Events en Domain-Driven Design."""

from datetime import datetime
from typing import Any, Dict, Generic, Protocol, TypeVar, runtime_checkable

EventId = TypeVar("EventId", covariant=True)


@runtime_checkable
class IDomainEvent(Protocol, Generic[EventId]):
    """
    Interface base para todos los eventos del dominio.

    Los eventos son hechos inmutables que han ocurrido en el dominio.
    Siguen el patrón Event Sourcing y notificación entre bounded contexts.
    """

    @property
    def event_id(self) -> EventId:
        """ID único del evento."""
        ...

    @property
    def event_type(self) -> str:
        """Tipo/nombre del evento para identificación y routing."""
        ...

    @property
    def occurred_at(self) -> datetime:
        """Timestamp de cuándo ocurrió el evento."""
        ...

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento para evolución."""
        ...

    @property
    def aggregate_id(self) -> Any:
        """ID del agregado que generó el evento."""
        ...

    @property
    def aggregate_type(self) -> str:
        """Tipo del agregado que generó el evento."""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el evento a diccionario para persistencia.
        NOTA: Para eventos de dominio, la serialización ES necesaria para event sourcing.
        """
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IDomainEvent":
        """
        Deserializa el evento desde diccionario.
        NOTA: Para eventos de dominio, la deserialización ES necesaria para event sourcing.
        """
        ...

    def __repr__(self) -> str:
        """Representación string para debugging."""
        return f"{self.event_type}(id={self.event_id}, aggregate={self.aggregate_type}:{self.aggregate_id})"


IDomainEvent = IDomainEvent
