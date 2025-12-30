"""Source Status Changed Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceStatusChanged:
    """
    Evento emitido cuando cambia el status de un Source.

    Captura transiciones de estado como active -> inactive,
    healthy -> degraded, etc.
    """

    # Campos obligatorios
    source_id: str
    previous_status: str
    new_status: str
    transition_reason: Optional[str] = None
    triggered_by: Optional[str] = None

    # Metadatos del evento
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    @property
    def aggregate_id(self) -> str:
        """ID del aggregate que emitió el evento."""
        return self.source_id

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Source"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "SourceStatusChanged"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "source_id": self.source_id,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "transition_reason": self.transition_reason,
            "triggered_by": self.triggered_by,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el evento a diccionario para persistencia."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
            "data": self.get_event_data(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceStatusChanged":
        """Deserializa el evento desde diccionario."""
        event_data = data.get("data", {})
        return cls(
            source_id=event_data["source_id"],
            previous_status=event_data["previous_status"],
            new_status=event_data["new_status"],
            transition_reason=event_data.get("transition_reason"),
            triggered_by=event_data.get("triggered_by"),
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

    @property
    def is_activation(self) -> bool:
        """True si es una transición hacia estado activo."""
        return self.new_status.lower() in [
            "active",
            "enabled",
            "running",
        ]

    @property
    def is_deactivation(self) -> bool:
        """True si es una transición hacia estado inactivo."""
        return self.new_status.lower() in [
            "inactive",
            "disabled",
            "stopped",
        ]

    def __str__(self) -> str:
        return f"SourceStatusChanged(source_id={self.source_id}, {self.previous_status} -> {self.new_status})"
