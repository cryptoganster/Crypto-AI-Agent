"""Unit tests para ArticleQueryAdapter.

Estos tests verifican que el query adapter implementa correctamente
las operaciones básicas de lectura sobre RssArticle aggregate.
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.persistence.query_adapters.article_query_adapter import (
    ArticleQueryAdapter,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.article.infra.persistence.models import ArticleModel
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleQueryAdapter:
    """Tests para ArticleQueryAdapter."""

    @pytest.fixture
    def mock_session(self):
        """Crea una sesión mock para testing."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        """Crea un session factory mock que retorna la sesión mock."""
        factory = Mock()
        factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        factory.return_value.__aexit__ = AsyncMock(return_value=None)
        return factory

    @pytest.fixture
    def query_adapter(self, mock_session_factory):
        """Crea un ArticleQueryAdapter con session factory mock."""
        return ArticleQueryAdapter(mock_session_factory)

    @pytest.fixture
    def sample_article_model(self):
        """Crea un ArticleModel de ejemplo para testing."""
        article_id = uuid4()
        source_id = uuid4()

        model = RssArticleModel(
            article_id=article_id,
            source_id=source_id,
            title="Test RssArticle",
            url="https://example.com/test",
            content_markdown="Test content",
            summary="Test summary",
            content_hash="test_hash",
            quality_level="high",
            quality_score=85,
            is_duplicate=False,
            has_error=False,
            is_coin_checked=False,
        )
        return model

    @pytest.mark.asyncio
    async def test_find_by_id_returns_correct_aggregate(
        self, query_adapter, mock_session, sample_article_model
    ):
        """Debería retornar el agregado correcto cuando el artículo existe."""
        # Arrange
        article_id = sample_article_model.article_id

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_article_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        article = await query_adapter.find_by_id(article_id)

        # Assert
        assert article is not None, "Debe retornar un artículo"
        assert isinstance(article, RssArticle), "Debe retornar un RssArticle aggregate"
        assert str(article.id) == str(article_id), "El ID debe coincidir"
        assert article.title == "Test RssArticle", "El título debe coincidir"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_when_not_found(
        self, query_adapter, mock_session
    ):
        """Debería retornar None cuando el artículo no existe."""
        # Arrange
        article_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        article = await query_adapter.find_by_id(article_id)

        # Assert
        assert article is None, "Debe retornar None cuando no existe"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_all_with_no_filters(
        self, query_adapter, mock_session, sample_article_model
    ):
        """Debería retornar todos los artículos sin filtros."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalars = Mock(
            return_value=Mock(all=Mock(return_value=[sample_article_model]))
        )
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        articles = await query_adapter.find_all()

        # Assert
        assert len(articles) == 1, "Debe retornar un artículo"
        assert isinstance(
            articles[0], RssArticle
        ), "Debe retornar RssArticle aggregates"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_all_with_source_id_filter(
        self, query_adapter, mock_session, sample_article_model
    ):
        """Debería filtrar por source_id cuando se proporciona."""
        # Arrange
        source_id = RssFeedId(str(sample_article_model.source_id))

        mock_result = AsyncMock()
        mock_result.scalars = Mock(
            return_value=Mock(all=Mock(return_value=[sample_article_model]))
        )
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        articles = await query_adapter.find_all(source_id=source_id)

        # Assert
        assert len(articles) == 1, "Debe retornar un artículo"
        assert str(articles[0].source_id) == str(
            source_id
        ), "El source_id debe coincidir"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_all_with_limit(
        self, query_adapter, mock_session, sample_article_model
    ):
        """Debería aplicar límite cuando se proporciona."""
        # Arrange
        limit = 10

        mock_result = AsyncMock()
        mock_result.scalars = Mock(
            return_value=Mock(all=Mock(return_value=[sample_article_model]))
        )
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        articles = await query_adapter.find_all(limit=limit)

        # Assert
        assert len(articles) == 1, "Debe retornar artículos"
        mock_session.execute.assert_called_once()
        # Verificar que el statement incluye limit (esto se verifica en la llamada)

    @pytest.mark.asyncio
    async def test_find_all_with_offset(
        self, query_adapter, mock_session, sample_article_model
    ):
        """Debería aplicar offset cuando se proporciona."""
        # Arrange
        offset = 5

        mock_result = AsyncMock()
        mock_result.scalars = Mock(
            return_value=Mock(all=Mock(return_value=[sample_article_model]))
        )
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        articles = await query_adapter.find_all(offset=offset)

        # Assert
        assert len(articles) == 1, "Debe retornar artículos"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_returns_true_correctly(self, query_adapter, mock_session):
        """Debería retornar True cuando el artículo existe."""
        # Arrange
        article_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar = Mock(return_value=True)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        exists = await query_adapter.exists(article_id)

        # Assert
        assert exists is True, "Debe retornar True cuando existe"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_returns_false_correctly(self, query_adapter, mock_session):
        """Debería retornar False cuando el artículo no existe."""
        # Arrange
        article_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar = Mock(return_value=False)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        exists = await query_adapter.exists(article_id)

        # Assert
        assert exists is False, "Debe retornar False cuando no existe"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_with_no_filters(self, query_adapter, mock_session):
        """Debería contar todos los artículos sin filtros."""
        # Arrange
        expected_count = 42

        mock_result = AsyncMock()
        mock_result.scalar = Mock(return_value=expected_count)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        count = await query_adapter.count()

        # Assert
        assert count == expected_count, f"Debe retornar {expected_count}"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_with_source_id_filter(self, query_adapter, mock_session):
        """Debería contar artículos filtrados por source_id."""
        # Arrange
        source_id = RssFeedId(str(uuid4()))
        expected_count = 15

        mock_result = AsyncMock()
        mock_result.scalar = Mock(return_value=expected_count)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        count = await query_adapter.count(source_id=source_id)

        # Assert
        assert count == expected_count, f"Debe retornar {expected_count}"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_all_returns_empty_list_when_no_results(
        self, query_adapter, mock_session
    ):
        """Debería retornar lista vacía cuando no hay resultados."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        articles = await query_adapter.find_all()

        # Assert
        assert articles == [], "Debe retornar lista vacía"
        assert isinstance(articles, list), "Debe retornar una lista"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_returns_zero_when_no_articles(
        self, query_adapter, mock_session
    ):
        """Debería retornar 0 cuando no hay artículos."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar = Mock(return_value=0)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        count = await query_adapter.count()

        # Assert
        assert count == 0, "Debe retornar 0"
        mock_session.execute.assert_called_once()
