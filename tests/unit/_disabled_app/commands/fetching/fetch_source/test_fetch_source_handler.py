"""Tests para FetchSourceHandler."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.app.commands.fetching.fetch_source.command import FetchSourceCommand
from src.app.commands.fetching.fetch_source.handler import FetchSourceHandler
from src.rss.feed.domain.aggregates import RssFeed
from src.rss.feed.domain.value_objects import RssFeedId
from src.scraping.domain.aggregates import Scraping


class TestFetchSourceHandler:
    """Tests para FetchSourceHandler."""

    @pytest.fixture
    def mock_repositories(self):
        """Crea mocks de repositorios."""
        return {
            "source_repository": AsyncMock(),
            "article_repository": AsyncMock(),
            "fetch_session_repository": AsyncMock(),
        }

    @pytest.fixture
    def mock_services(self):
        """Crea mocks de servicios."""
        return {
            "source_fetching_service": AsyncMock(),
            "error_tracking_service": Mock(),
            "event_publisher": AsyncMock(),
            "logger": Mock(),
        }

    @pytest.fixture
    def mock_adapters(self):
        """Crea mocks de query adapters."""
        return {
            "source_by_id_adapter": AsyncMock(),
        }

    @pytest.fixture
    def handler(self, mock_repositories, mock_services, mock_adapters):
        """Crea handler con dependencias mockeadas."""
        # Configurar logger mock
        mock_logger = mock_services["logger"]
        mock_logger.bind.return_value = mock_logger
        mock_logger.debug = Mock()
        mock_logger.info = Mock()
        mock_logger.success = Mock()
        mock_logger.error = Mock()

        return FetchSourceHandler(
            source_repository=mock_repositories["source_repository"],
            article_repository=mock_repositories["article_repository"],
            fetch_session_repository=mock_repositories["fetch_session_repository"],
            source_fetching_service=mock_services["source_fetching_service"],
            error_tracking_service=mock_services["error_tracking_service"],
            event_publisher=mock_services["event_publisher"],
            logger=mock_services["logger"],
            source_by_id_adapter=mock_adapters["source_by_id_adapter"],
        )

    @pytest.fixture
    def sample_fetch_session(self):
        """Crea FetchSession de ejemplo."""
        fetch_session = Mock(spec=FetchSession)
        fetch_session.id = uuid4()
        fetch_session.domain_events = []
        fetch_session.start_source_fetch = Mock()
        fetch_session.complete_source_fetch = Mock()
        fetch_session.fail_source_fetch = Mock()
        fetch_session.mark_events_as_committed = Mock()
        return fetch_session

    @pytest.fixture
    def sample_rss_feed(self):
        """Crea Source de ejemplo."""
        source = Mock(spec=Source)
        source.id = RssFeedId(str(uuid4()))
        source.name = "Test RssFeed"
        source.url = "https://example.com/feed.xml"
        source.domain_events = []
        source.mark_events_as_committed = Mock()
        return source

    @pytest.mark.asyncio
    async def test_handle_fetch_success(
        self,
        handler,
        mock_repositories,
        mock_services,
        mock_adapters,
        sample_fetch_session,
        sample_source,
    ):
        """Debería ejecutar fetch exitosamente."""
        # Arrange
        command = FetchSourceCommand(
            fetch_session_id=str(sample_fetch_session.id),
            source_id=str(sample_source.id),
        )

        # Mock repositories
        mock_repositories["fetch_session_repository"].find_by_id.return_value = (
            sample_fetch_session
        )
        mock_repositories["source_repository"].find_by_id.return_value = sample_source
        mock_adapters["source_by_id_adapter"].get_by_id.return_value = sample_source

        # Mock fetch result
        mock_fetch_result = Mock()
        mock_fetch_result.total_articles_discovered = 10
        mock_fetch_result.total_articles_created = 8
        mock_fetch_result.article_ids = ["art1", "art2", "art3"]
        mock_services["source_fetching_service"].fetch_sources.return_value = (
            mock_fetch_result
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.articles_discovered == 10
        assert result.articles_created == 8
        assert result.articles_duplicated == 2
        assert len(result.article_ids) == 3

        # Verificar que se llamaron los métodos correctos
        sample_fetch_session.start_source_fetch.assert_called_once_with(
            sample_source.id
        )
        sample_fetch_session.complete_source_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_fetch_session_not_found(self, handler, mock_repositories):
        """Debería fallar cuando la sesión no existe."""
        # Arrange
        command = FetchSourceCommand(
            fetch_session_id=str(uuid4()),
            source_id=str(uuid4()),
        )

        # Mock repository para retornar None
        mock_repositories["fetch_session_repository"].find_by_id.return_value = None

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "no encontrada" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_handle_source_not_found(
        self, handler, mock_repositories, mock_adapters, sample_fetch_session
    ):
        """Debería fallar cuando el source no existe."""
        # Arrange
        command = FetchSourceCommand(
            fetch_session_id=str(sample_fetch_session.id),
            source_id=str(uuid4()),
        )

        # Mock repositories
        mock_repositories["fetch_session_repository"].find_by_id.return_value = (
            sample_fetch_session
        )
        mock_adapters["source_by_id_adapter"].get_by_id.return_value = None

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "no encontrado" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_handle_fetch_failure(
        self,
        handler,
        mock_repositories,
        mock_services,
        mock_adapters,
        sample_fetch_session,
        sample_source,
    ):
        """Debería manejar errores durante el fetch."""
        # Arrange
        command = FetchSourceCommand(
            fetch_session_id=str(sample_fetch_session.id),
            source_id=str(sample_source.id),
        )

        # Mock repositories
        mock_repositories["fetch_session_repository"].find_by_id.return_value = (
            sample_fetch_session
        )
        mock_repositories["source_repository"].find_by_id.return_value = sample_source
        mock_adapters["source_by_id_adapter"].get_by_id.return_value = sample_source

        # Mock fetch service para lanzar error
        mock_services["source_fetching_service"].fetch_sources.side_effect = Exception(
            "Network error"
        )

        # Mock error tracking service
        mock_error_event = Mock()
        mock_error_event.category = Mock(value="NETWORK_ERROR")
        mock_error_event.severity = Mock(value="HIGH")
        mock_services["error_tracking_service"].create_error_event.return_value = (
            mock_error_event
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "Network error" in result.error_message
        assert result.error_type == "Exception"
        assert result.is_recoverable is True

        # Verificar que se marcó como fallido
        sample_fetch_session.fail_source_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_with_timeout(
        self,
        handler,
        mock_repositories,
        mock_services,
        mock_adapters,
        sample_fetch_session,
        sample_source,
    ):
        """Debería manejar timeout correctamente."""
        # Arrange
        command = FetchSourceCommand(
            fetch_session_id=str(sample_fetch_session.id),
            source_id=str(sample_source.id),
            timeout_seconds=5,
        )

        # Mock repositories
        mock_repositories["fetch_session_repository"].find_by_id.return_value = (
            sample_fetch_session
        )
        mock_repositories["source_repository"].find_by_id.return_value = sample_source
        mock_adapters["source_by_id_adapter"].get_by_id.return_value = sample_source

        # Mock fetch service para lanzar timeout
        import asyncio

        mock_services["source_fetching_service"].fetch_sources.side_effect = (
            asyncio.TimeoutError("Timeout")
        )

        # Mock error tracking service
        mock_error_event = Mock()
        mock_error_event.category = Mock(value="TIMEOUT")
        mock_error_event.severity = Mock(value="MEDIUM")
        mock_services["error_tracking_service"].create_error_event.return_value = (
            mock_error_event
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.error_type == "TimeoutError"

        # Verificar que se marcó como fallido
        sample_fetch_session.fail_source_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_publishes_domain_events(
        self,
        handler,
        mock_repositories,
        mock_services,
        mock_adapters,
        sample_fetch_session,
        sample_source,
    ):
        """Debería publicar eventos de dominio correctamente."""
        # Arrange
        command = FetchSourceCommand(
            fetch_session_id=str(sample_fetch_session.id),
            source_id=str(sample_source.id),
        )

        # Mock repositories
        mock_repositories["fetch_session_repository"].find_by_id.return_value = (
            sample_fetch_session
        )
        mock_repositories["source_repository"].find_by_id.return_value = sample_source
        mock_adapters["source_by_id_adapter"].get_by_id.return_value = sample_source

        # Mock fetch result
        mock_fetch_result = Mock()
        mock_fetch_result.total_articles_discovered = 5
        mock_fetch_result.total_articles_created = 5
        mock_fetch_result.article_ids = []
        mock_services["source_fetching_service"].fetch_sources.return_value = (
            mock_fetch_result
        )

        # Mock domain events
        mock_event1 = Mock()
        mock_event2 = Mock()
        sample_fetch_session.domain_events = [mock_event1]
        sample_source.domain_events = [mock_event2]

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True

        # Verificar que se publicaron eventos
        assert mock_services["event_publisher"].publish.call_count == 2

        # Verificar que se marcaron como committed
        sample_fetch_session.mark_events_as_committed.assert_called_once()
        sample_source.mark_events_as_committed.assert_called_once()
