"""Source Removed Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceRemoved:
    """
    Evento emitido cuando una source RSS se remueve del feed.

    Incluye información sobre la source removida y cualquier
    contenido relacionado que también fue eliminado.
    """

    # Campos obligatorios (sin valores por defecto)
    aggregate_id: str
    source_id: str

    # Campos opcionales (con valores por defecto)
    articles_removed_count: int = field(default=0)
    removal_reason: Optional[str] = field(default=None)
    removed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = field(default=1)

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Source"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "SourceRemoved"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "aggregate_id": self.aggregate_id,
            "source_id": self.source_id,
            "articles_removed_count": self.articles_removed_count,
            "removed_at": self.removed_at.isoformat() if self.removed_at else None,
            "removal_reason": self.removal_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceRemoved":
        """Crea evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            source_id=data["source_id"],
            articles_removed_count=data.get("articles_removed_count", 0),
            removal_reason=data.get("removal_reason"),
            removed_at=(
                datetime.fromisoformat(data["removed_at"])
                if "removed_at" in data and data["removed_at"]
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
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "version": self.version,
            "data": self.get_event_data(),
        }

    def __str__(self) -> str:
        return f"SourceRemoved(source_id={self.source_id}, articles_removed={self.articles_removed_count})"
