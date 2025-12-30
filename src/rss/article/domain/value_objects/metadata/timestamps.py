"""ArticleTimestamps Value Object - Timestamps y versión del artículo."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class RssArticleTimestamps:
    """
    Value Object para timestamps y versión del artículo.

    Encapsula created_at, updated_at y version en un solo VO inmutable.

    Attributes:
        created_at: Fecha de creación del artículo
        updated_at: Fecha de última actualización
        version: Versión del artículo (para optimistic locking)
    """

    created_at: datetime
    updated_at: datetime
    version: int = 0

    @staticmethod
    def create() -> "RssArticleTimestamps":
        """Crea timestamps iniciales con fecha actual."""
        now = datetime.now(timezone.utc)
        return RssArticleTimestamps(created_at=now, updated_at=now, version=0)

    def touch(self) -> "RssArticleTimestamps":
        """Actualiza updated_at a la fecha actual."""
        return RssArticleTimestamps(
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
            version=self.version,
        )

    def increment_version(self) -> "RssArticleTimestamps":
        """Incrementa versión y actualiza updated_at."""
        return RssArticleTimestamps(
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
            version=self.version + 1,
        )
