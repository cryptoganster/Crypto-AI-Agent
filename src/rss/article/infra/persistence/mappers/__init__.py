"""Mappers para el bounded context Article."""

from src.rss.article.infra.persistence.mappers.rss_article_mapper import (
    RssArticleMapper,
)
from src.rss.article.infra.persistence.mappers.rss_article_read_model_mapper import (
    RssArticleReadModelMapper,
)

# Aliases para compatibilidad
ArticleMapper = RssArticleMapper
ArticleReadModelMapper = RssArticleReadModelMapper

__all__ = [
    "RssArticleMapper",
    "RssArticleReadModelMapper",
    "ArticleMapper",  # Alias
    "ArticleReadModelMapper",  # Alias
]
