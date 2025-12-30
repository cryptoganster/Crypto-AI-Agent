"""ArticleContentUpdated Domain Event."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.shared.kernel import IDomainEvent


@dataclass(frozen=True)
class ArticleContentUpdated:
    """
    Domain Event emitido cuando se actualiza el contenido de un Article.

    Permite que otros componentes reaccionen a cambios en el contenido
    (regeneración de hashes, revalidación, etc.).
    """

    # Datos específicos del evento (campos requeridos primero)
    aggregate_id: str  # ID del Article aggregate que emitió el evento
    article_id: str
    source_id: str
    updated_fields: Dict[str, Any]
    updated_at: datetime

    # Campos opcionales
    previous_content_hash: Optional[str] = None
    new_content_hash: Optional[str] = None

    # Propiedades con valores por defecto (deben ir al final)
    _event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _event_type: str = field(default="ArticleContentUpdated")
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
        return "ArticleContentUpdated"

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
            "updated_fields": self.updated_fields,
            "previous_content_hash": self.previous_content_hash,
            "new_content_hash": self.new_content_hash,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleContentUpdated":
        """Deserializa el evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            article_id=data["article_id"],
            source_id=data["source_id"],
            updated_fields=data["updated_fields"],
            previous_content_hash=data.get("previous_content_hash"),
            new_content_hash=data.get("new_content_hash"),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
