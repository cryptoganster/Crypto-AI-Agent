"""Query para obtener el estado de procesamiento de un artículo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetArticleProcessingStatusQuery:
    """
    Query para obtener el estado de procesamiento AI de un artículo.

    Este query consulta el estado actual del pipeline de procesamiento
    sin modificar ningún estado.

    Attributes:
        article_id: ID del artículo a consultar

    Example:
        >>> query = GetArticleProcessingStatusQuery(article_id="art-123")
        >>> result = await handler.handle(query)
        >>> print(result.state)
        'embedding'
    """

    article_id: str
