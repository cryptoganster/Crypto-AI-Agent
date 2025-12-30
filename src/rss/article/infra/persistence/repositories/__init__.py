"""Repository implementations para Article bounded context."""

from .rss_article_read_repository import RssArticleReadRepository
from .rss_article_write_repository import RssArticleWriteRepository

# Aliases para compatibilidad
ArticleReadRepository = RssArticleReadRepository
ArticleWriteRepository = RssArticleWriteRepository

__all__ = [
    "RssArticleReadRepository",
    "RssArticleWriteRepository",
    "ArticleReadRepository",  # Alias
    "ArticleWriteRepository",  # Alias
]
