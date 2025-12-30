"""Query para obtener chunks de artículos."""

from .dto import ArticleChunkDTO, ArticleChunksResultDTO
from .handler import GetArticleChunksHandler
from .query import GetArticleChunksQuery

__all__ = [
    "GetArticleChunksQuery",
    "GetArticleChunksHandler",
    "ArticleChunkDTO",
    "ArticleChunksResultDTO",
]
