"""ArticleReadabilityScored domain event."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass(frozen=True)
class ArticleReadabilityScored:
    """
    Event emitted when article readability score is calculated and set.

    This event is emitted by Article.set_readability_score() when the
    readability score is calculated by ArticleReadabilityService.
    """

    # Required fields
    aggregate_id: str
    article_id: str
    source_id: str
    readability_score: float
    scored_at: datetime

    # Fields with defaults (must come after required fields)
    _event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _event_type: str = field(default="ArticleReadabilityScored")
    _occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _aggregate_type: str = field(default="Article")

    @property
    def event_id(self) -> str:
        return self._event_id

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def occurred_at(self) -> datetime:
        return self.scored_at

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
            "readability_score": self.readability_score,
            "scored_at": self.scored_at.isoformat(),
        }
