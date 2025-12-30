"""ArticleKeywordsExtracted domain event."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from src.shared.kernel import IDomainEvent


@dataclass(frozen=True)
class ArticleKeywordsExtracted:
    """
    Event emitted when keywords are extracted from an article.

    This event is emitted by Article.set_keywords() when keywords are
    extracted by ArticleKeywordService.
    """

    # Required fields first
    aggregate_id: str
    article_id: str
    source_id: str
    keywords: tuple[str, ...]  # Immutable tuple
    extracted_at: datetime

    # Default fields last
    _event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _event_type: str = field(default="ArticleKeywordsExtracted")
    _occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _aggregate_type: str = field(default="Article")

    def __post_init__(self):
        """Ensure keywords is a tuple (immutable)."""
        if isinstance(self.keywords, list):
            object.__setattr__(self, "keywords", tuple(self.keywords))

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
        return self.extracted_at

    @property
    def aggregate_type(self) -> str:
        """Return the aggregate type."""
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
            "keywords": list(self.keywords),
            "extracted_at": self.extracted_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleKeywordsExtracted":
        """Deserializa el evento desde diccionario."""
        return cls(
            aggregate_id=data["aggregate_id"],
            article_id=data["article_id"],
            source_id=data["source_id"],
            keywords=tuple(data["keywords"]),
            extracted_at=datetime.fromisoformat(data["extracted_at"]),
        )
