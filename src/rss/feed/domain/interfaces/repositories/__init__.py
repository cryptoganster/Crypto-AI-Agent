"""Repository interfaces para Source bounded context."""

from .rss_feed_read_repository import IRssFeedReadRepository
from .rss_feed_write_repository import IRssFeedWriteRepository

# Aliases para compatibilidad
ISourceReadRepository = IRssFeedReadRepository
ISourceWriteRepository = IRssFeedWriteRepository

__all__ = [
    "IRssFeedReadRepository",
    "IRssFeedWriteRepository",
    "ISourceReadRepository",  # Alias
    "ISourceWriteRepository",  # Alias
]
