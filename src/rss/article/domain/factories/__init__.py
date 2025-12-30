"""Article domain factories."""

from src.rss.article.domain.factories.rss_article_factory import (
    FeedItem,
    RssArticleFactory,
    ValidationResult,
)

# Alias para compatibilidad
ArticleFactory = RssArticleFactory

__all__ = [
    "RssArticleFactory",
    "ArticleFactory",  # Alias
    "FeedItem",
    "ValidationResult",
]
