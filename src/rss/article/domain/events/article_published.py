"""ArticlePublished Domain Event."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.shared.kernel import IDomainEvent


@dataclass(frozen=True)
class ArticlePublished:
    """
    Domain Event emitido cuando se publica un Article.

    Indica que el artículo ha pasado todas las validaciones
    y está listo para ser mostrado a los usuarios.
    """

    # Datos específicos del evento (campos requeridos primero)
    aggregate_id: str  # ID del Article aggregate que emitió el evento
    article_id: str
    source_id: str
    title: str
    url: str
    published_at: datetime

    # Campos opcionales
    published_by: Optional[str] = None

    # Propiedades con valores por defecto (deben ir al final)
    _event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _event_type: str = field(default="ArticlePublished")
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
        return "ArticlePublished"

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
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "published_by": self.published_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticlePublished":
        """Deserializa el evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            article_id=data["article_id"],
            source_id=data["source_id"],
            title=data["title"],
            url=data["url"],
            published_at=datetime.fromisoformat(data["published_at"]),
            published_by=data.get("published_by"),
        )
