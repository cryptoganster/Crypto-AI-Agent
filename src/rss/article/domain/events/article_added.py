"""Article Added Domain Event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ArticleAdded:
    """
    Evento emitido cuando se agrega un nuevo artículo RSS al feed.

    Contiene información sobre el artículo agregado y su source
    de origen para tracking y procesamiento posterior.
    """

    # Campos obligatorios (sin valores por defecto)
    aggregate_id: str
    source_id: str
    article_id: str
    article_title: str

    # Campos opcionales (con valores por defecto)
    article_url: Optional[str] = None
    added_at: Optional[datetime] = None
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    def __post_init__(self):
        if self.added_at is None:
            object.__setattr__(self, "added_at", datetime.now(timezone.utc))

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Article"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "ArticleAdded"

    @property
    def event_version(self) -> str:
        """Versión del evento."""
        return str(self.version)

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "aggregate_id": self.aggregate_id,
            "source_id": self.source_id,
            "article_id": self.article_id,
            "article_title": self.article_title,
            "article_url": self.article_url,
            "added_at": self.added_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleAdded":
        """Crea evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            source_id=data["source_id"],
            article_id=data["article_id"],
            article_title=data["article_title"],
            article_url=data["article_url"],
            added_at=(
                datetime.fromisoformat(data["added_at"]) if "added_at" in data else None
            ),
            event_id=UUID(data["event_id"]) if "event_id" in data else None,
            occurred_at=(
                datetime.fromisoformat(data["occurred_at"])
                if "occurred_at" in data
                else None
            ),
            version=data.get("version", 1),
        )

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
        return f"ArticleAdded(source_id={self.source_id}, title={self.article_title[:30]}...)"
