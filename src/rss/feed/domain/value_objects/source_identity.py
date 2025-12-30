"""RssFeedIdentity Value Object - Identidad del RssFeed aggregate."""

from dataclasses import dataclass
from datetime import datetime

from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl


@dataclass(frozen=True)
class RssFeedIdentity:
    """
    Value Object compuesto para identidad del RssFeed.

    Agrupa todos los campos relacionados con la identidad única
    y temporal del RssFeed aggregate.

    Attributes:
        source_id: ID único del RssFeed
        url: URL del feed RSS
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización
        version: Versión para optimistic locking
    """

    source_id: RssFeedId
    url: RssFeedUrl
    created_at: datetime
    updated_at: datetime
    version: int

    @classmethod
    def create(
        cls,
        source_id: RssFeedId,
        url: RssFeedUrl,
        created_at: datetime,
        updated_at: datetime,
        version: int = 0,
    ) -> "RssFeedIdentity":
        """
        Crea nueva instancia de RssFeedIdentity.

        Args:
            source_id: ID único del RssFeed
            url: URL del feed RSS
            created_at: Timestamp de creación
            updated_at: Timestamp de última actualización
            version: Versión inicial (default: 0)

        Returns:
            Nueva instancia de RssFeedIdentity
        """
        return cls(
            source_id=source_id,
            url=url,
            created_at=created_at,
            updated_at=updated_at,
            version=version,
        )

    def with_updated_timestamp(self, updated_at: datetime) -> "RssFeedIdentity":
        """
        Crea nueva instancia con timestamp actualizado.

        Args:
            updated_at: Nuevo timestamp de actualización

        Returns:
            Nueva instancia con timestamp actualizado
        """
        return RssFeedIdentity(
            source_id=self.source_id,
            url=self.url,
            created_at=self.created_at,
            updated_at=updated_at,
            version=self.version,
        )

    def with_incremented_version(self, updated_at: datetime) -> "RssFeedIdentity":
        """
        Crea nueva instancia con versión incrementada.

        Args:
            updated_at: Timestamp de actualización

        Returns:
            Nueva instancia con versión incrementada
        """
        return RssFeedIdentity(
            source_id=self.source_id,
            url=self.url,
            created_at=self.created_at,
            updated_at=updated_at,
            version=self.version + 1,
        )


# Alias para compatibilidad hacia atrás
SourceIdentity = RssFeedIdentity
