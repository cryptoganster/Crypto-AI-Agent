"""
Domain Event: ArticleErrorMarked
Emitido cuando un artículo RSS ha sido marcado con error.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ArticleErrorMarked:
    """
    Domain Event emitido cuando se marca un Article con un error.

    Permite que el sistema reaccione a errores de procesamiento
    y tome acciones correctivas automatizadas.
    """

    # Campos obligatorios (sin valores por defecto)
    aggregate_id: str  # ID del Article aggregate que emitió el evento
    article_id: str
    source_id: str
    error_type: str
    error_message: str

    # Campos opcionales (con valores por defecto)
    marked_at: Optional[datetime] = None
    error_code: Optional[str] = None
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    def __post_init__(self):
        """Inicializa valores por defecto después de la construcción."""
        if self.marked_at is None:
            object.__setattr__(self, "marked_at", datetime.now(timezone.utc))

    @property
    def aggregate_type(self) -> str:
        """Tipo del aggregate que emitió el evento."""
        return "Article"

    @property
    def event_type(self) -> str:
        """Tipo del evento."""
        return "ArticleErrorMarked"

    @property
    def event_version(self) -> str:
        """Versión del esquema del evento."""
        return "1.0"

    def get_event_data(self) -> Dict[str, Any]:
        """Datos del evento para serialización."""
        return {
            "aggregate_id": self.aggregate_id,
            "article_id": self.article_id,
            "source_id": self.source_id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "marked_at": self.marked_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleErrorMarked":
        """Crea evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            article_id=data["article_id"],
            source_id=data["source_id"],
            error_type=data["error_type"],
            error_message=data["error_message"],
            error_code=data.get("error_code"),
            marked_at=(
                datetime.fromisoformat(data["marked_at"])
                if "marked_at" in data
                else None
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
        return f"ArticleErrorMarked(article_id={self.article_id}, error_type={self.error_type})"
