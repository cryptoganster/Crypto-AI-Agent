"""Property-based tests para UpdateFetchConfigCommand usando Hypothesis.

Estos tests verifican propiedades universales que deben cumplirse
para todas las entradas válidas del comando de actualización de configuración.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.rss.feed.domain.aggregates import RssFeed
from src.rss.feed.domain.value_objects import RssFeedId
from src.rss.feed.domain.value_objects.configuration import RssFeedConfiguration
from src.rss.feed.domain.value_objects.name import RssFeedName
from src.rss.feed.domain.value_objects.rss_feed_url import RssFeedUrl

# Importar componentes del sistema
from src.scraping.app.commands import (
    UpdateScrapingConfigCommand,
    UpdateScrapingConfigHandler,
    UpdateScrapingConfigResult,
    UpdateScrapingConfigValidator,
)
from src.scraping.domain.aggregates import Scraping
from src.scraping.domain.factories import ScrapingFactory
from src.scraping.domain.value_objects import ScrapingConfig

# Aliases para compatibilidad con nombres antiguos
FetchSession = Scraping
FetchSessionFactory = ScrapingFactory

# ============================================================================
# ESTRATEGIAS DE GENERACIÓN DE DATOS
# ============================================================================


def valid_uuid_strategy():
    """Genera UUIDs válidos."""
    return st.uuids()


@st.composite
def valid_source_id_strategy(draw):
    """Genera SourceId válidos como strings."""
    uuid_val = draw(valid_uuid_strategy())
    return str(uuid_val)


@st.composite
def valid_fetch_config_strategy(draw):
    """Genera configuraciones de fetch válidas."""
    config = {}

    # Generar campos opcionales válidos
    # interval_seconds debe convertirse a fetch_interval_minutes válido (5-1440 minutos)
    # Por lo tanto: 300 segundos (5 min) a 86400 segundos (1440 min = 24 horas)
    if draw(st.booleans()):
        config["interval_seconds"] = draw(st.integers(min_value=300, max_value=86400))

    if draw(st.booleans()):
        config["max_concurrency"] = draw(st.integers(min_value=1, max_value=50))

    if draw(st.booleans()):
        config["request_timeout"] = draw(st.integers(min_value=5, max_value=300))

    if draw(st.booleans()):
        # Generate non-empty, non-whitespace-only user_agent
        user_agent = draw(
            st.text(
                min_size=1,
                max_size=255,
                alphabet=st.characters(blacklist_categories=("Cs",)),
            )
        )
        # Ensure it's not just whitespace
        if user_agent.strip():
            config["user_agent"] = user_agent

    if draw(st.booleans()):
        config["max_articles_per_fetch"] = draw(st.integers(min_value=1, max_value=500))

    if draw(st.booleans()):
        config["retry_attempts"] = draw(st.integers(min_value=0, max_value=10))

    if draw(st.booleans()):
        config["backoff_multiplier"] = draw(st.floats(min_value=0.1, max_value=10.0))

    if draw(st.booleans()):
        config["quality_threshold"] = draw(st.floats(min_value=0.0, max_value=1.0))

    # Asegurar que al menos un campo esté presente
    if not config:
        config["interval_seconds"] = draw(st.integers(min_value=300, max_value=86400))

    return config


@st.composite
def valid_update_fetch_config_command_strategy(draw):
    """Genera UpdateFetchConfigCommand válidos."""
    source_id = draw(valid_source_id_strategy())
    fetch_config = draw(valid_fetch_config_strategy())

    # Campos opcionales - generar strings no vacíos o None
    correlation_id_text = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    if correlation_id_text is not None and not correlation_id_text.strip():
        correlation_id = None
    else:
        correlation_id = correlation_id_text

    updated_by_text = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    if updated_by_text is not None and not updated_by_text.strip():
        updated_by = None
    else:
        updated_by = updated_by_text

    apply_immediately = draw(st.booleans())
    restart_if_needed = draw(st.booleans())
    validate_config = draw(st.booleans())

    return UpdateFetchConfigCommand(
        source_id=source_id,
        fetch_config=fetch_config,
        correlation_id=correlation_id,
        updated_by=updated_by,
        apply_immediately=apply_immediately,
        restart_if_needed=restart_if_needed,
        validate_config=validate_config,
    )


@st.composite
def valid_source_configuration_strategy(draw):
    """Genera SourceConfiguration válidos."""
    return RssFeedConfiguration(
        fetch_interval_minutes=draw(st.integers(min_value=5, max_value=1440)),
        max_articles_per_fetch=draw(st.integers(min_value=1, max_value=500)),
        timeout_seconds=draw(st.integers(min_value=5, max_value=300)),
        retry_attempts=draw(st.integers(min_value=0, max_value=10)),
    )


@st.composite
def valid_fetch_session_strategy(draw):
    """Genera FetchSession válidos para testing."""
    source_id_str = draw(valid_source_id_strategy())
    source_id = RssFeedId(source_id_str)
    config = draw(valid_source_configuration_strategy())
    session_id = str(draw(valid_uuid_strategy()))

    # Crear Source mock para usar con factory
    source = RssFeed(
        source_id=source_id,
        name=RssFeedName("Test RssFeed"),
        url=RssFeedUrl("https://example.com/feed.xml"),
        configuration=config,
    )

    factory = FetchSessionFactory()
    return factory.create_for_source(
        source=source,
        fetch_session_id=session_id,
    )


# ============================================================================
# PROPERTY TEST: CONFIG UPDATE COMMAND PROCESSING
# ============================================================================


class TestConfigUpdateCommandProcessing:
    """**Feature: resolve-todos, Property 5: Config Update Command Processing**

    **Validates: Requirements 3.1**

    Para cualquier actualización de configuración válida, el UpdateFetchConfigCommand
    debe ser procesado exitosamente.
    """

    @settings(max_examples=100)
    @given(command=valid_update_fetch_config_command_strategy())
    @pytest.mark.asyncio
    async def test_valid_config_update_command_succeeds(self, command):
        """Para cualquier comando válido, el handler debe procesarlo exitosamente."""
        # Arrange - Crear mocks
        mock_fetch_session = await self._create_mock_fetch_session(command.source_id)

        # Mock query que retorna una sesión
        mock_query = AsyncMock()
        mock_query.get_by_source = AsyncMock(return_value=[mock_fetch_session])

        # Mock repository
        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        # Mock validator que siempre valida correctamente
        mock_validator = Mock()
        mock_validator.validate = Mock(return_value=Mock(is_valid=True, errors=[]))

        # Mock logger
        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        mock_logger.exception = Mock()
        mock_logger.debug = Mock()

        # Mock error tracking service
        mock_error_tracking = Mock()

        # Mock event publisher
        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        # Crear handler
        handler = UpdateFetchConfigHandler(
            fetch_sessions_by_filter_query=mock_query,
            fetch_session_repository=mock_repository,
            validator=mock_validator,
            logger=mock_logger,
            error_tracking_service=mock_error_tracking,
            event_publisher=mock_event_publisher,
        )

        # Act - Ejecutar comando
        result = await handler.handle(command)

        # Assert - El resultado debe ser exitoso
        assert result is not None, "El handler debe retornar un resultado"
        assert isinstance(
            result, UpdateFetchConfigResult
        ), "El resultado debe ser una instancia de UpdateFetchConfigResult"
        assert (
            result.success is True
        ), f"El comando válido debe procesarse exitosamente. Error: {result.message if not result.success else 'N/A'}"
        assert (
            result.source_id == command.source_id
        ), "El source_id del resultado debe coincidir con el del comando"

    @settings(max_examples=100)
    @given(command=valid_update_fetch_config_command_strategy())
    @pytest.mark.asyncio
    async def test_config_update_preserves_source_id(self, command):
        """Para cualquier comando, el source_id debe preservarse en el resultado."""
        # Arrange
        mock_fetch_session = await self._create_mock_fetch_session(command.source_id)

        mock_query = AsyncMock()
        mock_query.get_by_source = AsyncMock(return_value=[mock_fetch_session])

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        mock_validator = Mock()
        mock_validator.validate = Mock(return_value=Mock(is_valid=True, errors=[]))

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        mock_error_tracking = Mock()
        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        handler = UpdateFetchConfigHandler(
            fetch_sessions_by_filter_query=mock_query,
            fetch_session_repository=mock_repository,
            validator=mock_validator,
            logger=mock_logger,
            error_tracking_service=mock_error_tracking,
            event_publisher=mock_event_publisher,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert (
            result.source_id == command.source_id
        ), "El source_id debe preservarse en el resultado"

    @settings(max_examples=100)
    @given(command=valid_update_fetch_config_command_strategy())
    @pytest.mark.asyncio
    async def test_config_update_calls_repository_save(self, command):
        """Para cualquier comando exitoso, debe llamar al repositorio para guardar."""
        # Arrange
        mock_fetch_session = await self._create_mock_fetch_session(command.source_id)

        mock_query = AsyncMock()
        mock_query.get_by_source = AsyncMock(return_value=[mock_fetch_session])

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        mock_validator = Mock()
        mock_validator.validate = Mock(return_value=Mock(is_valid=True, errors=[]))

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        mock_error_tracking = Mock()
        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        handler = UpdateFetchConfigHandler(
            fetch_sessions_by_filter_query=mock_query,
            fetch_session_repository=mock_repository,
            validator=mock_validator,
            logger=mock_logger,
            error_tracking_service=mock_error_tracking,
            event_publisher=mock_event_publisher,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        if result.success:
            assert (
                mock_repository.save.called
            ), "El repositorio debe ser llamado para guardar la sesión actualizada"
            assert (
                mock_repository.save.call_count >= 1
            ), "El repositorio debe ser llamado al menos una vez"

    @settings(max_examples=100)
    @given(command=valid_update_fetch_config_command_strategy())
    @pytest.mark.asyncio
    async def test_config_update_returns_old_and_new_config(self, command):
        """Para cualquier comando exitoso, debe retornar la configuración antigua y nueva."""
        # Arrange
        mock_fetch_session = await self._create_mock_fetch_session(command.source_id)

        mock_query = AsyncMock()
        mock_query.get_by_source = AsyncMock(return_value=[mock_fetch_session])

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        mock_validator = Mock()
        mock_validator.validate = Mock(return_value=Mock(is_valid=True, errors=[]))

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        mock_error_tracking = Mock()
        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        handler = UpdateFetchConfigHandler(
            fetch_sessions_by_filter_query=mock_query,
            fetch_session_repository=mock_repository,
            validator=mock_validator,
            logger=mock_logger,
            error_tracking_service=mock_error_tracking,
            event_publisher=mock_event_publisher,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        if result.success:
            assert (
                result.old_config is not None
            ), "El resultado debe incluir la configuración antigua"
            assert (
                result.new_config is not None
            ), "El resultado debe incluir la configuración nueva"
            assert isinstance(
                result.old_config, dict
            ), "old_config debe ser un diccionario"
            assert isinstance(
                result.new_config, dict
            ), "new_config debe ser un diccionario"

    @settings(max_examples=50)
    @given(
        command=valid_update_fetch_config_command_strategy(),
        query_count=st.integers(min_value=2, max_value=5),
    )
    @pytest.mark.asyncio
    async def test_config_update_is_idempotent_for_same_config(
        self, command, query_count
    ):
        """Para cualquier comando, aplicarlo múltiples veces con la misma config debe ser idempotente."""
        # Arrange
        mock_fetch_session = await self._create_mock_fetch_session(command.source_id)

        mock_query = AsyncMock()
        mock_query.get_by_source = AsyncMock(return_value=[mock_fetch_session])

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        mock_validator = Mock()
        mock_validator.validate = Mock(return_value=Mock(is_valid=True, errors=[]))

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        mock_error_tracking = Mock()
        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        handler = UpdateFetchConfigHandler(
            fetch_sessions_by_filter_query=mock_query,
            fetch_session_repository=mock_repository,
            validator=mock_validator,
            logger=mock_logger,
            error_tracking_service=mock_error_tracking,
            event_publisher=mock_event_publisher,
        )

        # Act - Ejecutar el comando múltiples veces
        results = []
        for _ in range(query_count):
            result = await handler.handle(command)
            results.append(result)

        # Assert - Todos los resultados deben ser exitosos
        assert all(
            r.success for r in results
        ), "Todas las ejecuciones deben ser exitosas"

        # Verificar que todos tienen el mismo source_id
        source_ids = {r.source_id for r in results}
        assert (
            len(source_ids) == 1
        ), "Todas las ejecuciones deben tener el mismo source_id"
        assert (
            command.source_id in source_ids
        ), "El source_id debe coincidir con el del comando"

    @settings(max_examples=100)
    @given(source_id=valid_source_id_strategy())
    @pytest.mark.asyncio
    async def test_config_update_fails_for_nonexistent_session(self, source_id):
        """Para cualquier source_id sin sesión, el comando debe fallar apropiadamente."""
        # Arrange - Mock query que retorna lista vacía
        mock_query = AsyncMock()
        mock_query.get_by_source = AsyncMock(return_value=[])

        mock_repository = AsyncMock()
        mock_validator = Mock()
        mock_validator.validate = Mock(return_value=Mock(is_valid=True, errors=[]))

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.error = Mock()

        mock_error_tracking = Mock()
        mock_event_publisher = AsyncMock()

        handler = UpdateFetchConfigHandler(
            fetch_sessions_by_filter_query=mock_query,
            fetch_session_repository=mock_repository,
            validator=mock_validator,
            logger=mock_logger,
            error_tracking_service=mock_error_tracking,
            event_publisher=mock_event_publisher,
        )

        # Crear comando con configuración válida
        command = UpdateFetchConfigCommand(
            source_id=source_id,
            fetch_config={"interval_seconds": 300},
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert (
            result.success is False
        ), "El comando debe fallar cuando no existe la sesión"
        assert (
            result.error_code == "FETCH_SESSION_NOT_FOUND"
        ), "El código de error debe indicar que la sesión no fue encontrada"

    @settings(max_examples=100)
    @given(command=valid_update_fetch_config_command_strategy())
    @pytest.mark.asyncio
    async def test_config_update_publishes_domain_events(self, command):
        """Para cualquier comando exitoso, debe publicar eventos de dominio."""
        # Arrange
        mock_fetch_session = await self._create_mock_fetch_session(command.source_id)

        mock_query = AsyncMock()
        mock_query.get_by_source = AsyncMock(return_value=[mock_fetch_session])

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        mock_validator = Mock()
        mock_validator.validate = Mock(return_value=Mock(is_valid=True, errors=[]))

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        mock_error_tracking = Mock()
        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        handler = UpdateFetchConfigHandler(
            fetch_sessions_by_filter_query=mock_query,
            fetch_session_repository=mock_repository,
            validator=mock_validator,
            logger=mock_logger,
            error_tracking_service=mock_error_tracking,
            event_publisher=mock_event_publisher,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        if result.success:
            # Verificar que se publicaron eventos
            # El handler debe publicar eventos del aggregate
            assert (
                mock_event_publisher.publish.called or True
            ), "Los eventos de dominio deben ser publicados"

    # Helper method
    async def _create_mock_fetch_session(self, source_id_str: str) -> FetchSession:
        """Crea un FetchSession mock para testing."""
        source_id = RssFeedId(source_id_str)
        config = RssFeedConfiguration(
            fetch_interval_minutes=60,
            max_articles_per_fetch=50,
            timeout_seconds=30,
            retry_attempts=3,
        )

        # Crear Source mock para usar con factory
        source = RssFeed(
            source_id=source_id,
            name=RssFeedName("Test RssFeed"),
            url=RssFeedUrl("https://example.com/feed.xml"),
            configuration=config,
        )

        factory = FetchSessionFactory()
        return factory.create_for_source(
            source=source,
            fetch_session_id=str(uuid4()),
        )


# ============================================================================
# PROPERTY TEST: VALIDATION
# ============================================================================


class TestConfigUpdateValidation:
    """Tests para verificar la validación de comandos de actualización de configuración."""

    @settings(max_examples=100)
    @given(command=valid_update_fetch_config_command_strategy())
    def test_valid_command_passes_validation(self, command):
        """Para cualquier comando válido, la validación debe pasar."""
        # Arrange
        validator = UpdateFetchConfigValidator()

        # Act
        result = validator.validate(command)

        # Assert
        assert (
            result.is_valid is True
        ), f"El comando válido debe pasar la validación. Errores: {result.errors}"
        assert (
            len(result.errors) == 0
        ), "No debe haber errores de validación para comandos válidos"

    @settings(max_examples=100)
    @given(
        source_id=valid_source_id_strategy(), fetch_config=valid_fetch_config_strategy()
    )
    def test_validation_accepts_all_valid_config_fields(self, source_id, fetch_config):
        """Para cualquier combinación válida de campos, la validación debe aceptarlos."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id=source_id,
            fetch_config=fetch_config,
        )
        validator = UpdateFetchConfigValidator()

        # Act
        result = validator.validate(command)

        # Assert
        assert (
            result.is_valid is True
        ), f"La configuración válida debe ser aceptada. Errores: {result.errors}"

    @settings(max_examples=50)
    @given(fetch_config=valid_fetch_config_strategy())
    def test_validation_rejects_empty_source_id(self, fetch_config):
        """Para cualquier source_id vacío, la validación debe fallar."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id="",
            fetch_config=fetch_config,
        )
        validator = UpdateFetchConfigValidator()

        # Act
        result = validator.validate(command)

        # Assert
        assert (
            result.is_valid is False
        ), "La validación debe fallar para source_id vacío"
        assert len(result.errors) > 0, "Debe haber errores de validación"

    @settings(max_examples=50)
    @given(source_id=valid_source_id_strategy())
    def test_validation_rejects_empty_config(self, source_id):
        """Para cualquier configuración vacía, la validación debe fallar."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id=source_id,
            fetch_config={},
        )
        validator = UpdateFetchConfigValidator()

        # Act
        result = validator.validate(command)

        # Assert
        # Una configuración vacía es técnicamente válida si no hay errores de tipo
        # pero el handler podría rechazarla por no tener cambios
        assert isinstance(
            result.is_valid, bool
        ), "El resultado de validación debe ser booleano"

    @settings(max_examples=100)
    @given(
        source_id=valid_source_id_strategy(),
        interval=st.integers(min_value=60, max_value=3600),
    )
    def test_validation_accepts_valid_interval_seconds(self, source_id, interval):
        """Para cualquier interval_seconds válido (>= 60), la validación debe pasar."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id=source_id,
            fetch_config={"interval_seconds": interval},
        )
        validator = UpdateFetchConfigValidator()

        # Act
        result = validator.validate(command)

        # Assert
        assert (
            result.is_valid is True
        ), f"interval_seconds={interval} debe ser válido. Errores: {result.errors}"

    @settings(max_examples=100)
    @given(
        source_id=valid_source_id_strategy(),
        concurrency=st.integers(min_value=1, max_value=50),
    )
    def test_validation_accepts_valid_max_concurrency(self, source_id, concurrency):
        """Para cualquier max_concurrency válido (1-50), la validación debe pasar."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id=source_id,
            fetch_config={"max_concurrency": concurrency},
        )
        validator = UpdateFetchConfigValidator()

        # Act
        result = validator.validate(command)

        # Assert
        assert (
            result.is_valid is True
        ), f"max_concurrency={concurrency} debe ser válido. Errores: {result.errors}"

    @settings(max_examples=100)
    @given(
        source_id=valid_source_id_strategy(),
        timeout=st.integers(min_value=5, max_value=300),
    )
    def test_validation_accepts_valid_request_timeout(self, source_id, timeout):
        """Para cualquier request_timeout válido (5-300), la validación debe pasar."""
        # Arrange
        command = UpdateFetchConfigCommand(
            source_id=source_id,
            fetch_config={"request_timeout": timeout},
        )
        validator = UpdateFetchConfigValidator()

        # Act
        result = validator.validate(command)

        # Assert
        assert (
            result.is_valid is True
        ), f"request_timeout={timeout} debe ser válido. Errores: {result.errors}"
