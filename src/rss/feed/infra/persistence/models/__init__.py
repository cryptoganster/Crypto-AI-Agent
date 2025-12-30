"""Source persistence models."""

from src.rss.feed.infra.persistence.models.rss_feed_model import RssFeedModel

# Alias para compatibilidad
SourceModel = RssFeedModel

__all__ = ["RssFeedModel", "SourceModel"]
