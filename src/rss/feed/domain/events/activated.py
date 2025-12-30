"""Source Activated Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceActivated:
    """
    Evento emitido cuando una source RSS se activa.

    Indica que la source está lista para ser incluida en
    las operaciones de fetch del servicio RSS.
    """

    # Todos los campos obligatorios PRIMERO
    aggregate_id: str
    source_id: str

    # Todos los campos con defaults DESPUÉS
    source_name: str = "unknown"
    previous_status: str = "inactive"
    activated_by: str = "system"
    activated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
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
        return "SourceActivated"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    # No necesitamos property para event_id ya que es un field del dataclass

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "aggregate_id": self.aggregate_id,
            "source_id": self.source_id,
            "activated_at": self.activated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceActivated":
        """Deserializa el evento desde diccionario."""
        event_data = data.get("data", {})
        return cls(
            aggregate_id=event_data["aggregate_id"],
            source_id=event_data["source_id"],
            activated_at=datetime.fromisoformat(event_data["activated_at"]),
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

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

    def __str__(self) -> str:
        return f"SourceActivated(source_id={self.source_id})"
