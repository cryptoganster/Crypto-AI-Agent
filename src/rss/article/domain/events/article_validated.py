"""
Domain Event: ArticleValidated
Emitido cuando un artículo RSS ha sido validado exitosamente.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from src.shared.kernel import IDomainEvent


@dataclass(frozen=True)
class ArticleValidated:
    """
    Domain Event emitido cuando se valida un Article.

    Indica que el artículo ha pasado todas las validaciones
    de contenido, formato y calidad requeridas.
    """

    # Datos específicos del evento (campos requeridos primero)
    aggregate_id: str  # ID del Article aggregate que emitió el evento
    article_id: str
    source_id: str
    validation_status: str
    validated_at: datetime
    validation_score: float
    quality_level: str = "unknown"

    # Propiedades con valores por defecto (deben ir al final)
    _event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _event_type: str = field(default="ArticleValidated")
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

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el evento a diccionario."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "article_id": self.article_id,
            "source_id": self.source_id,
            "validation_status": self.validation_status,
            "validated_at": self.validated_at.isoformat(),
            "validation_score": self.validation_score,
            "quality_level": self.quality_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleValidated":
        """Crea instancia desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            article_id=data["article_id"],
            source_id=data["source_id"],
            validation_status=data["validation_status"],
            validated_at=datetime.fromisoformat(data["validated_at"]),
            validation_score=data["validation_score"],
            quality_level=data.get("quality_level", "unknown"),
        )
