"""Source Added Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceAdded:
    """
    Evento emitido cuando se agrega una nueva source RSS al feed.

    Contiene información sobre la source agregada para permitir
    tracking y sincronización con otros bounded contexts.
    """

    # Campos obligatorios (sin valores por defecto)
    aggregate_id: str
    source_id: str
    source_url: str

    # Campos opcionales (con valores por defecto)
    source_name: Optional[str] = field(default=None)
    source_type: str = field(default="rss")
    added_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = field(default=1)

    # __post_init__ no necesario con default_factory

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Source"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "SourceAdded"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "aggregate_id": self.aggregate_id,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceAdded":
        """Crea evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            source_id=data["source_id"],
            source_url=data["source_url"],
            source_name=data.get("source_name"),
            added_at=(
                datetime.fromisoformat(data["added_at"])
                if "added_at" in data and data["added_at"]
                else datetime.now(timezone.utc)
            ),
            event_id=(
                UUID(data["event_id"])
                if "event_id" in data and data["event_id"]
                else uuid4()
            ),
            occurred_at=(
                datetime.fromisoformat(data["occurred_at"])
                if "occurred_at" in data and data["occurred_at"]
                else datetime.now(timezone.utc)
            ),
            version=data.get("version", 1),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte evento a diccionario."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "occurred_at": self.occurred_at.isoformat(),
            "version": self.version,
            "data": self.get_event_data(),
        }

    def __str__(self) -> str:
        return f"SourceAdded(source_id={self.source_id})"
