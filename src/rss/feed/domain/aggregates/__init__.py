"""Source Bounded Context - Domain Aggregates."""

from src.rss.feed.domain.aggregates.rss_feed import RssFeed

# Alias para compatibilidad hacia atrás
Source = RssFeed

__all__ = ["RssFeed", "Source"]
