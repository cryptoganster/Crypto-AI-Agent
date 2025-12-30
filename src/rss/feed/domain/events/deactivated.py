"""Source Deactivated Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceDeactivated:
    """
    Evento emitido cuando una source RSS se desactiva.

    Indica que la source no será incluida en futuras
    operaciones de fetch hasta que se reactive.
    """

    # Campos obligatorios (sin valores por defecto)
    aggregate_id: str
    source_id: str

    # Campos opcionales (con valores por defecto)
    source_name: str = "unknown"
    deactivated_by: str = "system"
    reason: Optional[str] = None
    deactivated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Source"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "SourceDeactivated"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "aggregate_id": self.aggregate_id,
            "source_id": self.source_id,
            "reason": self.reason,
            "deactivated_at": self.deactivated_at.isoformat(),
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
    def from_dict(cls, data: Dict[str, Any]) -> "SourceDeactivated":
        """Deserializa el evento desde diccionario."""
        event_data = data.get("data", {})
        return cls(
            aggregate_id=event_data["aggregate_id"],
            source_id=event_data["source_id"],
            reason=event_data.get("reason"),
            deactivated_at=datetime.fromisoformat(event_data["deactivated_at"]),
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

    def __str__(self) -> str:
        return f"SourceDeactivated(source_id={self.source_id}, reason={self.reason})"
