"""SourceFetchedEvent - Evento emitido cuando un Source completa una operación de fetch exitosa."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceFetchedEvent:
    """
    Evento de dominio emitido cuando un Source completa exitosamente una operación de fetch.

    Este evento es crucial para la coordinación event-driven entre agregados:
    - El Article aggregate puede escuchar este evento para procesar artículos nuevos
    - Los servicios de métricas pueden actualizar estadísticas
    - Los servicios de notificación pueden alertar sobre contenido nuevo
    """

    source_id: str
    scraping_id: str
    articles_found: int
    articles_new: int
    response_time_ms: Optional[float]
    fetched_at: datetime

    # Campos requeridos por IDomainEvent
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def event_name(self) -> str:
        """Nombre único del evento."""
        return "source.fetched"

    @property
    def aggregate_id(self) -> str:
        """ID del agregado que emitió el evento."""
        return self.source_id

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Source"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "SourceFetchedEvent"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    def has_new_articles(self) -> bool:
        """Verifica si el fetch encontró artículos nuevos."""
        return self.articles_new > 0

    def was_successful(self) -> bool:
        """Verifica si el fetch fue exitoso (siempre True para este evento)."""
        return True

    def get_efficiency_ratio(self) -> float:
        """
        Calcula la eficiencia del fetch (artículos nuevos vs total).

        Returns:
            Ratio entre 0.0 y 1.0, donde 1.0 significa todos los artículos eran nuevos
        """
        if self.articles_found == 0:
            return 0.0
        return self.articles_new / self.articles_found

    def is_slow_response(self, threshold_ms: float = 5000.0) -> bool:
        """
        Verifica si el tiempo de respuesta fue lento.

        Args:
            threshold_ms: Umbral en milisegundos para considerar lento

        Returns:
            True si el response_time_ms excede el threshold
        """
        if self.response_time_ms is None:
            return False
        return self.response_time_ms > threshold_ms

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "source_id": self.source_id,
            "scraping_id": self.scraping_id,
            "articles_found": self.articles_found,
            "articles_new": self.articles_new,
            "response_time_ms": self.response_time_ms,
            "fetched_at": self.fetched_at.isoformat(),
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
    def from_dict(cls, data: Dict[str, Any]) -> "SourceFetchedEvent":
        """Deserializa el evento desde diccionario."""
        event_data = data.get("data", {})
        return cls(
            source_id=event_data["source_id"],
            scraping_id=event_data["scraping_id"],
            articles_found=event_data["articles_found"],
            articles_new=event_data["articles_new"],
            response_time_ms=event_data.get("response_time_ms"),
            fetched_at=datetime.fromisoformat(event_data["fetched_at"]),
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

    def __str__(self) -> str:
        return (
            f"SourceFetchedEvent(source_id={self.source_id}, "
            f"articles_found={self.articles_found}, "
            f"articles_new={self.articles_new}, "
            f"fetched_at={self.fetched_at})"
        )
