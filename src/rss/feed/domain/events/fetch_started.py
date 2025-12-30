"""Source Fetch Started Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceFetchStarted:
    """
    Evento emitido cuando se inicia un fetch en un Source.

    Indica que una fuente RSS ha comenzado un proceso de fetch
    y permite tracking del progreso y coordinación con otros componentes.
    """

    # Campos obligatorios
    source_id: str
    scraping_id: str
    scraping_type: str = "scheduled"  # scheduled, manual, retry
    timeout_seconds: int = 30
    max_articles: Optional[int] = None
    filters_applied: Optional[Dict[str, Any]] = None

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
        return "SourceFetchStarted"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "source_id": self.source_id,
            "scraping_id": self.scraping_id,
            "scraping_type": self.scraping_type,
            "timeout_seconds": self.timeout_seconds,
            "max_articles": self.max_articles,
            "filters_applied": self.filters_applied,
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
    def from_dict(cls, data: Dict[str, Any]) -> "SourceFetchStarted":
        """Deserializa el evento desde diccionario."""
        event_data = data.get("data", {})
        return cls(
            source_id=event_data["source_id"],
            scraping_id=event_data["scraping_id"],
            scraping_type=event_data.get("scraping_type", "scheduled"),
            timeout_seconds=event_data.get("timeout_seconds", 30),
            max_articles=event_data.get("max_articles"),
            filters_applied=event_data.get("filters_applied"),
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

    @property
    def is_manual_scraping(self) -> bool:
        """True si es un scraping manual iniciado por usuario."""
        return self.scraping_type == "manual"

    @property
    def is_retry_scraping(self) -> bool:
        """True si es un scraping de reintento después de error."""
        return self.scraping_type == "retry"

    @property
    def has_article_limit(self) -> bool:
        """True si tiene límite de artículos."""
        return self.max_articles is not None and self.max_articles > 0

    def __str__(self) -> str:
        return f"SourceFetchStarted(source_id={self.source_id}, scraping_id={self.scraping_id}, type={self.scraping_type})"
