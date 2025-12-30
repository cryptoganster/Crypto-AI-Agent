"""Scraping Pipeline Completed Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ScrapingPipelineCompleted:
    """
    Evento emitido cuando un pipeline de scraping de múltiples sources se completa.

    Este evento es emitido por el ScrapingSourcesPipelineManager cuando
    todas las sources han sido procesadas (exitosamente o con error).
    """

    # Campos obligatorios
    pipeline_id: str
    sources_processed: int
    sources_success: int
    sources_failed: int
    total_articles: int
    duration_seconds: float

    # Campos con valores por defecto
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    @property
    def event_version(self) -> str:
        """Versión del evento para compatibilidad con IDomainEvent."""
        return str(self.version)

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "ScrapingPipeline"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "ScrapingPipelineCompleted"

    @property
    def success_rate(self) -> float:
        """Tasa de éxito del pipeline."""
        if self.sources_processed == 0:
            return 0.0
        return (self.sources_success / self.sources_processed) * 100.0

    @property
    def is_fully_successful(self) -> bool:
        """Indica si todas las sources fueron exitosas."""
        return self.sources_failed == 0 and self.sources_success > 0

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "pipeline_id": self.pipeline_id,
            "sources_processed": self.sources_processed,
            "sources_success": self.sources_success,
            "sources_failed": self.sources_failed,
            "total_articles": self.total_articles,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
            "is_fully_successful": self.is_fully_successful,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convierte evento a diccionario."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.pipeline_id,
            "occurred_at": self.occurred_at.isoformat(),
            "version": self.version,
            "data": self.get_event_data(),
        }

    def __str__(self) -> str:
        return (
            f"ScrapingPipelineCompleted("
            f"pipeline_id={self.pipeline_id}, "
            f"sources={self.sources_success}/{self.sources_processed}, "
            f"articles={self.total_articles}, "
            f"duration={self.duration_seconds:.2f}s)"
        )
