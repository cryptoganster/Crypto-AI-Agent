"""Unit tests para GetPublishingReadinessHandler.

Estos tests verifican que el handler determina correctamente la preparación
de publicación de artículos basándose en criterios de negocio.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.rss.article.app.queries import (
    ArticleReadinessDTO,
    GetPublishingReadinessHandler,
    GetPublishingReadinessQuery,
    PublishingReadinessDTO,
    ReadinessSummaryDTO,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId


class TestGetPublishingReadinessHandler:
    """Tests para GetPublishingReadinessHandler."""

    @pytest.fixture
    def mock_article_queries(self):
        """Crea un mock de IArticleQueries."""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_article_queries):
        """Crea un GetPublishingReadinessHandler con queries mock."""
        return GetPublishingReadinessHandler(mock_article_queries)

    def create_article(
        self,
        has_content: bool = True,
        quality_score: float = 0.7,
        has_summary: bool = True,
        has_keywords: bool = True,
        word_count: int = 500,
        has_error: bool = False,
    ) -> RssArticle:
        """Helper para crear artículos de prueba con diferentes estados."""
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url=f"https://example.com/article-{uuid4()}",
            source_id=RssFeedId(str(uuid4())),
        )

        # Configurar estado del artículo
        if has_content:
            article.update_content_fields(
                markdown="# Test Content\n\nThis is test content."
            )
            article.mark_events_as_committed()  # Limpiar eventos de test
        # Si no has_content, el artículo queda sin contenido (estado inicial)

        # Set quality using the VO
        from src.shared.domain.value_objects import Level

        if quality_score is not None:
            article._quality = article._quality.with_quality_level(
                Level.from_score(quality_score)
            )

        if has_summary:
            from src.rss.article.domain.value_objects.metadata import RssArticleSummary

            article._metadata = article._metadata.with_summary(
                RssArticleSummary("Test summary")
            )
        else:
            article._metadata = article._metadata.with_summary(None)

        if has_keywords:
            article.set_keywords(["test", "article", "content"])
        else:
            article.set_keywords([])

        # Set word count using the VO
        if word_count:
            from src.rss.article.domain.value_objects.analysis import WordCount

            article._metrics = article._metrics.__class__(
                word_count=WordCount(value=word_count),
                reading_time=article._metrics.reading_time,
            )

        article._has_error = has_error

        return article

    @pytest.mark.asyncio
    async def test_check_readiness_for_ready_article(
        self, handler, mock_article_queries
    ):
        """Debería retornar is_ready=True para artículo que cumple todos los criterios."""
        # Arrange
        article_id = uuid4()
        ready_article = self.create_article(
            has_content=True,
            quality_score=0.7,
            has_summary=True,
            has_keywords=True,
            word_count=500,
        )

        query = GetPublishingReadinessQuery(article_id=article_id)
        mock_article_queries.find_by_id = AsyncMock(return_value=ready_article)

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, PublishingReadinessDTO)
        assert result.is_ready is True
        assert len(result.pending_validations) == 0
        assert result.has_content is True
        assert result.has_summary is True
        assert result.has_keywords is True
        assert result.quality_score == 0.8  # Quantized from 0.7 to HIGH (0.8)
        assert result.word_count == 500

    @pytest.mark.asyncio
    async def test_check_readiness_for_article_without_content(
        self, handler, mock_article_queries
    ):
        """Debería identificar artículo sin contenido como no listo."""
        # Arrange
        article_id = uuid4()
        article = self.create_article(has_content=False)

        query = GetPublishingReadinessQuery(article_id=article_id)
        mock_article_queries.find_by_id = AsyncMock(return_value=article)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.is_ready is False
        assert "missing_content" in result.pending_validations
        assert result.has_content is False

    @pytest.mark.asyncio
    async def test_check_readiness_for_article_with_low_quality(
        self, handler, mock_article_queries
    ):
        """Debería identificar artículo con baja calidad como no listo."""
        # Arrange
        article_id = uuid4()
        article = self.create_article(quality_score=0.3)

        query = GetPublishingReadinessQuery(article_id=article_id)
        mock_article_queries.find_by_id = AsyncMock(return_value=article)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.is_ready is False
        assert "low_quality_score" in result.pending_validations
        assert result.quality_score == 0.3

    @pytest.mark.asyncio
    async def test_check_readiness_for_article_without_quality_score(
        self, handler, mock_article_queries
    ):
        """Debería identificar artículo sin quality score como no listo."""
        # Arrange
        article_id = uuid4()
        article = self.create_article(quality_score=None)

        query = GetPublishingReadinessQuery(article_id=article_id)
        mock_article_queries.find_by_id = AsyncMock(return_value=article)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.is_ready is False
        assert "missing_quality_score" in result.pending_validations
        assert result.quality_score is None

    @pytest.mark.asyncio
    async def test_check_readiness_for_article_without_summary(
        self, handler, mock_article_queries
    ):
        """Debería identificar artículo sin summary como no listo."""
        # Arrange
        article_id = uuid4()
        article = self.create_article(has_summary=False)

        query = GetPublishingReadinessQuery(article_id=article_id)
        mock_article_queries.find_by_id = AsyncMock(return_value=article)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.is_ready is False
        assert "missing_summary" in result.pending_validations
        assert result.has_summary is False

    @pytest.mark.asyncio
    async def test_check_readiness_for_article_without_keywords(
        self, handler, mock_article_queries
    ):
        """Debería identificar artículo sin keywords como no listo."""
        # Arrange
        article_id = uuid4()
        article = self.create_article(has_keywords=False)

        query = GetPublishingReadinessQuery(article_id=article_id)
        mock_article_queries.find_by_id = AsyncMock(return_value=article)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.is_ready is False
        assert "missing_keywords" in result.pending_validations
        assert result.has_keywords is False

    @pytest.mark.asyncio
    async def test_check_readiness_for_article_without_word_count(
        self, handler, mock_article_queries
    ):
        """Debería identificar artículo sin word count como no listo."""
        # Arrange
        article_id = uuid4()
        article = self.create_article(word_count=0)

        query = GetPublishingReadinessQuery(article_id=article_id)
        mock_article_queries.find_by_id = AsyncMock(return_value=article)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.is_ready is False
        assert "missing_word_count" in result.pending_validations

    @pytest.mark.asyncio
    async def test_check_readiness_for_nonexistent_article(
        self, handler, mock_article_queries
    ):
        """Debería lanzar ValueError cuando el artículo no existe."""
        # Arrange
        article_id = uuid4()
        query = GetPublishingReadinessQuery(article_id=article_id)
        mock_article_queries.find_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            await handler.handle(query)

    @pytest.mark.asyncio
    async def test_get_ready_articles(self, handler, mock_article_queries):
        """Debería retornar solo artículos listos para publicar."""
        # Arrange
        ready_article = self.create_article()
        not_ready_article = self.create_article(has_content=False)

        query = GetPublishingReadinessQuery(operation="ready", limit=10)
        mock_article_queries.find_all = AsyncMock(
            return_value=[ready_article, not_ready_article]
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ArticleReadinessDTO)
        assert result[0].is_ready is True
        assert len(result[0].pending_validations) == 0

    @pytest.mark.asyncio
    async def test_get_pending_articles(self, handler, mock_article_queries):
        """Debería retornar artículos con 1-2 validaciones pendientes."""
        # Arrange
        # Artículo con 1 validación pendiente
        pending_article = self.create_article(has_summary=False)

        # Artículo listo (0 validaciones)
        ready_article = self.create_article()

        # Artículo con muchas validaciones (3+)
        needs_work_article = self.create_article(
            has_content=False,
            has_summary=False,
            has_keywords=False,
        )

        query = GetPublishingReadinessQuery(operation="pending", limit=10)
        mock_article_queries.find_all = AsyncMock(
            return_value=[pending_article, ready_article, needs_work_article]
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].is_ready is False
        assert 1 <= len(result[0].pending_validations) <= 2

    @pytest.mark.asyncio
    async def test_get_needs_work_articles(self, handler, mock_article_queries):
        """Debería retornar artículos con 3+ validaciones pendientes."""
        # Arrange
        needs_work_article = self.create_article(
            has_content=False,
            has_summary=False,
            has_keywords=False,
        )

        ready_article = self.create_article()

        query = GetPublishingReadinessQuery(operation="needs_work", limit=10)
        mock_article_queries.find_all = AsyncMock(
            return_value=[needs_work_article, ready_article]
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].is_ready is False
        assert len(result[0].pending_validations) >= 3

    @pytest.mark.asyncio
    async def test_get_summary(self, handler, mock_article_queries):
        """Debería retornar resumen con contadores por estado."""
        # Arrange
        ready_article = self.create_article()
        pending_article = self.create_article(has_summary=False)

        # Artículo con 3+ validaciones pero con contenido (needs_work)
        needs_work_article = self.create_article(
            has_content=True,
            has_summary=False,
            has_keywords=False,
            word_count=0,
        )

        # Artículo sin contenido (blocked)
        blocked_article = self.create_article(
            has_content=False,
            has_summary=False,
            has_keywords=False,
        )

        query = GetPublishingReadinessQuery(operation="summary")
        mock_article_queries.find_all = AsyncMock(
            return_value=[
                ready_article,
                pending_article,
                needs_work_article,
                blocked_article,
            ]
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, ReadinessSummaryDTO)
        assert result.ready == 1
        assert result.pending == 1
        assert result.needs_work == 1
        assert result.blocked == 1
        assert result.total == 4

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(self, handler, mock_article_queries):
        """Debería respetar el parámetro limit."""
        # Arrange
        articles = [self.create_article() for _ in range(20)]

        query = GetPublishingReadinessQuery(operation="ready", limit=5)
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result) <= 5

    @pytest.mark.asyncio
    async def test_invalid_query_raises_error(self, handler, mock_article_queries):
        """Debería lanzar ValueError para query inválido."""
        # Arrange
        query = GetPublishingReadinessQuery()  # Sin article_id ni operation

        # Act & Assert
        with pytest.raises(ValueError, match="Query debe especificar"):
            await handler.handle(query)

    @pytest.mark.asyncio
    async def test_multiple_pending_validations(self, handler, mock_article_queries):
        """Debería identificar múltiples validaciones pendientes correctamente."""
        # Arrange
        article_id = uuid4()
        article = self.create_article(
            has_content=False,
            quality_score=0.3,
            has_summary=False,
        )

        query = GetPublishingReadinessQuery(article_id=article_id)
        mock_article_queries.find_by_id = AsyncMock(return_value=article)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.is_ready is False
        assert "missing_content" in result.pending_validations
        assert "low_quality_score" in result.pending_validations
        assert "missing_summary" in result.pending_validations
        assert len(result.pending_validations) == 3

    @pytest.mark.asyncio
    async def test_dto_composition(self, handler, mock_article_queries):
        """Debería componer correctamente el DTO con todos los campos."""
        # Arrange
        article_id = uuid4()
        article = self.create_article()
        article._readability_score = 0.75

        query = GetPublishingReadinessQuery(article_id=article_id)
        mock_article_queries.find_by_id = AsyncMock(return_value=article)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.article_id == str(article.identity_vo.article_id)
        assert result.quality_score == 0.7
        assert result.readability_score == 0.75
        assert result.word_count == 500
        assert result.has_content is True
        assert result.has_summary is True
        assert result.has_keywords is True

    @pytest.mark.asyncio
    async def test_empty_result_for_ready_articles_when_none_ready(
        self, handler, mock_article_queries
    ):
        """Debería retornar lista vacía cuando no hay artículos listos."""
        # Arrange
        not_ready_article = self.create_article(has_content=False)

        query = GetPublishingReadinessQuery(operation="ready", limit=10)
        mock_article_queries.find_all = AsyncMock(return_value=[not_ready_article])

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0
