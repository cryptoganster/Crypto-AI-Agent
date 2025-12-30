"""Interface para RssArticle Write Repository (CQRS Command Side)."""

from typing import Protocol

from src.rss.article.domain.aggregates import RssArticle
from src.rss.article.domain.value_objects.metadata import RssArticleId


class IRssArticleWriteRepository(Protocol):
    """
    Interface para operaciones de ESCRITURA del aggregate RssArticle.

    Siguiendo CQRS, este repositorio solo maneja Commands (mutaciones).
    Las Queries se manejan mediante Query Adapters especializados.

    Principios:
    - Operaciones de escritura (save, delete)
    - load() para cargar aggregate a modificar (CQRS estricto válido)
    - Event publishing automático al persistir
    - Adherencia estricta a Clean Architecture + DDD
    - NO contiene queries (find_*, búsquedas, filtros, etc.)

    Para queries, usar IRssArticleReadRepository.

    Nota: load() NO es violación CQRS (Vaughn Vernon, DDD Distilled):
    - Es el mismo bounded context
    - Retorna aggregate completo (no DTO)
    - Es para modificación, no para queries
    - Semántica diferente a find_by_id() (query)
    """

    async def load(self, article_id: RssArticleId) -> RssArticle | None:
        """
        Carga RssArticle aggregate para modificación.

        Necesario para Command Handlers que modifican aggregates existentes.
        Retorna el aggregate completo (no DTO).

        Args:
            article_id: ID del RssArticle a cargar

        Returns:
            RssArticle aggregate o None si no existe
        """
        ...

    async def save(self, article: RssArticle) -> None:
        """
        Persiste o actualiza un RssArticle aggregate.

        - Automatic event publishing si hay event_publisher configurado
        - Crea nuevo registro o actualiza existente automáticamente

        Args:
            article: Aggregate a persistir

        Raises:
            RepositoryException: Si falla la persistencia
        """
        ...

    async def delete(self, article_id: RssArticleId) -> bool:
        """
        Elimina un RssArticle por su ID.

        Args:
            article_id: ID del RssArticle a eliminar

        Returns:
            True si se eliminó, False si no existía

        Raises:
            RepositoryException: Si falla la eliminación
        """
        ...
