"""Scraping Started Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ScrapingStarted:
    """
    Evento emitido cuando se inicia una nueva operación de scraping RSS.

    Contiene información sobre la configuración de la operación,
    el número de sources que se procesarán, y las opciones de scraping
    que serán utilizadas por el ScrapingPipeline.

    Las opciones de scraping fluyen a través de este evento para
    mantener la arquitectura event-driven y CQRS estricto.
    """

    # Campos obligatorios (sin valores por defecto)
    aggregate_id: str
    source_id: str
    scraping_id: str
    sources_count: int
    max_concurrent: int

    # Lista de source_ids a procesar (para el Pipeline)
    source_ids: tuple = field(default_factory=tuple)

    # Opciones de scraping (transportadas al Pipeline)
    timeout_seconds: int = 30
    quality_threshold: Optional[float] = None
    enable_quality_filter: bool = True
    enable_deduplication: bool = True
    force_refresh: bool = False
    max_items_per_source: Optional[int] = None

    # Metadatos
    started_at: Optional[datetime] = None
    session_name: Optional[str] = None
    triggered_by: str = "manual"
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    def __post_init__(self):
        if self.started_at is None:
            object.__setattr__(self, "started_at", datetime.now(timezone.utc))

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
        return "ScrapingStarted"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "aggregate_id": self.aggregate_id,
            "source_id": self.source_id,
            "scraping_id": self.scraping_id,
            "sources_count": self.sources_count,
            "source_ids": list(self.source_ids),
            "max_concurrent": self.max_concurrent,
            "timeout_seconds": self.timeout_seconds,
            "quality_threshold": self.quality_threshold,
            "enable_quality_filter": self.enable_quality_filter,
            "enable_deduplication": self.enable_deduplication,
            "force_refresh": self.force_refresh,
            "max_items_per_source": self.max_items_per_source,
            "session_name": self.session_name,
            "triggered_by": self.triggered_by,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScrapingStarted":
        """Crea evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            source_id=data["source_id"],
            scraping_id=data["scraping_id"],
            sources_count=data["sources_count"],
            source_ids=tuple(data.get("source_ids", [])),
            max_concurrent=data["max_concurrent"],
            timeout_seconds=data.get("timeout_seconds", 30),
            quality_threshold=data.get("quality_threshold"),
            enable_quality_filter=data.get("enable_quality_filter", True),
            enable_deduplication=data.get("enable_deduplication", True),
            force_refresh=data.get("force_refresh", False),
            max_items_per_source=data.get("max_items_per_source"),
            session_name=data.get("session_name"),
            triggered_by=data.get("triggered_by", "manual"),
            started_at=(
                datetime.fromisoformat(data["started_at"])
                if data.get("started_at")
                else None
            ),
            event_id=UUID(data["event_id"]) if "event_id" in data else uuid4(),
            occurred_at=(
                datetime.fromisoformat(data["occurred_at"])
                if "occurred_at" in data
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
        return (
            f"ScrapingStarted(scraping_id={self.scraping_id}, "
            f"sources={self.sources_count}, quality={self.quality_threshold})"
        )
