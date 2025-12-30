"""ArticleTagAdded domain event."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ArticleTagAdded:
    """
    Event emitido cuando se agrega un tag a un artículo.

    Attributes:
        aggregate_id: ID del aggregate (Article)
        article_id: ID del artículo
        source_id: ID de la fuente del artículo
        tag: Tag agregado
        added_at: Timestamp cuando se agregó el tag
        event_id: ID único del evento
        occurred_at: Timestamp del evento
    """

    aggregate_id: str
    article_id: str
    source_id: str
    tag: str
    added_at: datetime
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
