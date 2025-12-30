"""Tests para FetchFromSourcesMapper."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from src.app.commands.fetching.fetch_from_sources.mapper import FetchFromSourcesMapper
from src.rss.feed.domain.aggregates import RssFeed
from src.rss.feed.domain.value_objects import RssFeedId
from src.rss.feed.domain.value_objects.name import RssFeedName
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl
from src.rss.feed.domain.value_objects.status import RssFeedStatus
from src.scraping.domain.aggregates import Scraping


class TestFetchFromSourcesMapper:
    """Tests para FetchFromSourcesMapper."""

    def test_source_to_dto_serializes_correctly(self):
        """Debería serializar Source a DTO correctamente."""
        # Arrange
        source = Source.__new__(Source)
        source._id = RssFeedId("src-123")
        source._name = RssFeedName("Test RssFeed")
        source._url = RssFeedUrl("https://example.com/feed")
        source._status = RssFeedStatus.active()
        source._is_active = True

        # Act
        dto = FetchFromSourcesMapper.source_to_dto(source)

        # Assert
        assert dto["source_id"] == "src-123"
        assert dto["name"] == "Test RssFeed"
        assert dto["url"] == "https://example.com/feed"
        assert dto["is_active"] is True
        assert dto["status"] == "active"

    def test_sources_to_dto_list_serializes_multiple_sources(self):
        """Debería serializar lista de Sources correctamente."""
        # Arrange
        source1 = Source.__new__(Source)
        source1._id = RssFeedId("src-1")
        source1._name = RssFeedName("RssFeed 1")
        source1._url = RssFeedUrl("https://example1.com/feed")
        source1._status = RssFeedStatus.active()
        source1._is_active = True

        source2 = Source.__new__(Source)
        source2._id = RssFeedId("src-2")
        source2._name = RssFeedName("RssFeed 2")
        source2._url = RssFeedUrl("https://example2.com/feed")
        source2._status = RssFeedStatus.inactive()
        source2._is_active = False

        sources = [source1, source2]

        # Act
        dtos = FetchFromSourcesMapper.sources_to_dto_list(sources)

        # Assert
        assert len(dtos) == 2
        assert dtos[0]["source_id"] == "src-1"
        assert dtos[1]["source_id"] == "src-2"
        assert dtos[0]["is_active"] is True
        assert dtos[1]["is_active"] is False

    def test_sources_to_dto_list_handles_empty_list(self):
        """Debería manejar lista vacía correctamente."""
        # Arrange
        sources = []

        # Act
        dtos = FetchFromSourcesMapper.sources_to_dto_list(sources)

        # Assert
        assert dtos == []
        assert isinstance(dtos, list)

    def test_fetch_session_to_dto_serializes_correctly(self):
        """Debería serializar FetchSession a DTO correctamente."""
        # Arrange
        session = FetchSession.__new__(FetchSession)
        session._id = "sess-123"
        session._source_id = RssFeedId("src-456")

        # Mock fetch_manager con last_fetch_at
        mock_fetch_manager = Mock()
        mock_fetch_manager.last_fetch_at = datetime(
            2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc
        )

        # Mock fetch_state
        mock_fetch_state = Mock()
        mock_phase = Mock()
        mock_phase.value = "idle"
        mock_fetch_state.phase = mock_phase
        mock_fetch_manager.fetch_state = mock_fetch_state

        session._fetch_manager = mock_fetch_manager

        # Act
        dto = FetchFromSourcesMapper.fetch_session_to_dto(session)

        # Assert
        assert dto["session_id"] == "sess-123"
        assert dto["source_id"] == "src-456"
        assert dto["status"] == "idle"
        assert dto["last_fetch_at"] == "2024-01-01T12:00:00+00:00"

    def test_fetch_session_to_dto_handles_none_last_fetch(self):
        """Debería manejar last_fetch_at None correctamente."""
        # Arrange
        session = FetchSession.__new__(FetchSession)
        session._id = "sess-789"
        session._source_id = RssFeedId("src-789")

        # Mock fetch_manager con last_fetch_at None
        mock_fetch_manager = Mock()
        mock_fetch_manager.last_fetch_at = None

        # Mock fetch_state
        mock_fetch_state = Mock()
        mock_phase = Mock()
        mock_phase.value = "stopped"
        mock_fetch_state.phase = mock_phase
        mock_fetch_manager.fetch_state = mock_fetch_state

        session._fetch_manager = mock_fetch_manager

        # Act
        dto = FetchFromSourcesMapper.fetch_session_to_dto(session)

        # Assert
        assert dto["last_fetch_at"] is None

    def test_source_to_dto_converts_value_objects_to_strings(self):
        """Debería convertir Value Objects a strings."""
        # Arrange
        source = Source.__new__(Source)
        source._id = RssFeedId("src-convert")
        source._name = RssFeedName("Convert Test")
        source._url = RssFeedUrl("https://convert.com/feed")
        source._status = RssFeedStatus.suspended()
        source._is_active = False

        # Act
        dto = FetchFromSourcesMapper.source_to_dto(source)

        # Assert - Verificar que son strings, no Value Objects
        assert isinstance(dto["source_id"], str)
        assert isinstance(dto["name"], str)
        assert isinstance(dto["url"], str)
        assert isinstance(dto["status"], str)
        assert isinstance(dto["is_active"], bool)

    def test_all_methods_are_static(self):
        """Debería tener todos los métodos estáticos (no requiere instancia)."""
        # Arrange
        source = Source.__new__(Source)
        source._id = RssFeedId("src-static")
        source._name = RssFeedName("Static Test")
        source._url = RssFeedUrl("https://static.com/feed")
        source._status = RssFeedStatus.active()
        source._is_active = True

        # Act - Llamar sin instanciar la clase
        dto = FetchFromSourcesMapper.source_to_dto(source)
        dtos = FetchFromSourcesMapper.sources_to_dto_list([source])

        # Assert
        assert dto is not None
        assert dtos is not None
        assert len(dtos) == 1
