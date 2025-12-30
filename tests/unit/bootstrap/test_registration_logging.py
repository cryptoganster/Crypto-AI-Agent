"""Tests para logging de registro de handlers."""

from typing import Type
from unittest.mock import Mock, call, patch

import pytest

from src.bootstrap.config.app_config import AppConfig
from src.bootstrap.containers.shared_infrastructure import SharedInfrastructure


class TestHandlerRegistrationLogging:
    """Tests para logging de registro de handlers."""

    @pytest.fixture
    def infra_with_mock_logger(self):
        """Crea SharedInfrastructure con logger mock."""
        # Create mock logger
        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.debug = Mock()
        mock_logger.error = Mock()
        mock_logger.warning = Mock()

        # Create mock mediator
        mock_mediator = Mock()
        mock_mediator._handler_registry = {}

        # Create minimal infra object
        infra = Mock(spec=SharedInfrastructure)
        infra.logger = mock_logger
        infra.mediator = mock_mediator
        infra.register_handler = SharedInfrastructure.register_handler.__get__(infra)
        infra.log_registered_handlers_summary = (
            SharedInfrastructure.log_registered_handlers_summary.__get__(infra)
        )

        return infra

    def test_register_handler_logs_success(self, infra_with_mock_logger):
        """Debería loggear éxito al registrar un handler."""
        # Arrange
        infra = infra_with_mock_logger
        mock_logger = infra.logger

        class TestCommand:
            pass

        class TestHandler:
            async def handle(self, command):
                pass

        handler = TestHandler()

        # Act
        infra.register_handler(TestCommand, handler)

        # Assert - Verificar que se loggeó el registro exitoso
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args

        assert call_args[0][0] == "Handler registrado en Mediator"
        assert call_args[1]["command_type"] == "TestCommand"
        assert call_args[1]["handler"] == "TestHandler"

    def test_register_handler_logs_command_name_correctly(self, infra_with_mock_logger):
        """Debería loggear el nombre del comando correctamente."""
        # Arrange
        infra = infra_with_mock_logger
        mock_logger = infra.logger

        class CreateRssArticleCommand:
            pass

        class CreateArticleHandler:
            pass

        handler = CreateArticleHandler()

        # Act
        infra.register_handler(CreateRssArticleCommand, handler)

        # Assert
        call_args = mock_logger.debug.call_args
        assert call_args[1]["command_type"] == "CreateRssArticleCommand"
        assert call_args[1]["handler"] == "CreateArticleHandler"

    def test_register_handler_logs_handler_class_name(self, infra_with_mock_logger):
        """Debería loggear el nombre de la clase del handler."""
        # Arrange
        infra = infra_with_mock_logger
        mock_logger = infra.logger

        class UpdateRssFeedCommand:
            pass

        class UpdateSourceHandler:
            async def handle(self, command):
                pass

        handler = UpdateSourceHandler()

        # Act
        infra.register_handler(UpdateRssFeedCommand, handler)

        # Assert
        call_args = mock_logger.debug.call_args
        assert call_args[1]["handler"] == "UpdateSourceHandler"

    def test_register_multiple_handlers_logs_each(self, infra_with_mock_logger):
        """Debería loggear cada handler registrado individualmente."""
        # Arrange
        infra = infra_with_mock_logger
        mock_logger = infra.logger

        class Command1:
            pass

        class Command2:
            pass

        class Command3:
            pass

        class Handler1:
            pass

        class Handler2:
            pass

        class Handler3:
            pass

        # Act
        infra.register_handler(Command1, Handler1())
        infra.register_handler(Command2, Handler2())
        infra.register_handler(Command3, Handler3())

        # Assert - Debería haber 3 llamadas a debug
        assert mock_logger.debug.call_count == 3

        # Verificar que cada comando fue loggeado
        calls = mock_logger.debug.call_args_list
        command_names = [call[1]["command_type"] for call in calls]

        assert "Command1" in command_names
        assert "Command2" in command_names
        assert "Command3" in command_names

    def test_register_handler_includes_structured_logging_fields(
        self, infra_with_mock_logger
    ):
        """Debería incluir campos estructurados en el log."""
        # Arrange
        infra = infra_with_mock_logger
        mock_logger = infra.logger

        class TestCommand:
            pass

        class TestHandler:
            pass

        handler = TestHandler()

        # Act
        infra.register_handler(TestCommand, handler)

        # Assert - Verificar campos estructurados
        call_args = mock_logger.debug.call_args

        # Debe tener el mensaje
        assert call_args[0][0] == "Handler registrado en Mediator"

        # Debe tener campos estructurados
        assert "command_type" in call_args[1]
        assert "handler" in call_args[1]

        # Los valores deben ser strings
        assert isinstance(call_args[1]["command_type"], str)
        assert isinstance(call_args[1]["handler"], str)


