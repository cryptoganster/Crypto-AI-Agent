"""ChunkArticle command module."""

from .command import ChunkArticleCommand
from .handler import ChunkArticleHandler
from .result import ChunkArticleResult

__all__ = [
    "ChunkArticleCommand",
    "ChunkArticleResult",
    "ChunkArticleHandler",
]
