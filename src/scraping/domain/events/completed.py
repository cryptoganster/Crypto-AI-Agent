"""Scraping Completed Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ScrapingCompleted:
    """
    Evento emitido cuando una operación de scraping RSS se completa.

    Contiene métricas de la operación completada y el estado final
    para análisis de rendimiento y troubleshooting.
    """

    # Campos obligatorios (sin valores por defecto)
    aggregate_id: str
    source_id: str
    scraping_id: str
    final_status: str  # completed, failed, partial, timeout, cancelled

    # Campos opcionales (con valores por defecto)
    articles_scraped: int = 0
    sources_processed: int = 0
    duration_seconds: Optional[float] = None
    sources_successful: int = 0
    sources_failed: int = 0
    articles_discovered: int = 0
    articles_new: int = 0
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    def __post_init__(self):
        if self.completed_at is None:
            object.__setattr__(self, "completed_at", datetime.now(timezone.utc))

    @property
    def event_version(self) -> str:
        """Versión del evento para compatibilidad con IDomainEvent."""
        return str(self.version)

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Scraping"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "ScrapingCompleted"

    @property
    def success_rate(self) -> float:
        """Tasa de éxito de la operación."""
        total_sources = self.sources_successful + self.sources_failed
        if total_sources == 0:
            return 0.0
        return (self.sources_successful / total_sources) * 100.0

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "aggregate_id": self.aggregate_id,
            "source_id": self.source_id,
            "scraping_id": self.scraping_id,
            "final_status": self.final_status,
            "sources_successful": self.sources_successful,
            "sources_failed": self.sources_failed,
            "articles_discovered": self.articles_discovered,
            "articles_new": self.articles_new,
            "completed_at": self.completed_at.isoformat(),
            "processing_time_seconds": self.processing_time_seconds,
            "success_rate": self.success_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScrapingCompleted":
        """Crea evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            source_id=data["source_id"],
            scraping_id=data["scraping_id"],
            final_status=data["final_status"],
            sources_successful=data.get("sources_successful", 0),
            sources_failed=data.get("sources_failed", 0),
            articles_discovered=data.get("articles_discovered", 0),
            articles_new=data.get("articles_new", 0),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if "completed_at" in data
                else None
            ),
            processing_time_seconds=data.get("processing_time_seconds"),
            event_id=UUID(data["event_id"]) if "event_id" in data else None,
            occurred_at=(
                datetime.fromisoformat(data["occurred_at"])
                if "occurred_at" in data
                else None
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
        return f"ScrapingCompleted(source_id={self.source_id}, scraping_id={self.scraping_id}, status={self.final_status}, success_rate={self.success_rate:.1f}%)"
