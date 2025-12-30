"""Unit tests para GetQualityMetricsHandler.

Estos tests verifican que el handler calcula correctamente las métricas
de calidad de artículos usando queries simples.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.rss.article.app.queries import (
    GetQualityMetricsHandler,
    GetQualityMetricsQuery,
    QualityMetricsDTO,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.feed.domain.value_objects import RssFeedId


class TestGetQualityMetricsHandler:
    """Tests para GetQualityMetricsHandler."""

    @pytest.fixture
    def mock_article_queries(self):
        """Crea un mock de IArticleQueries."""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_article_queries):
        """Crea un GetQualityMetricsHandler con queries mock."""
        return GetQualityMetricsHandler(mock_article_queries)

    def create_article(
        self, quality_score: float, created_at: datetime = None, source_id: str = None
    ) -> RssArticle:
        """Helper para crear artículos de prueba."""
        if created_at is None:
            created_at = datetime.now(timezone.utc)

        if source_id is None:
            source_id = str(uuid4())

        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url=f"https://example.com/article-{uuid4()}",
            source_id=RssFeedId(source_id),
        )

        # Establecer quality_score y created_at
        # Set quality using the VO
        from src.shared.domain.value_objects import Level

        if quality_score is not None:
            article._quality = article._quality.with_quality_level(
                Level.from_score(quality_score)
            )
        article._created_at = created_at

        return article

    @pytest.mark.asyncio
    async def test_with_empty_article_list(self, handler, mock_article_queries):
        """Debería retornar métricas vacías cuando no hay artículos."""
        # Arrange
        query = GetQualityMetricsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=[])

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, QualityMetricsDTO)
        assert result.average_score == 0.0
        assert result.total_articles == 0
        assert result.distribution == {
            "excellent": 0,
            "good": 0,
            "average": 0,
            "poor": 0,
        }
        assert result.source_id is None

    @pytest.mark.asyncio
    async def test_average_calculation(self, handler, mock_article_queries):
        """Debería calcular correctamente el promedio de calidad."""
        # Arrange
        # Scores are quantized:
        # 0.8 → HIGH (0.8)
        # 0.6 → HIGH (0.8)
        # 0.4 → MEDIUM (0.5)
        # 0.2 → LOW (0.2)
        articles = [
            self.create_article(quality_score=0.8),
            self.create_article(quality_score=0.6),
            self.create_article(quality_score=0.4),
            self.create_article(quality_score=0.2),
        ]
        expected_average = (0.8 + 0.8 + 0.5 + 0.2) / 4  # 0.575

        query = GetQualityMetricsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert abs(result.average_score - expected_average) < 0.001
        assert result.total_articles == 4

    @pytest.mark.asyncio
    async def test_distribution_calculation(self, handler, mock_article_queries):
        """Debería calcular correctamente la distribución por rangos."""
        # Arrange
        articles = [
            self.create_article(quality_score=0.9),  # excellent
            self.create_article(quality_score=0.85),  # excellent
            self.create_article(quality_score=0.7),  # good
            self.create_article(quality_score=0.65),  # good
            self.create_article(quality_score=0.5),  # average
            self.create_article(quality_score=0.45),  # average
            self.create_article(quality_score=0.3),  # poor
            self.create_article(quality_score=0.1),  # poor
        ]

        query = GetQualityMetricsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.distribution["excellent"] == 2
        assert result.distribution["good"] == 2
        assert result.distribution["average"] == 2
        assert result.distribution["poor"] == 2
        assert result.total_articles == 8

    @pytest.mark.asyncio
    async def test_filtering_by_hours(self, handler, mock_article_queries):
        """Debería filtrar artículos por tiempo cuando se especifica hours."""
        # Arrange
        now = datetime.now(timezone.utc)
        recent_article = self.create_article(
            quality_score=0.8, created_at=now - timedelta(hours=1)
        )
        old_article = self.create_article(
            quality_score=0.6, created_at=now - timedelta(hours=25)
        )

        query = GetQualityMetricsQuery(hours=24)
        mock_article_queries.find_all = AsyncMock(
            return_value=[recent_article, old_article]
        )

        # Act
        result = await handler.handle(query)

        # Assert
        # Solo el artículo reciente debe ser incluido
        assert result.total_articles == 1
        assert result.average_score == 0.8

    @pytest.mark.asyncio
    async def test_filtering_by_source_id(self, handler, mock_article_queries):
        """Debería filtrar por source_id cuando se especifica."""
        # Arrange
        source_id = uuid4()
        query = GetQualityMetricsQuery(source_id=source_id)

        articles = [
            self.create_article(quality_score=0.8, source_id=str(source_id)),
            self.create_article(quality_score=0.6, source_id=str(source_id)),
        ]

        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.source_id == str(source_id)
        assert result.total_articles == 2
        # Verificar que se llamó con el source_id correcto
        mock_article_queries.find_all.assert_called_once()
        call_args = mock_article_queries.find_all.call_args
        assert call_args.kwargs["source_id"] is not None

    @pytest.mark.asyncio
    async def test_ignores_articles_without_quality_score(
        self, handler, mock_article_queries
    ):
        """Debería ignorar artículos sin quality_score."""
        # Arrange
        article_with_score = self.create_article(quality_score=0.8)
        article_without_score = self.create_article(quality_score=None)  # Sin score

        query = GetQualityMetricsQuery()
        mock_article_queries.find_all = AsyncMock(
            return_value=[article_with_score, article_without_score]
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_articles == 1
        assert result.average_score == 0.8

    @pytest.mark.asyncio
    async def test_distribution_boundary_values(self, handler, mock_article_queries):
        """Debería clasificar correctamente los valores en los límites."""
        # Arrange
        articles = [
            self.create_article(quality_score=0.8),  # excellent (>= 0.8)
            self.create_article(quality_score=0.6),  # good (>= 0.6)
            self.create_article(quality_score=0.4),  # average (>= 0.4)
            self.create_article(quality_score=0.39),  # poor (< 0.4)
        ]

        query = GetQualityMetricsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.distribution["excellent"] == 1
        assert result.distribution["good"] == 1
        assert result.distribution["average"] == 1
        assert result.distribution["poor"] == 1

    @pytest.mark.asyncio
    async def test_combined_filters(self, handler, mock_article_queries):
        """Debería aplicar correctamente múltiples filtros."""
        # Arrange
        source_id = uuid4()
        now = datetime.now(timezone.utc)

        # Artículo que cumple ambos filtros
        matching_article = self.create_article(
            quality_score=0.8,
            source_id=str(source_id),
            created_at=now - timedelta(hours=1),
        )

        # Artículo que no cumple el filtro de tiempo
        old_article = self.create_article(
            quality_score=0.6,
            source_id=str(source_id),
            created_at=now - timedelta(hours=25),
        )

        query = GetQualityMetricsQuery(source_id=source_id, hours=24)
        mock_article_queries.find_all = AsyncMock(
            return_value=[matching_article, old_article]
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_articles == 1
        assert result.average_score == 0.8
        assert result.source_id == str(source_id)

    @pytest.mark.asyncio
    async def test_returns_correct_dto_structure(self, handler, mock_article_queries):
        """Debería retornar un DTO con la estructura correcta."""
        # Arrange
        articles = [self.create_article(quality_score=0.7)]
        query = GetQualityMetricsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, QualityMetricsDTO)
        assert isinstance(result.average_score, float)
        assert isinstance(result.distribution, dict)
        assert isinstance(result.total_articles, int)
        assert "excellent" in result.distribution
        assert "good" in result.distribution
        assert "average" in result.distribution
        assert "poor" in result.distribution
