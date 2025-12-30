"""ArticleLanguageDetected domain event."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from src.shared.kernel import IDomainEvent


@dataclass(frozen=True)
class ArticleLanguageDetected:
    """
    Event emitted when article language is detected and set.

    This event is emitted by Article.update_metadata_fields(language=) when the language
    is detected by ArticleLanguageDetectionService.
    """

    # Required fields first
    aggregate_id: str
    article_id: str
    source_id: str
    language_code: str
    confidence: float
    detected_at: datetime

    # Default fields last
    _event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _event_type: str = field(default="ArticleLanguageDetected")
    _occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _aggregate_type: str = field(default="Article")

    # Event-Driven: Datos para siguiente paso
    plaintext: str = None
    """Texto plano para generación de resumen."""

    article_url: str = None
    """URL para logging."""

    article_title: str = None
    """Título para logging."""

    @property
    def event_id(self) -> str:
        return self._event_id

    @property
    def event_type(self) -> str:
        """Return the event type identifier."""
        return self._event_type

    @property
    def occurred_at(self) -> datetime:
        """Return when the event occurred."""
        return self.detected_at

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
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "article_id": self.article_id,
            "source_id": self.source_id,
            "language_code": self.language_code,
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleLanguageDetected":
        """Deserializa el evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            article_id=data["article_id"],
            source_id=data["source_id"],
            language_code=data["language_code"],
            confidence=data["confidence"],
            detected_at=datetime.fromisoformat(data["detected_at"]),
        )
