"""Domain Event: ScrapingFailed - Emitido cuando una operación de scraping RSS falla."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ScrapingFailed:
    """
    Evento emitido cuando una operación completa de scraping RSS falla.

    Triggers potenciales:
    - Alertas críticas de sistema
    - Análisis de patrones de fallo
    - Ajuste automático de configuración
    - Escalado de alertas a administradores
    """

    # Campos obligatorios (sin valores por defecto)
    source_id: str
    scraping_id: str
    failed_sources: List[str]

    # Campos opcionales (con valores por defecto)
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    sources_attempted: int = 0
    sources_failed: int = 0
    failed_at: Optional[datetime] = field(default=None)
    retry_count: int = 0
    retry_scheduled: Optional[datetime] = None
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    def __post_init__(self):
        pass

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Scraping"

    @property
    def aggregate_id(self) -> str:
        """ID del aggregate para compatibilidad con IDomainEvent."""
        return self.scraping_id

    @property
    def event_version(self) -> str:
        """Versión del evento para compatibilidad con IDomainEvent."""
        return str(self.version)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte evento a diccionario."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "occurred_at": self.occurred_at.isoformat(),
            "version": self.version,
            "scraping_id": self.scraping_id,
            "source_id": self.source_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScrapingFailed":
        """Crea evento desde diccionario."""
        return cls(
            source_id=data.get("source_id", ""),
            scraping_id=data.get("scraping_id", ""),
            failed_sources=data.get("failed_sources", []),
            error_message=data.get("error_message"),
            error_type=data.get("error_type"),
            sources_attempted=data.get("sources_attempted", 0),
            sources_failed=data.get("sources_failed", 0),
            event_id=UUID(data["event_id"]) if "event_id" in data else None,
            occurred_at=(
                datetime.fromisoformat(data["occurred_at"])
                if "occurred_at" in data
                else None
            ),
            version=data.get("version", 1),
        )

    @property
    def event_type(self) -> str:
        """Tipo del evento para routing y logging."""
        return "rss.scraping.failed"

    def __str__(self) -> str:
        return f"Scraping {self.scraping_id} failed: {len(self.failed_sources)}/{self.sources_attempted} sources failed"
