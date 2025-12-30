"""Tests para UpdateFetchConfigMapper."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from src.app.commands.fetching.update_fetch_config.mapper import UpdateFetchConfigMapper
from src.rss.feed.domain.value_objects import RssFeedId
from src.scraping.domain.aggregates import Scraping


class TestUpdateFetchConfigMapper:
    """Tests para UpdateFetchConfigMapper."""

    def test_fetch_session_to_dto_serializes_correctly(self):
        """Debería serializar FetchSession a DTO correctamente."""
        # Arrange
        session = FetchSession.__new__(FetchSession)
        session._id = "sess-123"
        session._source_id = RssFeedId("src-456")

        # Mock fetch_manager
        mock_fetch_manager = Mock()
        mock_fetch_manager.next_fetch_at = datetime(
            2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc
        )

        # Mock fetch_state
        mock_fetch_state = Mock()
        mock_phase = Mock()
        mock_phase.value = "idle"
        mock_fetch_state.phase = mock_phase
        mock_fetch_manager.fetch_state = mock_fetch_state

        session._fetch_manager = mock_fetch_manager

        # Act
        dto = UpdateFetchConfigMapper.fetch_session_to_dto(session)

        # Assert
        assert dto["session_id"] == "sess-123"
        assert dto["source_id"] == "src-456"
        assert dto["status"] == "idle"
        assert dto["next_fetch_at"] == "2024-01-02T10:00:00+00:00"
        assert "can_start_fetch" in dto
        assert "is_fetch_active" in dto

    def test_fetch_session_to_dto_handles_none_next_fetch(self):
        """Debería manejar next_fetch_at None correctamente."""
        # Arrange
        session = FetchSession.__new__(FetchSession)
        session._id = "sess-789"
        session._source_id = RssFeedId("src-789")

        # Mock fetch_manager
        mock_fetch_manager = Mock()
        mock_fetch_manager.next_fetch_at = None

        # Mock fetch_state
        mock_fetch_state = Mock()
        mock_phase = Mock()
        mock_phase.value = "stopped"
        mock_fetch_state.phase = mock_phase
        mock_fetch_manager.fetch_state = mock_fetch_state

        session._fetch_manager = mock_fetch_manager

        # Act
        dto = UpdateFetchConfigMapper.fetch_session_to_dto(session)

        # Assert
        assert dto["next_fetch_at"] is None

    def test_fetch_session_to_dto_includes_all_required_fields(self):
        """Debería incluir todos los campos requeridos."""
        # Arrange
        session = FetchSession.__new__(FetchSession)
        session._id = "sess-complete"
        session._source_id = RssFeedId("src-complete")

        # Mock fetch_manager
        mock_fetch_manager = Mock()
        mock_fetch_manager.next_fetch_at = datetime.now(timezone.utc)

        # Mock fetch_state
        mock_fetch_state = Mock()
        mock_phase = Mock()
        mock_phase.value = "fetching"
        mock_fetch_state.phase = mock_phase
        mock_fetch_manager.fetch_state = mock_fetch_state

        session._fetch_manager = mock_fetch_manager

        # Act
        dto = UpdateFetchConfigMapper.fetch_session_to_dto(session)

        # Assert - Verificar que todos los campos requeridos están presentes
        required_fields = [
            "session_id",
            "source_id",
            "status",
            "can_start_fetch",
            "is_fetch_active",
            "next_fetch_at",
        ]
        for field in required_fields:
            assert field in dto, f"Campo requerido '{field}' faltante en DTO"

    def test_fetch_session_to_dto_converts_to_primitives(self):
        """Debería convertir Value Objects a primitivos."""
        # Arrange
        session = FetchSession.__new__(FetchSession)
        session._id = "sess-primitives"
        session._source_id = RssFeedId("src-primitives")

        # Mock fetch_manager con propiedades booleanas
        mock_fetch_manager = Mock()
        mock_fetch_manager.next_fetch_at = None
        mock_fetch_manager.can_start_fetch = True
        mock_fetch_manager.is_fetch_active = False

        # Mock fetch_state
        mock_fetch_state = Mock()
        mock_phase = Mock()
        mock_phase.value = "idle"
        mock_fetch_state.phase = mock_phase
        mock_fetch_manager.fetch_state = mock_fetch_state

        session._fetch_manager = mock_fetch_manager

        # Act
        dto = UpdateFetchConfigMapper.fetch_session_to_dto(session)

        # Assert - Verificar que son primitivos, no Value Objects
        assert isinstance(dto["session_id"], str)
        assert isinstance(dto["source_id"], str)
        assert isinstance(dto["status"], str)
        assert isinstance(dto["can_start_fetch"], bool)
        assert isinstance(dto["is_fetch_active"], bool)

    def test_fetch_session_to_dto_is_static_method(self):
        """Debería ser un método estático (no requiere instancia)."""
        # Arrange
        session = FetchSession.__new__(FetchSession)
        session._id = "sess-static"
        session._source_id = RssFeedId("src-static")

        # Mock fetch_manager
        mock_fetch_manager = Mock()
        mock_fetch_manager.next_fetch_at = None

        # Mock fetch_state
        mock_fetch_state = Mock()
        mock_phase = Mock()
        mock_phase.value = "idle"
        mock_fetch_state.phase = mock_phase
        mock_fetch_manager.fetch_state = mock_fetch_state

        session._fetch_manager = mock_fetch_manager

        # Act - Llamar sin instanciar la clase
        dto = UpdateFetchConfigMapper.fetch_session_to_dto(session)

        # Assert
        assert dto is not None
        assert dto["session_id"] == "sess-static"
