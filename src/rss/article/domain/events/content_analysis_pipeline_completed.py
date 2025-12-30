"""Content Analysis Pipeline Completed Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ContentAnalysisPipelineCompleted:
    """
    Evento emitido cuando el pipeline de análisis de contenido se completa.

    Contiene métricas de las 5 fases de análisis NLP:
    1. Cálculo de métricas
    2. Detección de idioma
    3. Generación de resumen
    4. Extracción de keywords
    5. Evaluación de calidad

    Este evento puede ser escuchado por otros bounded contexts o
    para notificaciones/analytics.

    Attributes:
        pipeline_id: ID único del pipeline
        final_status: Estado final (completed, partial, failed)
        articles_processed: Total de artículos procesados
        metrics_success: Artículos con métricas calculadas
        language_success: Artículos con idioma detectado
        summary_success: Artículos con resumen generado
        keywords_success: Artículos con keywords extraídos
        quality_success: Artículos con calidad evaluada
        duration_seconds: Duración total del pipeline
    """

    # Campos obligatorios
    pipeline_id: str
    final_status: str  # completed, partial, failed
    articles_processed: int

    # Métricas por fase
    metrics_success: int = 0
    metrics_failed: int = 0
    language_success: int = 0
    language_failed: int = 0
    summary_success: int = 0
    summary_failed: int = 0
    keywords_success: int = 0
    keywords_failed: int = 0
    quality_success: int = 0
    quality_failed: int = 0

    # Métricas generales
    duration_seconds: float = 0.0
    completed_at: Optional[datetime] = None

    # Metadatos
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    def __post_init__(self):
        if self.completed_at is None:
            object.__setattr__(self, "completed_at", datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> str:
        """ID del aggregate para compatibilidad con IDomainEvent."""
        return self.pipeline_id

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "ContentAnalysisPipeline"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "ContentAnalysisPipelineCompleted"

    @property
    def event_version(self) -> str:
        """Versión del evento."""
        return str(self.version)

    @property
    def success_rate(self) -> float:
        """Tasa de éxito general del pipeline."""
        total_operations = (
            self.metrics_success
            + self.metrics_failed
            + self.language_success
            + self.language_failed
            + self.summary_success
            + self.summary_failed
            + self.keywords_success
            + self.keywords_failed
            + self.quality_success
            + self.quality_failed
        )
        if total_operations == 0:
            return 0.0

        total_success = (
            self.metrics_success
            + self.language_success
            + self.summary_success
            + self.keywords_success
            + self.quality_success
        )
        return (total_success / total_operations) * 100.0

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "pipeline_id": self.pipeline_id,
            "final_status": self.final_status,
            "articles_processed": self.articles_processed,
            "metrics_success": self.metrics_success,
            "metrics_failed": self.metrics_failed,
            "language_success": self.language_success,
            "language_failed": self.language_failed,
            "summary_success": self.summary_success,
            "summary_failed": self.summary_failed,
            "keywords_success": self.keywords_success,
            "keywords_failed": self.keywords_failed,
            "quality_success": self.quality_success,
            "quality_failed": self.quality_failed,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

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
            f"ContentAnalysisPipelineCompleted(pipeline_id={self.pipeline_id}, "
            f"status={self.final_status}, success_rate={self.success_rate:.1f}%)"
        )
