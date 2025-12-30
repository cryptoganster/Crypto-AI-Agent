"""
Domain Event: SourceHealthRecovered
Emitido cuando una fuente RSS se recupera de problemas de salud.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from src.rss.feed.domain.value_objects import SourceId


@dataclass(frozen=True)
class SourceHealthRecovered:
    """
    Evento emitido cuando una fuente RSS se recupera y vuelve a estar saludable.

    Triggers potenciales:
    - Restaurar frecuencia normal de fetch
    - Cancelar alertas activas
    - Notificaciones de recuperación
    - Análisis de patrones de recuperación
    """

    # Campos del evento
    source_id: SourceId
    source_name: str
    source_url: str
    previous_health_score: float
    current_health_score: float
    recovery_threshold: float
    recovered_at: datetime
    downtime_duration: Optional[int] = None  # En segundos
    recovery_trigger: Optional[str] = None  # ej: "automatic_retry", "manual_check"

    # Campos requeridos por IDomainEvent
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def health_score(self) -> float:
        """Alias para current_health_score para compatibilidad."""
        return self.current_health_score

    @property
    def recovery_time_minutes(self) -> Optional[float]:
        """Tiempo de recuperación en minutos para compatibilidad."""
        if self.downtime_duration is not None:
            return self.downtime_duration / 60.0
        return None

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
        return "SourceHealthRecovered"

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
            "recovery_threshold": self.recovery_threshold,
            "recovered_at": self.recovered_at.isoformat(),
            "downtime_duration": self.downtime_duration,
            "recovery_trigger": self.recovery_trigger,
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
    def from_dict(cls, data: Dict[str, Any]) -> "SourceHealthRecovered":
        """Deserializa el evento desde diccionario."""
        from src.rss.feed.domain.value_objects import SourceId

        event_data = data.get("data", {})
        return cls(
            source_id=SourceId(event_data["source_id"]),
            source_name=event_data["source_name"],
            source_url=event_data["source_url"],
            previous_health_score=event_data["previous_health_score"],
            current_health_score=event_data["current_health_score"],
            recovery_threshold=event_data["recovery_threshold"],
            recovered_at=datetime.fromisoformat(event_data["recovered_at"]),
            downtime_duration=event_data.get("downtime_duration"),
            recovery_trigger=event_data.get("recovery_trigger"),
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

    def __str__(self) -> str:
        downtime_info = (
            f" after {self.downtime_duration} seconds" if self.downtime_duration else ""
        )
        return f"Source '{self.source_name}' recovered{downtime_info} (Health: {self.current_health_score:.2f})"
