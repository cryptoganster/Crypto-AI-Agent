"""Article repository interfaces."""

from src.rss.article.domain.interfaces.repositories.article_read_repository import (
    IRssArticleReadRepository,
)
from src.rss.article.domain.interfaces.repositories.article_write_repository import (
    IRssArticleWriteRepository,
)

# Aliases para compatibilidad
IArticleReadRepository = IRssArticleReadRepository
IArticleWriteRepository = IRssArticleWriteRepository

__all__ = [
    "IRssArticleReadRepository",
    "IRssArticleWriteRepository",
    "IArticleReadRepository",  # Alias
    "IArticleWriteRepository",  # Alias
]
