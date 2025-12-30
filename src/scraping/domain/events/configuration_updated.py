"""Scraping Configuration Updated Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from uuid import UUID, uuid4

from src.rss.feed.domain.value_objects.configuration import SourceConfiguration


@dataclass(frozen=True)
class ScrapingConfigurationUpdated:
    """
    Evento emitido cuando se actualiza la configuración de una operación de scraping RSS.

    Representa un cambio en la configuración específica de la operación,
    típicamente un override runtime sobre la configuración base del Source.
    """

    # Campos obligatorios (sin valores por defecto)
    scraping_id: str
    source_id: str
    previous_config: Union[SourceConfiguration, Dict[str, Any]]
    new_config: Union[SourceConfiguration, Dict[str, Any]]

    # Campos opcionales (con valores por defecto)
    updated_fields: Optional[list] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    is_runtime_override: bool = True
    changed_by: Optional[str] = None
    reason: Optional[str] = None
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    def __post_init__(self):
        if self.updated_at is None:
            object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> str:
        """ID del aggregate para compatibilidad con IDomainEvent."""
        return self.scraping_id

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
        return "ScrapingConfigurationUpdated"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "scraping_id": self.scraping_id,
            "updated_fields": self.updated_fields,
            "source_id": self.source_id,
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

    def get_configuration_changes(self) -> Dict[str, Dict[str, Any]]:
        """
        Calcula los cambios específicos entre configuraciones.

        Returns:
            Dict con 'added', 'modified', 'removed' keys
        """
        changes = {"added": {}, "modified": {}, "removed": {}}

        # Campos agregados
        for key, value in self.new_config.items():
            if key not in self.previous_config:
                changes["added"][key] = value

        # Campos modificados
        for key, value in self.new_config.items():
            if key in self.previous_config and self.previous_config[key] != value:
                changes["modified"][key] = {
                    "previous": self.previous_config[key],
                    "new": value,
                }

        # Campos removidos
        for key, value in self.previous_config.items():
            if key not in self.new_config:
                changes["removed"][key] = value

        return changes

    def has_significant_changes(self) -> bool:
        """
        Verifica si los cambios son significativos para el comportamiento de scraping.

        Returns:
            True si hay cambios que afectan el comportamiento de scraping
        """
        significant_keys = {
            "fetch_interval_minutes",
            "max_articles_per_fetch",
            "timeout_seconds",
            "retry_attempts",
        }

        changes = self.get_configuration_changes()

        # Verificar cambios en campos críticos
        for key in significant_keys:
            if (
                key in changes["added"]
                or key in changes["modified"]
                or key in changes["removed"]
            ):
                return True

        return False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScrapingConfigurationUpdated":
        """Crea evento desde diccionario."""
        return cls(
            scraping_id=data["scraping_id"],
            source_id=data["source_id"],
            previous_config=data["previous_config"],
            new_config=data["new_config"],
            is_runtime_override=data.get("is_runtime_override", True),
            changed_by=data.get("changed_by"),
            reason=data.get("reason"),
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
            "aggregate_id": self.scraping_id,
            "occurred_at": self.occurred_at.isoformat(),
            "version": self.version,
            "data": self.get_event_data(),
        }

    def __str__(self) -> str:
        changes = self.get_configuration_changes()
        change_count = sum(len(changes[key]) for key in changes)
        return f"ScrapingConfigurationUpdated(scraping_id={self.scraping_id}, source_id={self.source_id}, changes={change_count})"
