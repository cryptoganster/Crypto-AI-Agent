"""Source Metrics Updated Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceMetricsUpdated:
    """
    Evento emitido cuando se actualizan las métricas de un Source.

    Se emite después de cada fetch para mantener las métricas actualizadas
    y permitir monitoreo en tiempo real del rendimiento de las fuentes.
    """

    # Campos obligatorios
    source_id: str
    total_fetches: int
    successful_fetches: int
    failed_fetches: int
    total_articles_discovered: int
    total_articles_new: int
    success_rate: float
    last_fetch_at: Optional[datetime] = None
    average_response_time_ms: float = 0.0

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
        return "SourceMetricsUpdated"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "source_id": self.source_id,
            "total_fetches": self.total_fetches,
            "successful_fetches": self.successful_fetches,
            "failed_fetches": self.failed_fetches,
            "total_articles_discovered": self.total_articles_discovered,
            "total_articles_new": self.total_articles_new,
            "success_rate": self.success_rate,
            "last_fetch_at": (
                self.last_fetch_at.isoformat() if self.last_fetch_at else None
            ),
            "average_response_time_ms": self.average_response_time_ms,
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
    def from_dict(cls, data: Dict[str, Any]) -> "SourceMetricsUpdated":
        """Deserializa el evento desde diccionario."""
        event_data = data.get("data", {})
        return cls(
            source_id=event_data["source_id"],
            total_fetches=event_data["total_fetches"],
            successful_fetches=event_data["successful_fetches"],
            failed_fetches=event_data["failed_fetches"],
            total_articles_discovered=event_data["total_articles_discovered"],
            total_articles_new=event_data["total_articles_new"],
            success_rate=event_data["success_rate"],
            last_fetch_at=(
                datetime.fromisoformat(event_data["last_fetch_at"])
                if event_data.get("last_fetch_at")
                else None
            ),
            average_response_time_ms=event_data.get("average_response_time_ms", 0.0),
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

    @property
    def is_healthy(self) -> bool:
        """True si las métricas indican una fuente saludable."""
        return self.success_rate >= 80.0

    def __str__(self) -> str:
        return f"SourceMetricsUpdated(source_id={self.source_id}, success_rate={self.success_rate:.1f}%)"
