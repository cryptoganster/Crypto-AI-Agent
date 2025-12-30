"""Content Extractor Pipeline Completed Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ContentExtractorPipelineCompleted:
    """
    Evento emitido cuando el pipeline de extracción de contenido se completa.

    Contiene métricas de las 3 fases:
    1. Scraping de HTML
    2. Extracción de plaintext
    3. Conversión a markdown

    Este evento es escuchado por el ArticleProcessingPipeline para iniciar
    el procesamiento de NLP (metrics, language, summary, keywords, quality).

    Attributes:
        pipeline_id: ID único del pipeline
        final_status: Estado final (completed, partial, failed)
        articles_processed: Total de artículos procesados
        scraping_success: Artículos scrapeados exitosamente
        plaintext_success: Artículos con plaintext extraído
        markdown_success: Artículos convertidos a markdown
        duration_seconds: Duración total del pipeline
    """

    # Campos obligatorios
    pipeline_id: str
    final_status: str  # completed, partial, failed
    articles_processed: int

    # Métricas por fase
    scraping_success: int = 0
    scraping_failed: int = 0
    plaintext_success: int = 0
    plaintext_failed: int = 0
    markdown_success: int = 0
    markdown_failed: int = 0

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
        return "ContentExtractorPipeline"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "ContentExtractorPipelineCompleted"

    @property
    def event_version(self) -> str:
        """Versión del evento."""
        return str(self.version)

    @property
    def success_rate(self) -> float:
        """Tasa de éxito general del pipeline."""
        total_operations = (
            self.scraping_success
            + self.scraping_failed
            + self.plaintext_success
            + self.plaintext_failed
            + self.markdown_success
            + self.markdown_failed
        )
        if total_operations == 0:
            return 0.0

        total_success = (
            self.scraping_success + self.plaintext_success + self.markdown_success
        )
        return (total_success / total_operations) * 100.0

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "pipeline_id": self.pipeline_id,
            "final_status": self.final_status,
            "articles_processed": self.articles_processed,
            "scraping_success": self.scraping_success,
            "scraping_failed": self.scraping_failed,
            "plaintext_success": self.plaintext_success,
            "plaintext_failed": self.plaintext_failed,
            "markdown_success": self.markdown_success,
            "markdown_failed": self.markdown_failed,
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
            f"ContentExtractorPipelineCompleted(pipeline_id={self.pipeline_id}, "
            f"status={self.final_status}, success_rate={self.success_rate:.1f}%)"
        )
