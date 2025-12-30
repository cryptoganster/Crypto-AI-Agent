"""Query para obtener los chunks de un artículo."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GetArticleChunksQuery:
    """
    Query para obtener los chunks de un artículo desde el vector store.

    Este query consulta los chunks almacenados en el vector store
    sin modificar ningún estado. Permite filtrar y paginar resultados.

    Attributes:
        article_id: ID del artículo cuyos chunks se quieren obtener
        include_embeddings: Si incluir los embeddings en la respuesta (default: False)
        include_summaries: Si incluir los summaries en la respuesta (default: True)
        limit: Número máximo de chunks a retornar (default: None = todos)
        offset: Número de chunks a saltar para paginación (default: 0)

    Example:
        >>> # Obtener todos los chunks con summaries
        >>> query = GetArticleChunksQuery(article_id="art-123")
        >>> result = await handler.handle(query)
        >>> len(result)
        10
        >>>
        >>> # Obtener chunks con embeddings (para análisis)
        >>> query = GetArticleChunksQuery(
        ...     article_id="art-123",
        ...     include_embeddings=True
        ... )
        >>>
        >>> # Paginación
        >>> query = GetArticleChunksQuery(
        ...     article_id="art-123",
        ...     limit=5,
        ...     offset=0
        ... )
    """

    article_id: str
    include_embeddings: bool = False
    include_summaries: bool = True
    limit: Optional[int] = None
    offset: int = 0
