"""Source Created Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class RssFeedCreated:
    """
    Evento emitido cuando se crea un nuevo Source aggregate.

    Indica que una nueva fuente RSS ha sido registrada en el sistema
    y está disponible para configuración y activación.
    """

    # Campos obligatorios
    source_id: str
    name: str
    url: str
    # Campos opcionales (con valores por defecto)
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = field(default=1)

    def __post_init__(self):
        if self.source_name is None:
            object.__setattr__(self, "source_name", self.name)
        if self.source_url is None:
            object.__setattr__(self, "source_url", self.url)

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
        return "SourceCreated"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "source_id": self.source_id,
            "name": self.name,
            "url": self.url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
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
    def from_dict(cls, data: Dict[str, Any]) -> "SourceCreated":
        """Deserializa el evento desde diccionario."""
        event_data = data.get("data", {})
        return cls(
            source_id=event_data["source_id"],
            name=event_data["name"],
            url=event_data["url"],
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            version=data.get("version", 1),
        )

    def __str__(self) -> str:
        return f"SourceCreated(source_id={self.source_id}, name='{self.name}', url='{self.url}')"


# Alias para compatibilidad hacia atrás
SourceCreated = RssFeedCreated
