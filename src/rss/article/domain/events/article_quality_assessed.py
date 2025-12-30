"""ArticleQualityAssessed Domain Event."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.shared.kernel import IDomainEvent


@dataclass(frozen=True)
class ArticleQualityAssessed:
    """
    Domain Event emitido cuando se evalúa la calidad de un Article.

    Permite que otros componentes reaccionen a cambios en la
    calidad del contenido (filtros, rankings, etc.).
    """

    # Datos específicos del evento (campos requeridos primero)
    aggregate_id: str  # ID del Article aggregate que emitió el evento
    article_id: str
    source_id: str
    quality_score: float
    quality_metrics: Dict[str, float]
    assessed_at: datetime

    # Campos opcionales
    assessment_criteria: Optional[Dict[str, Any]] = None
    assessed_by: Optional[str] = None

    # Propiedades con valores por defecto (deben ir al final)
    _event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _event_type: str = field(default="ArticleQualityAssessed")
    _occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _aggregate_type: str = field(default="Article")

    # Implementación del protocolo IDomainEvent mediante properties
    @property
    def event_id(self) -> str:
        return self._event_id

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def occurred_at(self) -> datetime:
        return self._occurred_at

    @property
    def aggregate_type(self) -> str:
        return self._aggregate_type

    @property
    def event_version(self) -> str:
        return "1.0"

    @property
    def event_name(self) -> str:
        """Nombre del evento."""
        return self.event_type

    def to_dict(self) -> dict:
        """Serializa el evento a diccionario."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "article_id": self.article_id,
            "source_id": self.source_id,
            "quality_score": self.quality_score,
            "quality_metrics": self.quality_metrics,
            "assessed_at": self.assessed_at.isoformat(),
            "assessed_by": self.assessed_by,
            "assessment_criteria": self.assessment_criteria,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleQualityAssessed":
        """Crea instancia desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            article_id=data["article_id"],
            source_id=data["source_id"],
            quality_score=data["quality_score"],
            quality_metrics=data["quality_metrics"],
            assessed_at=datetime.fromisoformat(data["assessed_at"]),
            assessment_criteria=data.get("assessment_criteria"),
            assessed_by=data.get("assessed_by"),
        )
