"""Article Content Pipeline Completed Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ArticleContentPipelineCompleted:
    """
    Evento emitido cuando un pipeline de contenido de artículos se completa.

    Este evento es emitido por el ArticleContentPipelineManager cuando
    todos los artículos han sido procesados (scraping, plaintext, markdown).
    """

    # Campos obligatorios
    pipeline_id: str
    articles_processed: int
    articles_completed: int
    articles_failed: int
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
        return "ArticleContentPipeline"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "ArticleContentPipelineCompleted"

    @property
    def success_rate(self) -> float:
        """Tasa de éxito del pipeline."""
        if self.articles_processed == 0:
            return 0.0
        return (self.articles_completed / self.articles_processed) * 100.0

    @property
    def is_fully_successful(self) -> bool:
        """Indica si todos los artículos fueron exitosos."""
        return self.articles_failed == 0 and self.articles_completed > 0

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "pipeline_id": self.pipeline_id,
            "articles_processed": self.articles_processed,
            "articles_completed": self.articles_completed,
            "articles_failed": self.articles_failed,
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
            f"ArticleContentPipelineCompleted("
            f"pipeline_id={self.pipeline_id}, "
            f"articles={self.articles_completed}/{self.articles_processed}, "
            f"duration={self.duration_seconds:.2f}s)"
        )
