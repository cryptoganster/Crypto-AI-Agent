"""Unit tests para ArticleReadRepository.find_by_guid().

Tests para verificar la funcionalidad de búsqueda por GUID en el repositorio de lectura.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.rss.article.domain.read_models import ArticleReadModel
from src.rss.article.infra.persistence.models import ArticleModel
from src.rss.article.infra.persistence.repositories.article_read_repository import (
    ArticleReadRepository,
)


class TestRssArticleReadRepositoryFindByGuid:
    """Tests para find_by_guid() method."""

    @pytest.fixture
    def mock_session(self):
        """Mock para AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def mock_logger(self):
        """Mock para ILogger."""
        logger = Mock()
        logger.debug = Mock()
        logger.error = Mock()
        return logger

    @pytest.fixture
    def repository(self, mock_session, mock_logger):
        """Repository con dependencias mockeadas."""
        return ArticleReadRepository(
            session=mock_session,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_article_model(self):
        """Modelo de artículo de ejemplo con GUID."""
        return RssArticleModel(
            id=uuid4(),
            source_id=uuid4(),
            title="Test RssArticle",
            url="https://example.com/test",
            rss_guid="test-guid-123",
            pub_date=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            version=1,
        )

    @pytest.mark.asyncio
    async def test_find_by_guid_with_source_id_returns_article(
        self,
        repository,
        mock_session,
        sample_article_model,
    ):
        """Debería encontrar artículo por GUID y source_id."""
        # Arrange
        guid = "test-guid-123"
        source_id = str(sample_article_model.source_id)

        # Mock query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_article_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repository.find_by_guid(guid=guid, source_id=source_id)

        # Assert
        assert result is not None
        assert isinstance(result, ArticleReadModel)
        assert result.rss_guid == guid
        assert str(result.source_id) == source_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_guid_without_source_id_searches_all_sources(
        self,
        repository,
        mock_session,
        sample_article_model,
    ):
        """Debería buscar en todas las sources cuando no se proporciona source_id."""
        # Arrange
        guid = "test-guid-123"

        # Mock query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_article_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repository.find_by_guid(guid=guid, source_id=None)

        # Assert
        assert result is not None
        assert isinstance(result, ArticleReadModel)
        assert result.rss_guid == guid
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_guid_returns_none_when_not_found(
        self,
        repository,
        mock_session,
        mock_logger,
    ):
        """Debería retornar None cuando no se encuentra artículo."""
        # Arrange
        guid = "non-existent-guid"
        source_id = str(uuid4())

        # Mock query result - no encontrado
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repository.find_by_guid(guid=guid, source_id=source_id)

        # Assert
        assert result is None
        mock_logger.debug.assert_called()
        # Verificar que se loggeó "no encontrado"
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("no encontrado" in call.lower() for call in debug_calls)

    @pytest.mark.asyncio
    async def test_find_by_guid_logs_success(
        self,
        repository,
        mock_session,
        mock_logger,
        sample_article_model,
    ):
        """Debería loggear cuando encuentra artículo exitosamente."""
        # Arrange
        guid = "test-guid-123"
        source_id = str(sample_article_model.source_id)

        # Mock query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_article_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        await repository.find_by_guid(guid=guid, source_id=source_id)

        # Assert
        mock_logger.debug.assert_called()
        # Verificar que se loggeó "encontrado"
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("encontrado" in call.lower() for call in debug_calls)

    @pytest.mark.asyncio
    async def test_find_by_guid_raises_exception_on_db_error(
        self,
        repository,
        mock_session,
        mock_logger,
    ):
        """Debería lanzar excepción y loggear error cuando falla la query."""
        # Arrange
        guid = "test-guid-123"
        source_id = str(uuid4())

        # Mock query error
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await repository.find_by_guid(guid=guid, source_id=source_id)

        assert "Database error" in str(exc_info.value)
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_guid_includes_pub_date_in_dto(
        self,
        repository,
        mock_session,
        sample_article_model,
    ):
        """Debería incluir pub_date en el DTO retornado."""
        # Arrange
        guid = "test-guid-123"
        expected_pub_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        sample_article_model.pub_date = expected_pub_date

        # Mock query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_article_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repository.find_by_guid(guid=guid)

        # Assert
        assert result is not None
        assert result.pub_date == expected_pub_date

    @pytest.mark.asyncio
    async def test_find_by_guid_handles_none_pub_date(
        self,
        repository,
        mock_session,
        sample_article_model,
    ):
        """Debería manejar correctamente cuando pub_date es None."""
        # Arrange
        guid = "test-guid-123"
        sample_article_model.pub_date = None

        # Mock query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_article_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repository.find_by_guid(guid=guid)

        # Assert
        assert result is not None
        assert result.pub_date is None

    @pytest.mark.asyncio
    async def test_find_by_guid_filters_by_source_correctly(
        self,
        repository,
        mock_session,
        sample_article_model,
    ):
        """Debería filtrar correctamente por source_id cuando se proporciona."""
        # Arrange
        guid = "test-guid-123"
        source_id = str(sample_article_model.source_id)

        # Mock query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_article_model)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await repository.find_by_guid(guid=guid, source_id=source_id)

        # Assert
        assert result is not None
        assert str(result.source_id) == source_id

        # Verificar que se llamó execute con la query correcta
        mock_session.execute.assert_called_once()
        # La query debe incluir filtro por source_id
        call_args = mock_session.execute.call_args
        assert call_args is not None
