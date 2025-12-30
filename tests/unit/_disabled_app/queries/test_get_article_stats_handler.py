"""Unit tests para GetArticleStatsHandler.

Estos tests verifican que el handler calcula correctamente las estadísticas
completas de artículos usando queries simples.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.rss.article.app.queries import (
    ArticleStatsDTO,
    GetArticleStatsHandler,
    GetArticleStatsQuery,
    TimelineDataPoint,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId


class TestGetArticleStatsHandler:
    """Tests para GetArticleStatsHandler."""

    @pytest.fixture
    def mock_article_queries(self):
        """Crea un mock de IArticleQueries."""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_article_queries):
        """Crea un GetArticleStatsHandler con queries mock."""
        return GetArticleStatsHandler(mock_article_queries)

    def create_article(
        self,
        quality_score: float = None,
        created_at: datetime = None,
        source_id: str = None,
        status: str = "draft",
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

        # Establecer atributos
        # Set quality using the VO
        from src.shared.domain.value_objects import Level

        if quality_score is not None:
            article._quality = article._quality.with_quality_level(
                Level.from_score(quality_score)
            )
        article._created_at = created_at

        # Establecer estado basándose en timestamps
        if status == "archived":
            article._archived_at = datetime.now(timezone.utc)
            article._published_at = datetime.now(timezone.utc) - timedelta(days=1)
        elif status == "published":
            article._published_at = datetime.now(timezone.utc)
            article._archived_at = None
        else:  # draft
            article._published_at = None
            article._archived_at = None

        return article

    @pytest.mark.asyncio
    async def test_with_empty_article_list(self, handler, mock_article_queries):
        """Debería retornar estadísticas vacías cuando no hay artículos."""
        # Arrange
        query = GetArticleStatsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=[])

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, ArticleStatsDTO)
        assert result.total_articles == 0
        assert result.by_source == {}
        assert result.by_status == {}
        assert result.average_quality == 0.0
        assert result.recent_count == 0
        assert result.quality_distribution == {
            "high": 0,
            "medium": 0,
            "low": 0,
            "unscored": 0,
        }
        assert result.publication_timeline == []
        assert result.source_id is None

    @pytest.mark.asyncio
    async def test_overall_stats_calculation(self, handler, mock_article_queries):
        """Debería calcular correctamente las estadísticas generales."""
        # Arrange
        source1 = str(uuid4())
        source2 = str(uuid4())

        articles = [
            self.create_article(
                quality_score=0.8, source_id=source1, status="published"
            ),
            self.create_article(quality_score=0.6, source_id=source1, status="draft"),
            self.create_article(
                quality_score=0.4, source_id=source2, status="published"
            ),
        ]

        query = GetArticleStatsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_articles == 3
        # Scores are now quantized to quality levels:
        # 0.4 → MEDIUM (0.5), 0.6 → HIGH (0.8), 0.8 → HIGH (0.8)
        # Average: (0.5 + 0.8 + 0.8) / 3 = 0.7
        assert abs(result.average_quality - 0.7) < 0.001

    @pytest.mark.asyncio
    async def test_stats_by_source(self, handler, mock_article_queries):
        """Debería calcular correctamente las estadísticas por fuente."""
        # Arrange
        source1 = str(uuid4())
        source2 = str(uuid4())

        articles = [
            self.create_article(source_id=source1),
            self.create_article(source_id=source1),
            self.create_article(source_id=source1),
            self.create_article(source_id=source2),
            self.create_article(source_id=source2),
        ]

        query = GetArticleStatsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.by_source[source1] == 3
        assert result.by_source[source2] == 2
        assert len(result.by_source) == 2

    @pytest.mark.asyncio
    async def test_quality_distribution(self, handler, mock_article_queries):
        """Debería calcular correctamente la distribución de calidad."""
        # Arrange
        # Scores are quantized by Level:
        # 0.9 → PREMIUM (0.95) → high (>= 0.7)
        # 0.75 → HIGH (0.8) → high (>= 0.7)
        # 0.6 → HIGH (0.8) → high (>= 0.7)
        # 0.5 → MEDIUM (0.5) → medium (>= 0.4)
        # 0.3 → MEDIUM (0.5) → medium (>= 0.4)
        # 0.1 → LOW (0.2) → low (< 0.4)
        articles = [
            self.create_article(quality_score=0.9),  # high
            self.create_article(quality_score=0.75),  # high
            self.create_article(quality_score=0.6),  # high (quantized to 0.8)
            self.create_article(quality_score=0.5),  # medium
            self.create_article(quality_score=0.3),  # medium (quantized to 0.5)
            self.create_article(quality_score=0.1),  # low
            self.create_article(quality_score=None),  # unscored
            self.create_article(quality_score=None),  # unscored
        ]

        query = GetArticleStatsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert (
            result.quality_distribution["high"] == 3
        )  # 0.9, 0.75, 0.6 all quantize to >= 0.7
        assert result.quality_distribution["medium"] == 2  # 0.5, 0.3 quantize to 0.5
        assert result.quality_distribution["low"] == 1  # 0.1 quantizes to 0.2
        assert result.quality_distribution["unscored"] == 2

    @pytest.mark.asyncio
    async def test_publication_timeline(self, handler, mock_article_queries):
        """Debería calcular correctamente el timeline de publicaciones."""
        # Arrange
        now = datetime.now(timezone.utc)
        today = now.date()
        yesterday = (now - timedelta(days=1)).date()
        two_days_ago = (now - timedelta(days=2)).date()

        articles = [
            self.create_article(created_at=now),
            self.create_article(created_at=now - timedelta(hours=2)),
            self.create_article(created_at=now - timedelta(days=1)),
            self.create_article(created_at=now - timedelta(days=2)),
            self.create_article(created_at=now - timedelta(days=2, hours=3)),
        ]

        query = GetArticleStatsQuery(timeline_days=30)
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.publication_timeline) == 3

        # Verificar que está ordenado por fecha
        dates = [point.date for point in result.publication_timeline]
        assert dates == sorted(dates)

        # Verificar conteos
        timeline_dict = {
            point.date: point.count for point in result.publication_timeline
        }
        assert timeline_dict[today.isoformat()] == 2
        assert timeline_dict[yesterday.isoformat()] == 1
        assert timeline_dict[two_days_ago.isoformat()] == 2

    @pytest.mark.asyncio
    async def test_recent_count_calculation(self, handler, mock_article_queries):
        """Debería calcular correctamente el conteo de artículos recientes."""
        # Arrange
        now = datetime.now(timezone.utc)

        articles = [
            self.create_article(created_at=now - timedelta(hours=1)),
            self.create_article(created_at=now - timedelta(hours=12)),
            self.create_article(created_at=now - timedelta(hours=23)),
            self.create_article(created_at=now - timedelta(hours=25)),  # Fuera de 24h
            self.create_article(created_at=now - timedelta(days=2)),  # Fuera de 24h
        ]

        query = GetArticleStatsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.recent_count == 3

    @pytest.mark.asyncio
    async def test_stats_by_status(self, handler, mock_article_queries):
        """Debería calcular correctamente las estadísticas por estado."""
        # Arrange
        articles = [
            self.create_article(status="published"),
            self.create_article(status="published"),
            self.create_article(status="published"),
            self.create_article(status="draft"),
            self.create_article(status="draft"),
            self.create_article(status="archived"),
        ]

        query = GetArticleStatsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.by_status["published"] == 3
        assert result.by_status["draft"] == 2
        assert result.by_status["archived"] == 1

    @pytest.mark.asyncio
    async def test_filtering_by_source_id(self, handler, mock_article_queries):
        """Debería filtrar por source_id cuando se especifica."""
        # Arrange
        source_id = uuid4()
        query = GetArticleStatsQuery(source_id=source_id)

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
    async def test_timeline_respects_days_parameter(
        self, handler, mock_article_queries
    ):
        """Debería respetar el parámetro timeline_days."""
        # Arrange
        now = datetime.now(timezone.utc)

        articles = [
            self.create_article(created_at=now - timedelta(days=1)),
            self.create_article(created_at=now - timedelta(days=5)),
            self.create_article(created_at=now - timedelta(days=6)),
            self.create_article(created_at=now - timedelta(days=15)),  # Fuera de 7 días
        ]

        query = GetArticleStatsQuery(timeline_days=7)
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        # Solo los primeros 3 artículos deben estar en el timeline (dentro de 7 días)
        total_in_timeline = sum(point.count for point in result.publication_timeline)
        assert total_in_timeline == 3

    @pytest.mark.asyncio
    async def test_average_quality_ignores_none_values(
        self, handler, mock_article_queries
    ):
        """Debería ignorar valores None al calcular el promedio de calidad."""
        # Arrange
        # Scores are quantized:
        # 0.8 → HIGH (0.8)
        # 0.6 → HIGH (0.8)
        articles = [
            self.create_article(quality_score=0.8),
            self.create_article(quality_score=0.6),
            self.create_article(quality_score=None),
            self.create_article(quality_score=None),
        ]

        query = GetArticleStatsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        # Promedio de 0.8 y 0.8 (ambos quantizados a HIGH)
        assert abs(result.average_quality - 0.8) < 0.001

    @pytest.mark.asyncio
    async def test_quality_distribution_boundary_values(
        self, handler, mock_article_queries
    ):
        """Debería clasificar correctamente los valores en los límites."""
        # Arrange
        # Scores are quantized:
        # 0.7 → HIGH (0.8) → high (>= 0.7)
        # 0.69 → HIGH (0.8) → high (>= 0.7)
        # 0.4 → MEDIUM (0.5) → medium (>= 0.4)
        # 0.39 → MEDIUM (0.5) → medium (>= 0.4)
        articles = [
            self.create_article(quality_score=0.7),  # high
            self.create_article(quality_score=0.69),  # high (quantized to 0.8)
            self.create_article(quality_score=0.4),  # medium
            self.create_article(quality_score=0.39),  # medium (quantized to 0.5)
        ]

        query = GetArticleStatsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert (
            result.quality_distribution["high"] == 2
        )  # 0.7 and 0.69 both quantize to HIGH
        assert (
            result.quality_distribution["medium"] == 2
        )  # 0.4 and 0.39 both quantize to MEDIUM
        assert result.quality_distribution["low"] == 0

    @pytest.mark.asyncio
    async def test_returns_correct_dto_structure(self, handler, mock_article_queries):
        """Debería retornar un DTO con la estructura correcta."""
        # Arrange
        articles = [self.create_article(quality_score=0.7)]
        query = GetArticleStatsQuery()
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, ArticleStatsDTO)
        assert isinstance(result.total_articles, int)
        assert isinstance(result.by_source, dict)
        assert isinstance(result.by_status, dict)
        assert isinstance(result.average_quality, float)
        assert isinstance(result.recent_count, int)
        assert isinstance(result.quality_distribution, dict)
        assert isinstance(result.publication_timeline, list)

        # Verificar estructura de quality_distribution
        assert "high" in result.quality_distribution
        assert "medium" in result.quality_distribution
        assert "low" in result.quality_distribution
        assert "unscored" in result.quality_distribution

        # Verificar estructura de timeline
        if result.publication_timeline:
            assert isinstance(result.publication_timeline[0], TimelineDataPoint)

    @pytest.mark.asyncio
    async def test_comprehensive_stats_integration(self, handler, mock_article_queries):
        """Debería calcular todas las estadísticas correctamente en conjunto."""
        # Arrange
        source1 = str(uuid4())
        source2 = str(uuid4())
        now = datetime.now(timezone.utc)

        articles = [
            # Source 1, published, high quality, recent
            self.create_article(
                quality_score=0.9,
                source_id=source1,
                status="published",
                created_at=now - timedelta(hours=2),
            ),
            # Source 1, draft, medium quality, recent
            self.create_article(
                quality_score=0.5,
                source_id=source1,
                status="draft",
                created_at=now - timedelta(hours=12),
            ),
            # Source 2, published, low quality, not recent
            self.create_article(
                quality_score=0.2,
                source_id=source2,
                status="published",
                created_at=now - timedelta(days=2),
            ),
            # Source 2, archived, no quality, not recent
            self.create_article(
                quality_score=None,
                source_id=source2,
                status="archived",
                created_at=now - timedelta(days=3),
            ),
        ]

        query = GetArticleStatsQuery(timeline_days=7)
        mock_article_queries.find_all = AsyncMock(return_value=articles)

        # Act
        result = await handler.handle(query)

        # Assert
        # Totales
        assert result.total_articles == 4

        # Por fuente
        assert result.by_source[source1] == 2
        assert result.by_source[source2] == 2

        # Por estado
        assert result.by_status["published"] == 2
        assert result.by_status["draft"] == 1
        assert result.by_status["archived"] == 1

        # Calidad promedio (solo 3 con score)
        expected_avg = (0.9 + 0.5 + 0.2) / 3
        assert abs(result.average_quality - expected_avg) < 0.001

        # Recientes (últimas 24h)
        assert result.recent_count == 2

        # Distribución de calidad
        assert result.quality_distribution["high"] == 1
        assert result.quality_distribution["medium"] == 1
        assert result.quality_distribution["low"] == 1
        assert result.quality_distribution["unscored"] == 1

        # Timeline
        assert len(result.publication_timeline) > 0
