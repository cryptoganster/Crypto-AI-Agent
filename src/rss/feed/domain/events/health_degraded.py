"""
Domain Event: SourceHealthDegraded
Emitido cuando la salud de una fuente RSS se deteriora significativamente.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from src.rss.feed.domain.value_objects import SourceId


@dataclass(frozen=True)
class SourceHealthDegraded:
    """
    Evento emitido cuando una fuente RSS experimenta degradación en su salud.

    Triggers potenciales:
    - Alertas automáticas de monitoreo
    - Ajuste automático de frecuencia de fetch
    - Notificaciones a administradores
    - Análisis de patrones de fallo
    """

    source_id: SourceId
    source_name: str
    source_url: str
    previous_health_score: float
    current_health_score: float
    degradation_threshold: float
    degraded_at: datetime
    failure_count: int
    last_successful_fetch: Optional[datetime] = None
    degradation_reason: Optional[str] = None

    # Campos requeridos por IDomainEvent
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def health_score(self) -> float:
        """Alias para current_health_score para compatibilidad."""
        return self.current_health_score

    @property
    def error_count(self) -> int:
        """Alias para failure_count para compatibilidad."""
        return self.failure_count

    @property
    def last_error(self) -> Optional[str]:
        """Alias para degradation_reason para compatibilidad."""
        return self.degradation_reason

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Source"

    @property
    def aggregate_id(self) -> str:
        """ID del aggregate que emitió el evento."""
        return str(self.source_id)

    @property
    def event_type(self) -> str:
        """Tipo del evento para routing y logging."""
        return "SourceHealthDegraded"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "source_id": str(self.source_id),
            "source_name": self.source_name,
            "source_url": self.source_url,
            "previous_health_score": self.previous_health_score,
            "current_health_score": self.current_health_score,
            "degradation_threshold": self.degradation_threshold,
            "degraded_at": self.degraded_at.isoformat(),
            "failure_count": self.failure_count,
            "last_successful_fetch": (
                self.last_successful_fetch.isoformat()
                if self.last_successful_fetch
                else None
            ),
            "degradation_reason": self.degradation_reason,
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
    def from_dict(cls, data: Dict[str, Any]) -> "SourceHealthDegraded":
        """Deserializa el evento desde diccionario."""
        from src.rss.feed.domain.value_objects import SourceId

        event_data = data.get("data", {})
        return cls(
            source_id=SourceId(event_data["source_id"]),
            source_name=event_data["source_name"],
            source_url=event_data["source_url"],
            previous_health_score=event_data["previous_health_score"],
            current_health_score=event_data["current_health_score"],
            degradation_threshold=event_data["degradation_threshold"],
            degraded_at=datetime.fromisoformat(event_data["degraded_at"]),
            failure_count=event_data["failure_count"],
            last_successful_fetch=(
                datetime.fromisoformat(event_data["last_successful_fetch"])
                if event_data.get("last_successful_fetch")
                else None
            ),
            degradation_reason=event_data.get("degradation_reason"),
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

    def __str__(self) -> str:
        return f"Source '{self.source_name}' health degraded from {self.previous_health_score:.2f} to {self.current_health_score:.2f}"
