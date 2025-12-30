"""Tests para StartFetchSessionHandler con soporte multi-source."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.app.commands.fetching.start_fetch_session.command import (
    StartFetchSessionCommand,
)
from src.app.commands.fetching.start_fetch_session.handler import (
    StartFetchSessionHandler,
)
from src.rss.feed.domain.aggregates import RssFeed
from src.rss.feed.domain.value_objects import RssFeedId
from src.scraping.domain.aggregates import Scraping


class TestStartFetchSessionHandler:
    """Tests para StartFetchSessionHandler."""

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
            "fetch_session_factory": Mock(),
            "source_fetching_service": AsyncMock(),
            "error_tracking_service": Mock(),
            "event_publisher": AsyncMock(),
            "logger": Mock(),
        }

    @pytest.fixture
    def mock_adapters(self):
        """Crea mocks de query adapters."""
        return {
            "sources_list_adapter": AsyncMock(),
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
        mock_logger.exception = Mock()

        return StartFetchSessionHandler(
            source_repository=mock_repositories["source_repository"],
            article_repository=mock_repositories["article_repository"],
            fetch_session_repository=mock_repositories["fetch_session_repository"],
            fetch_session_factory=mock_services["fetch_session_factory"],
            source_fetching_service=mock_services["source_fetching_service"],
            error_tracking_service=mock_services["error_tracking_service"],
            event_publisher=mock_services["event_publisher"],
            logger=mock_services["logger"],
            sources_list_adapter=mock_adapters["sources_list_adapter"],
            source_by_id_adapter=mock_adapters["source_by_id_adapter"],
        )

    @pytest.fixture
    def sample_sources(self):
        """Crea sources de ejemplo."""
        return [
            {
                "source_id": str(uuid4()),
                "name": "Test RssFeed 1",
                "url": "https://example.com/feed1.xml",
                "is_active": True,
            },
            {
                "source_id": str(uuid4()),
                "name": "Test RssFeed 2",
                "url": "https://example.com/feed2.xml",
                "is_active": True,
            },
        ]

    @pytest.mark.asyncio
    async def test_handle_with_multiple_sources_success(
        self, handler, mock_repositories, mock_services, mock_adapters, sample_sources
    ):
        """Debería procesar múltiples sources exitosamente."""
        # Arrange
        command = StartFetchSessionCommand(
            source_ids=[s["source_id"] for s in sample_sources],
            max_concurrent_sources=2,
            timeout_seconds=30,
        )

        # Mock query adapter para retornar sources (dicts)
        mock_adapters["source_by_id_adapter"].get_by_id.side_effect = sample_sources

        # Mock repository para retornar Source aggregates reales
        from src.domain.value_objects.source.source_health import RssFeedHealth
        from src.domain.value_objects.source.source_identity import RssFeedIdentity
        from src.domain.value_objects.source.source_metadata import RssFeedMetadata

        mock_sources = []
        for src_data in sample_sources:
            mock_source = Mock(spec=Source)
            mock_source.id = RssFeedId(src_data["source_id"])
            mock_source.name = src_data["name"]
            mock_source.url = src_data["url"]
            mock_source.is_active = src_data["is_active"]
            mock_source.domain_events = []
            mock_source.mark_events_as_committed = Mock()
            mock_sources.append(mock_source)

        mock_repositories["source_repository"].find_by_id.side_effect = mock_sources

        # Mock scraping session factory
        mock_scraping_session = Mock(spec=Scraping)
        mock_scraping_session.id = Mock()
        mock_scraping_session.id.__str__ = Mock(return_value=str(uuid4()))
        mock_scraping_session.domain_events = []
        mock_scraping_session.mark_events_as_committed = Mock()
        mock_services["fetch_session_factory"].create_multi_source = Mock(
            return_value=mock_scraping_session
        )

        # Mock fetch result
        mock_fetch_result = Mock()
        mock_fetch_result.total_articles_created = 10
        mock_fetch_result.total_articles_discovered = 12
        mock_fetch_result.successful_sources = 2
        mock_fetch_result.failed_sources = 0
        mock_fetch_result.article_ids = ["art1", "art2"]
        mock_services["source_fetching_service"].fetch_sources.return_value = (
            mock_fetch_result
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.sources_count == 2
        assert result.articles_created == 10
        assert len(result.article_ids) == 2

    @pytest.mark.asyncio
    async def test_handle_with_no_sources_raises_error(self, handler, mock_adapters):
        """Debería lanzar error cuando no hay sources disponibles."""
        # Arrange
        command = StartFetchSessionCommand(
            source_ids=[],
            max_concurrent_sources=5,
        )

        # Mock query adapter para retornar lista vacía
        mock_adapters["sources_list_adapter"].get_active.return_value = []

        # Act & Assert
        with pytest.raises(ValueError, match="No hay sources válidas disponibles"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_handle_with_nonexistent_source(self, handler, mock_adapters):
        """Debería manejar sources no existentes correctamente."""
        # Arrange
        command = StartFetchSessionCommand(
            source_ids=[str(uuid4())],  # Usar UUID válido
            max_concurrent_sources=5,
        )

        # Mock query adapter para retornar None
        mock_adapters["source_by_id_adapter"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(
            ValueError, match="Ninguna de las sources especificadas está disponible"
        ):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_handle_with_inactive_source(self, handler, mock_adapters):
        """Debería omitir sources inactivas."""
        # Arrange
        inactive_source = {
            "source_id": str(uuid4()),
            "name": "Inactive RssFeed",
            "url": "https://example.com/feed.xml",
            "is_active": False,
        }

        command = StartFetchSessionCommand(
            source_ids=[inactive_source["source_id"]],
            max_concurrent_sources=5,
        )

        # Mock query adapter
        mock_adapters["source_by_id_adapter"].get_by_id.return_value = inactive_source

        # Act & Assert
        with pytest.raises(
            ValueError, match="Ninguna de las sources especificadas está disponible"
        ):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_handle_filters_none_source_ids(self, handler, mock_adapters):
        """Debería filtrar None values en source_ids automáticamente."""
        # Arrange - Command con None en la lista (simula el bug original)
        valid_source_id = str(uuid4())
        command = StartFetchSessionCommand(
            source_ids=[None, valid_source_id, None],  # Incluye None values
            max_concurrent_sources=5,
        )

        # El command debería filtrar None automáticamente en __post_init__
        assert None not in command.source_ids
        assert len(command.source_ids) == 1
        assert command.source_ids[0] == valid_source_id

        # Mock query adapter para retornar source válida
        valid_source = {
            "source_id": valid_source_id,
            "name": "Valid RssFeed",
            "url": "https://example.com/feed.xml",
            "is_active": True,
        }
        mock_adapters["source_by_id_adapter"].get_by_id.return_value = valid_source

        # Mock repository
        from src.domain.value_objects.source.source_identity import RssFeedIdentity

        mock_source = Mock(spec=Source)
        mock_source.id = RssFeedId(valid_source_id)
        mock_source.name = valid_source["name"]
        mock_source.url = valid_source["url"]
        mock_source.is_active = True
        mock_source.domain_events = []
        mock_source.mark_events_as_committed = Mock()

        mock_repositories = handler._source_repository
        mock_repositories.find_by_id.return_value = mock_source

        # Mock scraping session factory
        mock_scraping_session = Mock(spec=Scraping)
        mock_scraping_session.id = Mock()
        mock_scraping_session.id.__str__ = Mock(return_value=str(uuid4()))
        mock_scraping_session.domain_events = []
        mock_scraping_session.mark_events_as_committed = Mock()

        from src.scraping.domain.factories import ScrapingFactory

        handler._fetch_session_factory = Mock(spec=ScrapingFactory)
        handler._fetch_session_factory.create_multi_source = Mock(
            return_value=mock_scraping_session
        )

        # Mock fetch result
        mock_fetch_result = Mock()
        mock_fetch_result.total_articles_created = 5
        mock_fetch_result.total_articles_discovered = 5
        mock_fetch_result.successful_sources = 1
        mock_fetch_result.failed_sources = 0
        mock_fetch_result.article_ids = ["art1"]
        handler._source_fetching_service.fetch_sources.return_value = mock_fetch_result

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.sources_count == 1  # Solo 1 source válida procesada
