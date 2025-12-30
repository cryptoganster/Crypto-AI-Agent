"""Implementación de IRssArticleReadRepository.

CQRS ESTRICTO: Este repositorio devuelve Read Models (solo datos), NO Aggregates.
Para modificar artículos, usar RssArticleWriteRepository.load() que devuelve Aggregates.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.rss.article.domain.interfaces.repositories import (
    IRssArticleReadRepository,
)
from src.rss.article.domain.read_models import ArticleReadModel
from src.rss.article.infra.persistence.mappers.rss_article_read_model_mapper import (
    RssArticleReadModelMapper,
)
from src.rss.article.infra.persistence.models import RssArticleModel
from src.rss.feed.domain.value_objects import SourceId
from src.shared.kernel.logger import ILogger


class RssArticleReadRepository(IRssArticleReadRepository):
    """
    Implementación de IRssArticleReadRepository (CQRS Read Side).

    CQRS ESTRICTO:
    - Devuelve DTOs (solo datos, sin comportamiento)
    - Optimizado para queries de lectura
    - NO usar para modificar artículos

    Para Write Side:
    - Usar RssArticleWriteRepository.load() que devuelve Aggregates

    Responsabilidades:
    - Operaciones de lectura sobre RssArticle
    - Conversión de modelos ORM a DTOs
    - Manejo de errores de persistencia
    """

    def __init__(self, session: AsyncSession, logger: ILogger):
        """
        Inicializa el repositorio de lectura.

        Args:
            session: Sesión de SQLAlchemy
            logger: Logger para registrar operaciones
        """
        self._session = session
        self._logger = logger
        self._read_model_mapper = RssArticleReadModelMapper()

    async def find_by_id(self, article_id: UUID) -> Optional[ArticleReadModel]:
        """
        Busca un artículo por su ID (CQRS Read Side).

        CQRS ESTRICTO: Devuelve Read Model (solo datos), NO Aggregate.
        Para modificar, usar ArticleWriteRepository.load().

        Args:
            article_id: UUID del artículo a buscar

        Returns:
            ArticleReadModel si existe, None en caso contrario
        """
        try:
            stmt = select(RssArticleModel).where(RssArticleModel.id == article_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                self._logger.debug(
                    "Artículo no encontrado",
                    article_id=str(article_id),
                )
                return None

            read_model = self._read_model_mapper.to_read_model(model)
            self._logger.debug(
                "Artículo encontrado (ReadModel)",
                article_id=str(article_id),
            )
            return read_model

        except Exception as e:
            self._logger.error(
                "Error buscando artículo por ID",
                article_id=str(article_id),
                error=str(e),
            )
            raise

    async def find_all(
        self,
        source_id: Optional[SourceId] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ArticleReadModel]:
        """
        Busca todos los artículos con filtros opcionales.

        Args:
            source_id: Filtrar por fuente específica (opcional)
            limit: Límite de resultados (opcional)
            offset: Offset para paginación (opcional)

        Returns:
            Lista de Article aggregates que cumplen los criterios
        """
        try:
            stmt = select(RssArticleModel)

            # Aplicar filtros
            if source_id is not None:
                stmt = stmt.where(RssArticleModel.source_id == str(source_id))

            # Ordenar por fecha de creación descendente
            stmt = stmt.order_by(RssArticleModel.created_at.desc())

            # Aplicar paginación
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)

            result = await self._session.execute(stmt)
            models = result.scalars().all()

            articles = [self._read_model_mapper.to_read_model(model) for model in models]

            self._logger.debug(
                "Artículos encontrados",
                count=len(articles),
                source_id=str(source_id) if source_id else None,
                limit=limit,
                offset=offset,
            )

            return articles

        except Exception as e:
            self._logger.error(
                "Error buscando artículos",
                source_id=str(source_id) if source_id else None,
                error=str(e),
            )
            raise

    async def exists(self, article_id: UUID) -> bool:
        """
        Verifica si existe un artículo con el ID dado.

        Args:
            article_id: UUID del artículo a verificar

        Returns:
            True si el artículo existe, False en caso contrario
        """
        try:
            stmt = (
                select(func.count())
                .select_from(RssArticleModel)
                .where(RssArticleModel.id == article_id)
            )
            result = await self._session.execute(stmt)
            count = result.scalar()

            exists = count > 0
            self._logger.debug(
                "Verificación de existencia de artículo",
                article_id=str(article_id),
                exists=exists,
            )
            return exists

        except Exception as e:
            self._logger.error(
                "Error verificando existencia de artículo",
                article_id=str(article_id),
                error=str(e),
            )
            raise

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
        """
        try:
            stmt = select(func.count()).select_from(RssArticleModel)

            # Aplicar filtros
            if source_id is not None:
                stmt = stmt.where(RssArticleModel.source_id == str(source_id))

            result = await self._session.execute(stmt)
            count = result.scalar()

            self._logger.debug(
                "Conteo de artículos",
                count=count,
                source_id=str(source_id) if source_id else None,
            )

            return count

        except Exception as e:
            self._logger.error(
                "Error contando artículos",
                source_id=str(source_id) if source_id else None,
                error=str(e),
            )
            raise

    async def find_by_url_and_source(
        self,
        url: str,
        source_id: str,
    ) -> Optional[ArticleReadModel]:
        """
        Busca un artículo por URL y source_id.

        Útil para verificación de duplicados durante fetch.

        Args:
            url: URL del artículo
            source_id: ID de la fuente

        Returns:
            Article aggregate si existe, None en caso contrario
        """
        try:
            stmt = select(RssArticleModel).where(
                RssArticleModel.url == url,
                RssArticleModel.source_id == source_id,
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                self._logger.debug(
                    "Artículo no encontrado por URL y source",
                    url=url,
                    source_id=source_id,
                )
                return None

            read_model = self._read_model_mapper.to_read_model(model)
            self._logger.debug(
                "Artículo encontrado por URL y source",
                article_id=str(read_model.id),
                url=url,
                source_id=source_id,
            )
            return read_model

        except Exception as e:
            self._logger.error(
                "Error buscando artículo por URL y source",
                url=url,
                source_id=source_id,
                error=str(e),
            )
            raise

    async def find_without_scraped_content(
        self,
        limit: Optional[int] = None,
    ) -> List[ArticleReadModel]:
        """
        Busca artículos sin contenido scrapeado.

        Operación básica de filtrado sin lógica de negocio.
        Útil para pipelines de procesamiento.

        Args:
            limit: Límite de resultados (opcional)

        Returns:
            Lista de Article aggregates sin contenido scrapeado
        """
        try:
            stmt = (
                select(RssArticleModel)
                .where(RssArticleModel.content_scraped.is_(None))
                .order_by(RssArticleModel.created_at.desc())
            )

            if limit is not None:
                stmt = stmt.limit(limit)

            result = await self._session.execute(stmt)
            models = result.scalars().all()

            articles = [self._read_model_mapper.to_read_model(model) for model in models]

            self._logger.debug(
                "Artículos sin contenido scrapeado encontrados",
                count=len(articles),
                limit=limit,
            )

            return articles

        except Exception as e:
            self._logger.error(
                "Error buscando artículos sin contenido scrapeado",
                error=str(e),
            )
            raise

    async def find_pending_processing(
        self,
        limit: Optional[int] = None,
    ) -> List[ArticleReadModel]:
        """
        Busca artículos que necesitan procesamiento.

        Criterios (OR - cualquiera de estos indica procesamiento incompleto):
        - Sin content_scraped (nunca se scrapeó el contenido HTML)
        - Sin plaintext_content (no se extrajo texto plano)
        - Sin markdown_content (no se convirtió a markdown)

        NOTA: NO incluye criterio de fecha para permitir recuperación de
        artículos antiguos que quedaron sin procesar por interrupciones.

        Args:
            limit: Límite de resultados (opcional, default 10)

        Returns:
            Lista de Article aggregates que necesitan procesamiento
        """
        from sqlalchemy import or_

        try:
            # Construir query con criterios (sin límite de fecha)
            stmt = (
                select(RssArticleModel)
                .where(
                    or_(
                        # Sin contenido scrapeado (CRÍTICO - primer paso del pipeline)
                        RssArticleModel.content_scraped.is_(None),
                        RssArticleModel.content_scraped == "",
                        # Sin plaintext
                        RssArticleModel.content_plaintext.is_(None),
                        RssArticleModel.content_plaintext == "",
                        # Sin markdown
                        RssArticleModel.content_markdown.is_(None),
                        RssArticleModel.content_markdown == "",
                    )
                )
                .order_by(RssArticleModel.created_at.desc())
            )

            # Aplicar límite (default 10)
            if limit is None:
                limit = 10
            stmt = stmt.limit(limit)

            result = await self._session.execute(stmt)
            models = result.scalars().all()

            # CQRS: Retornar Read Models (solo datos necesarios para comandos)
            articles = [
                self._read_model_mapper.to_read_model(model) for model in models
            ]

            self._logger.info(
                "Artículos pendientes de procesamiento encontrados",
                count=len(articles),
                limit=limit,
            )

            return articles

        except Exception as e:
            self._logger.error(
                "Error buscando artículos pendientes de procesamiento",
                error=str(e),
            )
            raise

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
        """
        try:
            stmt = select(RssArticleModel).where(RssArticleModel.rss_guid == guid)

            # Filtrar por source_id si se proporciona
            if source_id is not None:
                stmt = stmt.where(RssArticleModel.source_id == source_id)

            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                self._logger.debug(
                    "Artículo no encontrado por GUID",
                    guid=guid,
                    source_id=source_id,
                )
                return None

            read_model = self._read_model_mapper.to_read_model(model)
            self._logger.debug(
                "Artículo encontrado por GUID (ReadModel)",
                article_id=str(read_model.id),
                guid=guid,
                source_id=source_id,
            )
            return read_model

        except Exception as e:
            self._logger.error(
                "Error buscando artículo por GUID",
                guid=guid,
                source_id=source_id,
                error=str(e),
            )
            raise
