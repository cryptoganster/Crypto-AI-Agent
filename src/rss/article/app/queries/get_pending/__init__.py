"""GetPendingArticlesQuery - Query Handler completo."""

from .handler import GetPendingArticlesHandler
from .query import GetPendingArticlesQuery
from .result import GetPendingArticlesResult, PendingArticleDTO

__all__ = [
    "GetPendingArticlesQuery",
    "GetPendingArticlesHandler",
    "GetPendingArticlesResult",
    "PendingArticleDTO",
]
