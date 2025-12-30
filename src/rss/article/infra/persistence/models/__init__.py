"""Article persistence models."""

from src.rss.article.infra.persistence.models.rss_article_model import RssArticleModel

# Alias para compatibilidad
ArticleModel = RssArticleModel

__all__ = ["RssArticleModel", "ArticleModel"]
