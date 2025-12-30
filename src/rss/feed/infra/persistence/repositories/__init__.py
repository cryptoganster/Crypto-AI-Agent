"""Repository implementations para Source bounded context."""

from .rss_feed_read_repository import RssFeedReadRepository
from .rss_feed_write_repository import RssFeedWriteRepository

# Aliases para compatibilidad
SourceReadRepository = RssFeedReadRepository
SourceWriteRepository = RssFeedWriteRepository

__all__ = [
    "RssFeedReadRepository",
    "RssFeedWriteRepository",
    "SourceReadRepository",  # Alias
    "SourceWriteRepository",  # Alias
]
