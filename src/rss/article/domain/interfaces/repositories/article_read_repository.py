"""Interface para operaciones de lectura sobre RssArticle - CQRS Read Side.

CQRS ESTRICTO: Este repositorio devuelve DTOs (solo datos), NO Aggregates.

Este módulo define la interface para operaciones de lectura sobre
artículos RSS, siguiendo los principios de CQRS estricto.

El Read Repository retorna DTOs sin comportamiento.
Para modificar artículos, usar IRssArticleWriteRepository.load() que devuelve Aggregates.
"""

from typing import List, Optional, Protocol
from uuid import UUID

from src.rss.article.domain.read_models import ArticleReadModel
from src.rss.feed.domain.value_objects import SourceId


class IRssArticleReadRepository(Protocol):
    """
    Interface para operaciones de lectura sobre RssArticle (CQRS Read Side).

    CQRS ESTRICTO:
    - Devuelve Read Models (solo datos, sin comportamiento)
    - Optimizado para queries de lectura
    - NO usar para modificar artículos

    Para Write Side:
    - Usar IRssArticleWriteRepository.load() que devuelve Aggregates

    Operaciones:
    - find_by_id: Buscar artículo por ID
    - find_all: Listar artículos con filtros opcionales
    - exists: Verificar existencia de artículo
    - count: Contar artículos con filtros opcionales
    - find_by_url_and_source: Buscar por URL y source (para duplicados)

    Principios:
    - Solo operaciones de lectura básicas
    - Retorna Read Models (sin comportamiento)
    - Sin transformaciones o cálculos complejos
    - Sin lógica de negocio
    """

    async def find_by_id(self, article_id: UUID) -> Optional[ArticleReadModel]:
        """
        Busca un artículo por su ID (CQRS Read Side).

        CQRS ESTRICTO: Devuelve Read Model (solo datos), NO Aggregate.
        Para modificar, usar RssArticleWriteRepository.load().

        Args:
            article_id: UUID del artículo a buscar

        Returns:
            ArticleReadModel si existe, None en caso contrario

        Raises:
            RepositoryException: Si falla la consulta
        """
        ...

    async def find_all(
        self,
        source_id: Optional[SourceId] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ArticleReadModel]:
        """
        Busca todos los artículos con filtros opcionales (CQRS Read Side).

        Args:
            source_id: Filtrar por fuente específica (opcional)
            limit: Límite de resultados (opcional)
            offset: Offset para paginación (opcional)

        Returns:
            Lista de ArticleReadModel que cumplen los criterios

        Raises:
            RepositoryException: Si falla la consulta
        """
        ...

    async def exists(self, article_id: UUID) -> bool:
        """
        Verifica si existe un artículo con el ID dado.

        Args:
            article_id: UUID del artículo a verificar

        Returns:
            True si el artículo existe, False en caso contrario

        Raises:
            RepositoryException: Si falla la consulta
        """
        ...

    async def count(
        self,
        source_id: Optional[SourceId] = None,
    ) -> int:
        """
        Cuenta artículos con filtros opcionales.

        Args:
            source_id: Filtrar por fuente específica (opcional)

        Returns:
            Número de artículos que cumplen los criterios

        Raises:
            RepositoryException: Si falla la consulta
        """
        ...

    async def find_by_url_and_source(
        self,
        url: str,
        source_id: str,
    ) -> Optional[ArticleReadModel]:
        """
        Busca un artículo por URL y source_id (CQRS Read Side).

        Útil para verificación de duplicados durante fetch.

        Args:
            url: URL del artículo
            source_id: ID de la fuente

        Returns:
            ArticleReadModel si existe, None en caso contrario

        Raises:
            RepositoryException: Si falla la consulta
        """
        ...

    async def find_by_guid(
        self,
        guid: str,
        source_id: Optional[str] = None,
    ) -> Optional[ArticleReadModel]:
        """
        Busca un artículo por RSS GUID (CQRS Read Side).

        Útil para verificación de duplicados durante fetch usando GUID.
        El GUID es más confiable que la URL para detectar duplicados.

        Args:
            guid: GUID del feed RSS
            source_id: ID de la fuente (opcional - si se omite busca en todas las sources)

        Returns:
            ArticleReadModel si existe, None en caso contrario

        Raises:
            RepositoryException: Si falla la consulta
        """
        ...

    async def find_without_scraped_content(
        self,
        limit: Optional[int] = None,
    ) -> List[ArticleReadModel]:
        """
        Busca artículos sin contenido scrapeado (CQRS Read Side).

        Operación básica de filtrado sin lógica de negocio.
        Útil para pipelines de procesamiento.

        Args:
            limit: Límite de resultados (opcional)

        Returns:
            Lista de ArticleReadModel sin contenido scrapeado

        Raises:
            RepositoryException: Si falla la consulta
        """
        ...

    async def find_pending_processing(
        self,
        limit: Optional[int] = None,
    ) -> List[ArticleReadModel]:
        """
        Busca artículos que necesitan procesamiento (CQRS Read Side).

        Criterios:
        - Sin markdown_content O
        - Sin plaintext_content O
        - Creados recientemente (últimas 24 horas)

        Operación básica de filtrado sin lógica de negocio.
        Útil para pipelines de extracción de contenido.

        Args:
            limit: Límite de resultados (opcional, default 10)

        Returns:
            Lista de ArticleReadModel que necesitan procesamiento

        Raises:
            RepositoryException: Si falla la consulta
        """
        ...
