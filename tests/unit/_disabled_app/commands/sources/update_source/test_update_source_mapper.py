"""Tests para UpdateSourceMapper."""

from datetime import datetime, timezone
from unittest.mock import Mock, PropertyMock

import pytest

from src.rss.feed.app.commands.update_source.mapper import UpdateSourceMapper
from src.rss.feed.domain.aggregates import RssFeed
from src.rss.feed.domain.value_objects import RssFeedId
from src.rss.feed.domain.value_objects.description import RssFeedDescription
from src.rss.feed.domain.value_objects.name import RssFeedName
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl
from src.rss.feed.domain.value_objects.status import RssFeedStatus


def create_mock_source(
    source_id: str = "src-123",
    name: str = "Test RssFeed",
    url: str = "https://example.com/feed",
    description: str = "Test description",
    status: str = "active",
    is_active: bool = True,
    success_rate: float = 0.85,
    updated_at: datetime = None,
) -> Mock:
    """Helper para crear mock de Source con estructura correcta."""
    mock_source = Mock(spec=Source)

    # Configurar properties
    mock_source.id = RssFeedId(source_id)
    mock_source.name = RssFeedName(name)
    mock_source.url = RssFeedUrl(url)
    mock_source.description = RssFeedDescription(description) if description else None
    mock_source.status = (
        RssFeedStatus.active() if status == "active" else RssFeedStatus.inactive()
    )
    mock_source.is_active = is_active
    mock_source.updated_at = updated_at or datetime(
        2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc
    )

    # Mock metrics
    if success_rate is not None:
        mock_metrics = Mock()
        mock_metrics.success_rate = success_rate
        mock_source.metrics = mock_metrics
    else:
        mock_source.metrics = None

    return mock_source


class TestUpdateSourceMapper:
    """Tests para UpdateSourceMapper."""

    def test_source_to_summary_serializes_correctly(self):
        """Debería serializar Source a DTO correctamente."""
        # Arrange
        source = create_mock_source(
            source_id="src-123",
            name="Test RssFeed",
            url="https://example.com/feed",
            description="Test description",
            status="active",
            is_active=True,
            success_rate=0.85,
            updated_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Act
        dto = UpdateSourceMapper.source_to_summary(source)

        # Assert
        assert dto["id"] == "src-123"
        assert dto["name"] == "Test RssFeed"
        assert dto["url"] == "https://example.com/feed"
        assert dto["description"] == "Test description"
        assert dto["status"] == "active"
        assert dto["is_active"] is True
        assert dto["success_rate"] == 0.85
        assert dto["updated_at"] == "2024-01-01T12:00:00+00:00"

    def test_source_to_summary_handles_none_description(self):
        """Debería manejar description None correctamente."""
        # Arrange
        source = create_mock_source(
            source_id="src-123",
            description=None,
            success_rate=None,
        )

        # Act
        dto = UpdateSourceMapper.source_to_summary(source)

        # Assert
        assert dto["description"] is None
        assert dto["success_rate"] == 0.0

    def test_source_to_summary_handles_none_metrics(self):
        """Debería manejar metrics None correctamente."""
        # Arrange
        source = create_mock_source(
            source_id="src-123",
            description="Test",
            success_rate=None,
        )

        # Act
        dto = UpdateSourceMapper.source_to_summary(source)

        # Assert
        assert dto["success_rate"] == 0.0
        assert dto["is_active"] is True

    def test_source_to_summary_converts_value_objects_to_strings(self):
        """Debería convertir Value Objects a strings."""
        # Arrange
        source = create_mock_source(
            source_id="src-456",
            name="Another RssFeed",
            url="https://test.com/rss",
            description="Description",
            status="inactive",
            is_active=False,
            success_rate=None,
            updated_at=datetime(2024, 2, 1, 10, 30, 0, tzinfo=timezone.utc),
        )

        # Act
        dto = UpdateSourceMapper.source_to_summary(source)

        # Assert - Verificar que son strings, no Value Objects
        assert isinstance(dto["id"], str)
        assert isinstance(dto["name"], str)
        assert isinstance(dto["url"], str)
        assert isinstance(dto["description"], str)
        assert isinstance(dto["status"], str)
        assert isinstance(dto["updated_at"], str)

    def test_source_to_summary_includes_all_required_fields(self):
        """Debería incluir todos los campos requeridos."""
        # Arrange
        source = create_mock_source(
            source_id="src-789",
            name="Complete RssFeed",
            url="https://complete.com/feed",
            description="Complete",
            success_rate=1.0,
            updated_at=datetime(2024, 3, 1, 8, 0, 0, tzinfo=timezone.utc),
        )

        # Act
        dto = UpdateSourceMapper.source_to_summary(source)

        # Assert - Verificar que todos los campos requeridos están presentes
        required_fields = [
            "id",
            "name",
            "url",
            "description",
            "status",
            "is_active",
            "success_rate",
            "updated_at",
        ]
        for field in required_fields:
            assert field in dto, f"Campo requerido '{field}' faltante en DTO"

    def test_source_to_summary_is_static_method(self):
        """Debería ser un método estático (no requiere instancia)."""
        # Arrange
        source = create_mock_source(
            source_id="src-static",
            name="Static Test",
            url="https://static.com/feed",
            description=None,
            success_rate=None,
        )

        # Act - Llamar sin instanciar la clase
        dto = UpdateSourceMapper.source_to_summary(source)

        # Assert
        assert dto is not None
        assert dto["id"] == "src-static"
