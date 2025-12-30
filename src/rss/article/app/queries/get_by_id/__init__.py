"""GetArticleByIdQuery - Query Handler completo."""

from .handler import GetArticleByIdHandler
from .interface import IGetArticleByIdHandler
from .query import GetArticleByIdQuery
from .result import ArticleDTO, GetArticleByIdResult

__all__ = [
    "GetArticleByIdQuery",
    "GetArticleByIdHandler",
    "GetArticleByIdResult",
    "ArticleDTO",
    "IGetArticleByIdHandler",
]
