"""Interfaces para Query pattern en CQRS."""

from abc import ABC, abstractmethod
from typing import Generic, Protocol, TypeVar

# Type variables para Query y Result
TQuery = TypeVar("TQuery")
TResult = TypeVar("TResult")


class IQuery(Protocol):
    """
    Interface marker para Queries en CQRS.

    Las Queries representan solicitudes de lectura de datos sin modificar
    el estado del sistema. Son objetos inmutables que encapsulan los
    parámetros necesarios para recuperar información.

    Características:
    - Inmutables (usar @dataclass(frozen=True))
    - Nombrados con sustantivos o preguntas (GetArticle, ListArticles)
    - Contienen solo parámetros de búsqueda
    - No modifican estado del sistema
    - Pueden retornar DTOs optimizados para lectura

    Separación CQRS:
    - Commands: Modifican estado, retornan éxito/fallo
    - Queries: Solo leen, retornan datos

    Example:
        >>> @dataclass(frozen=True)
        >>> class GetArticleQuery:
        ...     article_id: str
        >>>
        >>> @dataclass(frozen=True)
        >>> class ListArticlesQuery:
        ...     source_id: Optional[str] = None
        ...     status: Optional[str] = None
        ...     limit: int = 20
        ...     offset: int = 0
    """

    pass


class IQueryHandler(ABC, Generic[TQuery, TResult]):
    """
    Interface base para Query Handlers en CQRS.

    Los Query Handlers ejecutan queries de lectura y retornan datos
    optimizados para presentación. Pueden acceder directamente a la
    base de datos sin pasar por aggregates para mejor performance.

    Responsabilidades:
    - Ejecutar query de lectura
    - Transformar datos a DTOs
    - Aplicar filtros y paginación
    - Optimizar queries (joins, projections)
    - NO modificar estado del sistema

    Principios:
    - Un handler por query (Single Responsibility)
    - Puede usar query adapters optimizados
    - Retorna DTOs, no aggregates de dominio
    - Enfocado en performance de lectura
    - No usa repositories de escritura

    Optimizaciones permitidas:
    - Queries SQL directas
    - Projections (solo campos necesarios)
    - Joins optimizados
    - Caching de resultados
    - Denormalización de datos

    Example:
        >>> class GetArticleQueryHandler(IQueryHandler[GetArticleQuery, ArticleDTO]):
        ...     def __init__(self, query_adapter: IGetArticleQueryAdapter):
        ...         self._query_adapter = query_adapter
        ...
        ...     async def handle(self, query: GetArticleQuery) -> Optional[ArticleDTO]:
        ...         return await self._query_adapter.execute(query.article_id)
        >>>
        >>> class ListArticlesQueryHandler(IQueryHandler[ListArticlesQuery, PaginatedArticlesDTO]):
        ...     def __init__(self, query_adapter: IListArticlesQueryAdapter):
        ...         self._query_adapter = query_adapter
        ...
        ...     async def handle(self, query: ListArticlesQuery) -> PaginatedArticlesDTO:
        ...         articles, total = await self._query_adapter.execute(
        ...             source_id=query.source_id,
        ...             status=query.status,
        ...             limit=query.limit,
        ...             offset=query.offset
        ...         )
        ...         return PaginatedArticlesDTO(
        ...             items=articles,
        ...             total=total,
        ...             page=(query.offset // query.limit) + 1,
        ...             page_size=query.limit
        ...         )
    """

    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """
        Ejecuta la query y retorna los datos solicitados.

        Args:
            query: Query a ejecutar

        Returns:
            Datos solicitados (DTO o lista de DTOs)

        Raises:
            NotFoundException: Si el recurso no existe
            QueryException: Si hay errores en la query
        """
        pass
