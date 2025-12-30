"""Event handlers para Clustering bounded context."""

from src.clustering.app.event_handlers.on_article_embedding_generated import (
    OnArticleAIProcessedHandler,
)

__all__ = [
    "OnArticleAIProcessedHandler",
]