class TestHandlerRegistrationErrorLogging:
    """Tests para logging de errores en registro de handlers."""

    @pytest.fixture
    def infra_with_mock_logger(self):
        """Crea SharedInfrastructure con logger mock."""
        # Create mock logger
        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.debug = Mock()
        mock_logger.error = Mock()
        mock_logger.warning = Mock()

        # Create mock mediator
        mock_mediator = Mock()
        mock_mediator._handler_registry = {}

        # Create minimal infra object
        infra = Mock(spec=SharedInfrastructure)
        infra.logger = mock_logger
        infra.mediator = mock_mediator
        infra.register_handler = SharedInfrastructure.register_handler.__get__(infra)

        return infra

    def test_register_handler_logs_error_on_exception(self, infra_with_mock_logger):
        """Debería loggear error si el registro falla."""
        # Arrange
        infra = infra_with_mock_logger
        mock_logger = infra.logger

        class TestCommand:
            pass

        # Mock mediator para que lance excepción
        infra.mediator._handler_registry = Mock()
        infra.mediator._handler_registry.__setitem__ = Mock(
            side_effect=RuntimeError("Registry error")
        )

        handler = Mock()
        handler.__class__.__name__ = "TestHandler"

        # Act & Assert
        with pytest.raises(RuntimeError):
            infra.register_handler(TestCommand, handler)

        # Verificar que se loggeó el error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        assert call_args[0][0] == "Error registrando handler en Mediator"
        assert call_args[1]["command_type"] == "TestCommand"
        assert call_args[1]["handler"] == "TestHandler"
        assert "error" in call_args[1]

    def test_register_handler_logs_error_details(self, infra_with_mock_logger):
        """Debería loggear detalles del error."""
        # Arrange
        infra = infra_with_mock_logger
        mock_logger = infra.logger

        class FailCommand:
            pass

        # Mock mediator para que lance excepción con mensaje específico
        error_message = "Specific error message"
        infra.mediator._handler_registry = Mock()
        infra.mediator._handler_registry.__setitem__ = Mock(
            side_effect=ValueError(error_message)
        )

        handler = Mock()
        handler.__class__.__name__ = "FailHandler"

        # Act & Assert
        with pytest.raises(ValueError):
            infra.register_handler(FailCommand, handler)

        # Verificar que el error incluye el mensaje
        call_args = mock_logger.error.call_args
        assert error_message in call_args[1]["error"]

    def test_register_handler_logs_error_with_command_and_handler_info(
        self, infra_with_mock_logger
    ):
        """Debería incluir información del comando y handler en el error."""
        # Arrange
        infra = infra_with_mock_logger
        mock_logger = infra.logger

        class ImportantCommand:
            pass

        class ImportantHandler:
            pass

        # Mock mediator para que lance excepción
        infra.mediator._handler_registry = Mock()
        infra.mediator._handler_registry.__setitem__ = Mock(
            side_effect=Exception("Test error")
        )

        handler = ImportantHandler()

        # Act & Assert
        with pytest.raises(Exception):
            infra.register_handler(ImportantCommand, handler)

        # Verificar que el log incluye comando y handler
        call_args = mock_logger.error.call_args
        assert call_args[1]["command_type"] == "ImportantCommand"
        assert call_args[1]["handler"] == "ImportantHandler"


class TestStartupHandlerListLogging:
    """Tests para logging de lista completa de handlers al startup."""

    @pytest.fixture
    def infra_with_handlers(self):
        """Crea SharedInfrastructure con handlers registrados."""
        # Create mock logger
        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.debug = Mock()
        mock_logger.error = Mock()
        mock_logger.warning = Mock()

        # Create commands
        class Command1:
            pass

        class Command2:
            pass

        class Command3:
            pass

        # Create mock mediator with handlers
        mock_mediator = Mock()
        mock_mediator._handler_registry = {
            Command1: Mock(),
            Command2: Mock(),
            Command3: Mock(),
        }

        # Create minimal infra object
        infra = Mock(spec=SharedInfrastructure)
        infra.logger = mock_logger
        infra.mediator = mock_mediator
        infra.log_registered_handlers_summary = (
            SharedInfrastructure.log_registered_handlers_summary.__get__(infra)
        )

        return infra

    def test_log_registered_handlers_summary_logs_count(self, infra_with_handlers):
        """Debería loggear el número total de handlers registrados."""
        # Arrange
        infra = infra_with_handlers
        mock_logger = infra.logger

        # Act
        infra.log_registered_handlers_summary()

        # Assert
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args

        assert "handlers_count" in call_args[1]
        assert call_args[1]["handlers_count"] == 3

    def test_log_registered_handlers_summary_logs_handler_names(
        self, infra_with_handlers
    ):
        """Debería loggear los nombres de todos los handlers."""
        # Arrange
        infra = infra_with_handlers
        mock_logger = infra.logger

        # Act
        infra.log_registered_handlers_summary()

        # Assert
        call_args = mock_logger.info.call_args

        assert "handlers" in call_args[1]
        handlers_list = call_args[1]["handlers"]

        assert "Command1" in handlers_list
        assert "Command2" in handlers_list
        assert "Command3" in handlers_list

    def test_log_registered_handlers_summary_with_empty_registry(self):
        """Debería manejar registry vacío correctamente."""
        # Arrange
        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()

        mock_mediator = Mock()
        mock_mediator._handler_registry = {}

        infra = Mock(spec=SharedInfrastructure)
        infra.logger = mock_logger
        infra.mediator = mock_mediator
        infra.log_registered_handlers_summary = (
            SharedInfrastructure.log_registered_handlers_summary.__get__(infra)
        )

        # Act
        infra.log_registered_handlers_summary()

        # Assert
        call_args = mock_logger.info.call_args

        assert call_args[1]["handlers_count"] == 0
        assert call_args[1]["handlers"] == []

    def test_log_registered_handlers_summary_message(self, infra_with_handlers):
        """Debería incluir mensaje descriptivo."""
        # Arrange
        infra = infra_with_handlers
        mock_logger = infra.logger

        # Act
        infra.log_registered_handlers_summary()

        # Assert
        call_args = mock_logger.info.call_args
        message = call_args[0][0]

        assert (
            "Handlers registrados en Mediator" in message
            or "handlers" in message.lower()
        )
