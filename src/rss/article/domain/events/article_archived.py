"""ArticleArchived Domain Event."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.shared.kernel import IDomainEvent


@dataclass(frozen=True)
class ArticleArchived:
    """
    Domain Event emitido cuando se archiva un Article.

    Indica que el artículo ya no está activo,
    pero se mantiene para auditoría e historial.
    """

    # Datos específicos del evento (campos requeridos primero)
    aggregate_id: str  # ID del Article aggregate que emitió el evento
    article_id: str
    source_id: str
    archived_at: datetime

    # Campos opcionales
    archived_by: Optional[str] = None
    reason: Optional[str] = None

    # Propiedades con valores por defecto (deben ir al final)
    _event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _event_type: str = field(default="ArticleArchived")
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
        return "ArticleArchived"

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el evento a diccionario."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "article_id": self.article_id,
            "source_id": self.source_id,
            "archived_at": self.archived_at.isoformat(),
            "archived_by": self.archived_by,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleArchived":
        """Deserializa el evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            article_id=data["article_id"],
            source_id=data["source_id"],
            archived_at=datetime.fromisoformat(data["archived_at"]),
            archived_by=data.get("archived_by"),
            reason=data.get("reason"),
        )
