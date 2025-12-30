"""
Domain Event: ArticleContentHashGenerated
Emitido cuando se genera el hash del contenido de un artículo RSS.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from src.rss.article.domain.value_objects.metadata import ArticleId
from src.rss.article.domain.value_objects.similarity import ContentHash
from src.rss.feed.domain.value_objects import SourceId
from src.shared.kernel import IDomainEvent


@dataclass(frozen=True)
class ArticleContentHashGenerated:
    """
    Evento emitido cuando se genera el hash del contenido de un artículo RSS.

    Triggers potenciales:
    - Detección de duplicados en tiempo real
    - Actualización de índices de similitud
    - Análisis de contenido único por fuente
    - Métricas de originalidad de contenido
    """

    # Datos específicos del evento (campos requeridos primero)
    article_id: ArticleId
    source_id: SourceId
    content_hash: ContentHash
    hash_algorithm: str
    generated_at: datetime
    content_length: int
    aggregate_id: str

    # Propiedades con valores por defecto (deben ir al final)
    _event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _event_type: str = field(default="ArticleContentHashGenerated")
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
        if not hasattr(self, "aggregate_type") or not self.aggregate_type:
            object.__setattr__(self, "aggregate_type", "Article")
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "article_id": str(self.article_id.value),
            "source_id": str(self.source_id.value),
            "content_hash": self.content_hash.to_dict(),
            "hash_algorithm": self.hash_algorithm,
            "generated_at": self.generated_at.isoformat(),
            "content_length": self.content_length,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleContentHashGenerated":
        """Deserializa el evento desde diccionario."""
        return cls(
            article_id=ArticleId(data["article_id"]),
            source_id=SourceId(data["source_id"]),
            content_hash=ContentHash.from_dict(data["content_hash"]),
            hash_algorithm=data["hash_algorithm"],
            generated_at=datetime.fromisoformat(data["generated_at"]),
            content_length=data["content_length"],
            aggregate_id=data["aggregate_id"],
        )

    def __str__(self) -> str:
        return f"Content hash generated for article {self.article_id.value} using {self.hash_algorithm}"
