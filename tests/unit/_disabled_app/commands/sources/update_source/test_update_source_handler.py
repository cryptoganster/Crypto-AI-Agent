"""Tests para UpdateSourceHandler."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.rss.feed.app.commands.update_source.command import UpdateRssFeedCommand
from src.rss.feed.app.commands.update_source.exception import InvalidSourceUpdateError
from src.rss.feed.app.commands.update_source.handler import UpdateSourceHandler
from src.rss.feed.app.commands.update_source.validator import UpdateSourceValidator
from src.rss.feed.domain.aggregates import RssFeed
from src.rss.feed.domain.value_objects import RssFeedId
from src.rss.feed.domain.value_objects.name import RssFeedName
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl
from src.rss.feed.domain.value_objects.status import RssFeedStatus


class TestUpdateSourceHandler:
    """Tests para UpdateSourceHandler."""

    @pytest.fixture
    def mock_source_query(self):
        """Mock para source query."""
        return Mock()

    @pytest.fixture
    def mock_source_repository(self):
        """Mock para source repository."""
        mock = Mock()
        mock.save = AsyncMock()
        return mock

    @pytest.fixture
    def validator(self):
        """Validator real."""
        return UpdateSourceValidator()

    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        mock = Mock()
        mock.bind = Mock(return_value=mock)
        mock.info = Mock()
        mock.error = Mock()
        mock.exception = Mock()
        return mock

    @pytest.fixture
    def mock_error_tracking_service(self):
        """Mock para error tracking service."""
        mock = Mock()
        mock.create_error_event = Mock(
            return_value=Mock(category="test", severity="error")
        )
        return mock

    @pytest.fixture
    def handler(
        self,
        mock_source_query,
        mock_source_repository,
        validator,
        mock_logger,
        mock_error_tracking_service,
    ):
        """Handler con dependencias mockeadas."""
        return UpdateSourceHandler(
            source_query=mock_source_query,
            source_repository=mock_source_repository,
            validator=validator,
            logger=mock_logger,
            error_tracking_service=mock_error_tracking_service,
        )

    @pytest.fixture
    def sample_rss_feed(self):
        """Source de ejemplo."""
        source_id = SourceId.generate()
        return RssFeed(
            source_id=source_id,
            name=RssFeedName("Test RssFeed"),
            url=RssFeedUrl("https://example.com/feed.xml"),
        )

    @pytest.mark.asyncio
    async def test_handle_with_valid_command_succeeds(
        self, handler, mock_source_query, mock_source_repository, sample_source
    ):
        """Debería manejar comando válido exitosamente."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id=str(sample_source.id),
            name="Updated Name",
        )
        mock_source_query.get_by_id = AsyncMock(return_value=sample_source)

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.source_id == str(sample_source.id)
        mock_source_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_with_invalid_command_returns_failure(
        self, handler, mock_source_query, mock_source_repository
    ):
        """Debería retornar failure cuando el comando es inválido."""
        # Arrange - comando sin source_id
        command = UpdateRssFeedCommand(
            source_id="",  # Inválido
            name="Updated Name",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "Validación fallida" in result.message
        assert result.error_code == "VALIDATION_ERROR"
        mock_source_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_with_no_updates_returns_failure(
        self, handler, mock_source_query, mock_source_repository
    ):
        """Debería retornar failure cuando no hay actualizaciones."""
        # Arrange - comando sin actualizaciones
        command = UpdateRssFeedCommand(
            source_id=str(uuid4()),
            # Sin name, description, ni source_config
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "Validación fallida" in result.message
        mock_source_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_with_nonexistent_source_returns_not_found(
        self, handler, mock_source_query, mock_source_repository
    ):
        """Debería retornar not found cuando el source no existe."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id=str(uuid4()),
            name="Updated Name",
        )
        mock_source_query.get_by_id = AsyncMock(return_value=None)

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "no encontrado" in result.message.lower()
        mock_source_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_with_invalid_config_returns_failure(
        self, handler, mock_source_query, mock_source_repository, sample_source
    ):
        """Debería retornar failure cuando la configuración es inválida."""
        # Arrange
        command = UpdateRssFeedCommand(
            source_id=str(sample_source.id),
            source_config={"priority": 999},  # Fuera de rango (1-10)
        )
        mock_source_query.get_by_id = AsyncMock(return_value=sample_source)

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert "Validación fallida" in result.message
        mock_source_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_validator_exception_is_caught_and_converted_to_failure(
        self, handler, mock_source_query, mock_source_repository
    ):
        """Debería capturar InvalidSourceUpdateError y convertirla a failure result."""
        # Arrange - comando que causará excepción en validator
        command = UpdateRssFeedCommand(
            source_id="valid-id",
            name="",  # Nombre vacío causará excepción
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.error_code == "VALIDATION_ERROR"
        assert "Validación fallida" in result.message
        # Verificar que el validator lanzó la excepción correctamente
        assert "name debe ser string no vacío" in result.message
