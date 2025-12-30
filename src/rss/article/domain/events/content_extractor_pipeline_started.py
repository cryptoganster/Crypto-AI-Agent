"""Content Extractor Pipeline Started Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ContentExtractorPipelineStarted:
    """
    Evento emitido cuando se inicia el pipeline de extracción de contenido.

    Este pipeline coordina:
    1. Scraping de HTML
    2. Extracción de plaintext
    3. Conversión a markdown

    Attributes:
        pipeline_id: ID único del pipeline
        article_ids: IDs de artículos a procesar (puede estar vacío si se consultan)
        articles_count: Número de artículos a procesar
        force_rescrape: Si se debe re-scrapear artículos ya procesados
        triggered_by: Quién/qué inició el pipeline
    """

    # Campos obligatorios
    pipeline_id: str
    articles_count: int

    # Artículos a procesar
    article_ids: tuple = field(default_factory=tuple)

    # Opciones
    force_rescrape: bool = False
    triggered_by: str = "manual"

    # Metadatos
    started_at: Optional[datetime] = None
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    def __post_init__(self):
        if self.started_at is None:
            object.__setattr__(self, "started_at", datetime.now(timezone.utc))

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
        return "ContentExtractorPipelineStarted"

    @property
    def event_version(self) -> str:
        """Versión del evento."""
        return str(self.version)

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "pipeline_id": self.pipeline_id,
            "articles_count": self.articles_count,
            "article_ids": list(self.article_ids),
            "force_rescrape": self.force_rescrape,
            "triggered_by": self.triggered_by,
            "started_at": self.started_at.isoformat() if self.started_at else None,
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
            f"ContentExtractorPipelineStarted(pipeline_id={self.pipeline_id}, "
            f"articles={self.articles_count})"
        )
