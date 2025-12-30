"""Source Fetch Stopped Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceFetchStopped:
    """
    Evento emitido cuando se detiene un fetch en un Source.

    Indica que un proceso de fetch ha terminado (exitoso, fallido o cancelado)
    y proporciona información sobre el resultado final.
    """

    # Campos obligatorios
    source_id: str
    scraping_id: str
    stop_reason: str  # completed, failed, cancelled, timeout
    duration_ms: int
    articles_found: int = 0
    articles_new: int = 0
    error_message: Optional[str] = None

    # Metadatos adicionales
    response_time_ms: Optional[float] = None
    bytes_processed: Optional[int] = None
    http_status_code: Optional[int] = None

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
        return "SourceFetchStopped"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "source_id": self.source_id,
            "scraping_id": self.scraping_id,
            "stop_reason": self.stop_reason,
            "duration_ms": self.duration_ms,
            "articles_found": self.articles_found,
            "articles_new": self.articles_new,
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms,
            "bytes_processed": self.bytes_processed,
            "http_status_code": self.http_status_code,
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
    def from_dict(cls, data: Dict[str, Any]) -> "SourceFetchStopped":
        """Deserializa el evento desde diccionario."""
        event_data = data.get("data", {})
        return cls(
            source_id=event_data["source_id"],
            scraping_id=event_data["scraping_id"],
            stop_reason=event_data["stop_reason"],
            duration_ms=event_data["duration_ms"],
            articles_found=event_data.get("articles_found", 0),
            articles_new=event_data.get("articles_new", 0),
            error_message=event_data.get("error_message"),
            response_time_ms=event_data.get("response_time_ms"),
            bytes_processed=event_data.get("bytes_processed"),
            http_status_code=event_data.get("http_status_code"),
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

    @property
    def was_successful(self) -> bool:
        """True si el fetch se completó exitosamente."""
        return self.stop_reason == "completed"

    @property
    def was_failed(self) -> bool:
        """True si el fetch falló por error."""
        return self.stop_reason == "failed"

    @property
    def was_cancelled(self) -> bool:
        """True si el fetch fue cancelado."""
        return self.stop_reason == "cancelled"

    @property
    def was_timeout(self) -> bool:
        """True si el fetch terminó por timeout."""
        return self.stop_reason == "timeout"

    @property
    def found_new_articles(self) -> bool:
        """True si se encontraron artículos nuevos."""
        return self.articles_new > 0

    @property
    def duration_seconds(self) -> float:
        """Duración en segundos."""
        return self.duration_ms / 1000.0

    def __str__(self) -> str:
        status = "✓" if self.was_successful else "✗"
        return f"SourceFetchStopped({status} source_id={self.source_id}, scraping_id={self.scraping_id}, reason={self.stop_reason})"
