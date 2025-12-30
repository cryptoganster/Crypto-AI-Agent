"""Source Configuration Updated Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from uuid import UUID, uuid4

from src.rss.feed.domain.value_objects.configuration import SourceConfiguration


@dataclass(frozen=True)
class SourceConfigurationUpdated:
    """
    Evento emitido cuando se actualiza la configuración de un Source.

    Contiene información sobre los cambios realizados en la configuración
    de fetch, filtering y scheduling de una fuente RSS.
    """

    # Campos obligatorios
    source_id: str
    previous_config: Union[SourceConfiguration, Dict[str, Any]]
    new_config: Union[SourceConfiguration, Dict[str, Any]]
    updated_by: Optional[str] = None
    update_reason: Optional[str] = None

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
        return "SourceConfigurationUpdated"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "source_id": self.source_id,
            "previous_config": self._serialize_config(self.previous_config),
            "new_config": self._serialize_config(self.new_config),
            "updated_by": self.updated_by,
            "update_reason": self.update_reason,
        }

    def _serialize_config(
        self, config: Union[SourceConfiguration, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Serializa configuración para eventos."""
        if isinstance(config, SourceConfiguration):
            # Los eventos de dominio pueden serializar internamente para event sourcing
            return {
                "fetch_interval_minutes": config.fetch_interval_minutes,
                "max_articles_per_fetch": config.max_articles_per_fetch,
                "timeout_seconds": config.timeout_seconds,
                "retry_attempts": config.retry_attempts,
                "custom_headers": config.custom_headers,
                "max_concurrent_fetches": config.max_concurrent_fetches,
                "next_fetch_at": config.next_fetch_at,
                "content_filters": config.content_filters,
            }
        return config

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
    def from_dict(cls, data: Dict[str, Any]) -> "SourceConfigurationUpdated":
        """Deserializa el evento desde diccionario."""
        event_data = data.get("data", {})
        return cls(
            source_id=event_data["source_id"],
            previous_config=event_data["previous_config"],
            new_config=event_data["new_config"],
            updated_by=event_data.get("updated_by"),
            update_reason=event_data.get("update_reason"),
            event_id=UUID(data["event_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

    def get_changed_fields(self) -> Dict[str, Dict[str, Any]]:
        """Retorna solo los campos que cambiaron."""
        changes = {}
        for key in set(
            list(self.previous_config.keys()) + list(self.new_config.keys())
        ):
            old_value = self.previous_config.get(key)
            new_value = self.new_config.get(key)
            if old_value != new_value:
                changes[key] = {"from": old_value, "to": new_value}
        return changes

    def __str__(self) -> str:
        changed_count = len(self.get_changed_fields())
        return f"SourceConfigurationUpdated(source_id={self.source_id}, config_keys={list(self.new_config.keys())})"
