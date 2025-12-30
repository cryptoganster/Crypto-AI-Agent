"""Handler para queries de preparación de publicación de artículos."""

from typing import List, Optional, Union
from uuid import UUID

from src.rss.article.app.queries.get_publishing_readiness.dto import (
    ArticleReadinessDTO,
    PublishingReadinessDTO,
    ReadinessSummaryDTO,
)
from src.rss.article.app.queries.get_publishing_readiness.query import (
    GetPublishingReadinessQuery,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.interfaces.repositories import IArticleReadRepository


class GetPublishingReadinessHandler:
    """Handler para queries de preparación de publicación.

    Este handler implementa la lógica de negocio para determinar
    si un artículo está listo para publicación basándose en:
    - Contenido markdown presente
    - Quality score suficiente (>= 0.5)
    - Summary generado
    - Keywords extraídas
    - Word count calculado
    """

    def __init__(self, article_queries: IArticleReadRepository):
        """Inicializa el handler con dependencias.

        Args:
            article_queries: Interface para queries simples de artículos
        """
        self._article_queries = article_queries

    async def handle(
        self, query: GetPublishingReadinessQuery
    ) -> Union[PublishingReadinessDTO, List[ArticleReadinessDTO], ReadinessSummaryDTO]:
        """Ejecuta el query de preparación de publicación.

        Args:
            query: Query con parámetros de búsqueda

        Returns:
            DTO apropiado según el tipo de query:
            - PublishingReadinessDTO si se especifica article_id
            - List[ArticleReadinessDTO] si operation es 'ready', 'pending' o 'needs_work'
            - ReadinessSummaryDTO si operation es 'summary'

        Raises:
            ValueError: Si article_id no existe o parámetros inválidos
        """
        # Caso 1: Verificar preparación de artículo específico
        if query.article_id:
            return await self._check_article_readiness(query.article_id)

        # Caso 2: Obtener artículos listos
        if query.operation == "ready":
            return await self._get_ready_articles(query.limit)

        # Caso 3: Obtener resumen
        if query.operation == "summary":
            return await self._get_summary()

        # Caso 4: Obtener artículos pendientes
        if query.operation == "pending":
            return await self._get_pending_articles(query.limit)

        # Caso 5: Obtener artículos que necesitan trabajo
        if query.operation == "needs_work":
            return await self._get_needs_work_articles(query.limit)

        raise ValueError(
            "Query debe especificar article_id o operation "
            "('ready', 'summary', 'pending', 'needs_work')"
        )

    async def _check_article_readiness(
        self, article_id: UUID
    ) -> PublishingReadinessDTO:
        """Verifica la preparación de un artículo específico.

        Args:
            article_id: ID del artículo a verificar

        Returns:
            DTO con estado de preparación y validaciones pendientes

        Raises:
            ValueError: Si el artículo no existe
        """
        article = await self._article_queries.find_by_id(article_id)

        if article is None:
            raise ValueError(f"Article {article_id} not found")

        pending_validations = self._get_pending_validations(article)
        is_ready = len(pending_validations) == 0

        return PublishingReadinessDTO(
            article_id=str(article.id),
            is_ready=is_ready,
            pending_validations=pending_validations,
            quality_score=article.quality.quality_score,
            has_content=article.content.has_markdown,
            has_summary=article.metadata.summary is not None,
            has_keywords=len(article.metadata.keywords.keywords) > 0,
            word_count=article.metrics.word_count.value,
            readability_score=(
                article.quality.readability_score.value
                if article.quality.readability_score
                else None
            ),
        )

    async def _get_ready_articles(self, limit: int) -> List[ArticleReadinessDTO]:
        """Obtiene artículos listos para publicar.

        Args:
            limit: Número máximo de artículos a retornar

        Returns:
            Lista de artículos que cumplen todos los criterios
        """
        # Obtener todos los artículos (en producción, esto debería ser paginado)
        articles = await self._article_queries.find_all(limit=limit * 3)

        ready_articles = []
        for article in articles:
            pending = self._get_pending_validations(article)
            if len(pending) == 0:
                ready_articles.append(
                    ArticleReadinessDTO(
                        article_id=str(article.id),
                        title=article.metadata.title,
                        is_ready=True,
                        pending_validations=[],
                        quality_score=article.quality.quality_score,
                        has_content=article.content.has_markdown,
                        has_summary=article.metadata.summary is not None,
                        has_keywords=len(article.metadata.keywords.keywords) > 0,
                        word_count=article.metrics.word_count.value,
                        created_at=article.created_at,
                    )
                )

                if len(ready_articles) >= limit:
                    break

        return ready_articles

    async def _get_pending_articles(self, limit: int) -> List[ArticleReadinessDTO]:
        """Obtiene artículos pendientes de validación.

        Args:
            limit: Número máximo de artículos a retornar

        Returns:
            Lista de artículos con 1-2 validaciones pendientes
        """
        articles = await self._article_queries.find_all(limit=limit * 3)

        pending_articles = []
        for article in articles:
            pending = self._get_pending_validations(article)
            # Pendientes: tienen algunas validaciones pero no muchas
            if 1 <= len(pending) <= 2:
                pending_articles.append(
                    ArticleReadinessDTO(
                        article_id=str(article.id),
                        title=article.metadata.title,
                        is_ready=False,
                        pending_validations=pending,
                        quality_score=article.quality.quality_score,
                        has_content=article.content.has_markdown,
                        has_summary=article.metadata.summary is not None,
                        has_keywords=len(article.metadata.keywords.keywords) > 0,
                        word_count=article.metrics.word_count.value,
                        created_at=article.created_at,
                    )
                )

                if len(pending_articles) >= limit:
                    break

        return pending_articles

    async def _get_needs_work_articles(self, limit: int) -> List[ArticleReadinessDTO]:
        """Obtiene artículos que necesitan trabajo significativo.

        Args:
            limit: Número máximo de artículos a retornar

        Returns:
            Lista de artículos con 3+ validaciones pendientes
        """
        articles = await self._article_queries.find_all(limit=limit * 3)

        needs_work_articles = []
        for article in articles:
            pending = self._get_pending_validations(article)
            # Necesitan trabajo: tienen muchas validaciones pendientes
            if len(pending) >= 3:
                needs_work_articles.append(
                    ArticleReadinessDTO(
                        article_id=str(article.id),
                        title=article.metadata.title,
                        is_ready=False,
                        pending_validations=pending,
                        quality_score=article.quality.quality_score,
                        has_content=article.content.has_markdown,
                        has_summary=article.metadata.summary is not None,
                        has_keywords=len(article.metadata.keywords.keywords) > 0,
                        word_count=article.metrics.word_count.value,
                        created_at=article.created_at,
                    )
                )

                if len(needs_work_articles) >= limit:
                    break

        return needs_work_articles

    async def _get_summary(self) -> ReadinessSummaryDTO:
        """Obtiene resumen de preparación de artículos.

        Returns:
            DTO con contadores por estado
        """
        # Obtener todos los artículos
        articles = await self._article_queries.find_all()

        ready = 0
        pending = 0
        needs_work = 0
        blocked = 0

        for article in articles:
            pending_validations = self._get_pending_validations(article)
            validation_count = len(pending_validations)

            if validation_count == 0:
                ready += 1
            elif 1 <= validation_count <= 2:
                pending += 1
            elif validation_count >= 3:
                # Artículos con errores o sin contenido básico son "blocked"
                if article.error.has_error or not article.content.has_markdown:
                    blocked += 1
                else:
                    needs_work += 1

        return ReadinessSummaryDTO(
            ready=ready,
            pending=pending,
            needs_work=needs_work,
            blocked=blocked,
            total=len(articles),
        )

    def _get_pending_validations(self, article: RssArticle) -> List[str]:
        """Determina qué validaciones están pendientes para un artículo.

        Criterios de preparación:
        1. Debe tener contenido markdown
        2. Debe tener quality score >= 0.5
        3. Debe tener summary
        4. Debe tener keywords
        5. Debe tener word count

        Args:
            article: Artículo a evaluar

        Returns:
            Lista de validaciones pendientes
        """
        pending = []

        # Validación 1: Contenido
        if not article.content.has_markdown:
            pending.append("missing_content")

        # Validación 2: Quality score
        if article.quality.quality_score is None:
            pending.append("missing_quality_score")
        elif article.quality.quality_score < 0.5:
            pending.append("low_quality_score")

        # Validación 3: Summary
        if article.metadata.summary is None:
            pending.append("missing_summary")

        # Validación 4: Keywords
        if len(article.metadata.keywords.keywords) == 0:
            pending.append("missing_keywords")

        # Validación 5: Word count
        if (
            article.metrics.word_count is None
            or article.metrics.word_count.value is None
            or article.metrics.word_count.value == 0
        ):
            pending.append("missing_word_count")

        return pending
