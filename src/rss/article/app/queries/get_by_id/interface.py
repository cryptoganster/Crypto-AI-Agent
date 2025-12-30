"""Interface para GetArticleByIdHandler."""

from typing import Protocol

from .query import GetArticleByIdQuery
from .result import GetArticleByIdResult


class IGetArticleByIdHandler(Protocol):
    """
    Interface para GetArticleByIdHandler.

    Define el contrato para obtener un artículo por ID.
    """

    async def handle(self, query: GetArticleByIdQuery) -> GetArticleByIdResult:
        """
        Ejecuta query para obtener artículo por ID.

        Args:
            query: Query con article_id

        Returns:
            GetArticleByIdResult con ArticleDTO o error
        """
        ...
