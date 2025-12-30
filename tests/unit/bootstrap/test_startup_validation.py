"""Tests para la validación de handlers críticos en el startup."""

from unittest.mock import MagicMock, Mock

import pytest

from src.bootstrap.config.app_config import AppConfig


class TestValidateCriticalHandlers:
    """Tests para _validate_critical_handlers()."""

    def test_validates_all_critical_handlers_are_registered(self):
        """Debería validar que todos los handlers críticos están registrados."""
        # Arrange
        from src.app.commands.fetching.start_fetch_session.command import (
            StartFetchSessionCommand,
        )
        from src.app.commands.pipelines.run_fetch_pipeline.command import (
            RunFetchPipelineCommand,
        )
        from src.app.commands.pipelines.run_processing_pipeline.command import (
            RunProcessingPipelineCommand,
        )
        from src.app.commands.pipelines.run_scraping_pipeline.command import (
            RunScrapingPipelineCommand,
        )

        # Mock mediator con todos los handlers registrados
        mock_mediator = Mock()
        mock_mediator._handler_registry = {
            RunFetchPipelineCommand: Mock(),
            StartFetchSessionCommand: Mock(),
            RunProcessingPipelineCommand: Mock(),
            RunScrapingPipelineCommand: Mock(),
        }

        # Mock config
        mock_config = Mock(spec=AppConfig)
        mock_config.is_development = True

        # Import the function
        from src.main import _validate_critical_handlers

        # Act & Assert - No debería lanzar excepción
        try:
            _validate_critical_handlers(mock_mediator, mock_config)
        except RuntimeError:
            pytest.fail(
                "No debería lanzar RuntimeError cuando todos los handlers están registrados"
            )

    def test_raises_runtime_error_when_handler_missing_in_development(self):
        """Debería lanzar RuntimeError cuando falta un handler crítico en development."""
        # Arrange
        from src.app.commands.pipelines.run_fetch_pipeline.command import (
            RunFetchPipelineCommand,
        )
        from src.app.commands.pipelines.run_processing_pipeline.command import (
            RunProcessingPipelineCommand,
        )
        from src.app.commands.pipelines.run_scraping_pipeline.command import (
            RunScrapingPipelineCommand,
        )

        # Mock mediator sin StartFetchSessionCommand
        mock_mediator = Mock()
        mock_mediator._handler_registry = {
            RunFetchPipelineCommand: Mock(),
            RunProcessingPipelineCommand: Mock(),
            RunScrapingPipelineCommand: Mock(),
            # StartFetchSessionCommand faltante
        }

        # Mock config en modo development
        mock_config = Mock(spec=AppConfig)
        mock_config.is_development = True

        # Import the function
        from src.main import _validate_critical_handlers

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            _validate_critical_handlers(mock_mediator, mock_config)

        # Verificar mensaje de error
        error_message = str(exc_info.value)
        assert "Critical handlers missing" in error_message
        assert "StartFetchSessionCommand" in error_message
        assert "register_pipeline_handlers" in error_message

    def test_raises_runtime_error_when_multiple_handlers_missing_in_development(self):
        """Debería lanzar RuntimeError listando todos los handlers faltantes en development."""
        # Arrange
        from src.app.commands.pipelines.run_fetch_pipeline.command import (
            RunFetchPipelineCommand,
        )

        # Mock mediator con solo un handler registrado
        mock_mediator = Mock()
        mock_mediator._handler_registry = {
            RunFetchPipelineCommand: Mock(),
        }

        # Mock config en modo development
        mock_config = Mock(spec=AppConfig)
        mock_config.is_development = True

        # Import the function
        from src.main import _validate_critical_handlers

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            _validate_critical_handlers(mock_mediator, mock_config)

        # Verificar que lista todos los handlers faltantes
        error_message = str(exc_info.value)
        assert "Critical handlers missing" in error_message
        assert "StartFetchSessionCommand" in error_message
        assert "RunProcessingPipelineCommand" in error_message
        assert "RunScrapingPipelineCommand" in error_message

    def test_raises_runtime_error_when_no_handlers_registered_in_development(self):
        """Debería lanzar RuntimeError cuando no hay handlers registrados en development."""
        # Arrange
        mock_mediator = Mock()
        mock_mediator._handler_registry = {}

        # Mock config en modo development
        mock_config = Mock(spec=AppConfig)
        mock_config.is_development = True

        # Import the function
        from src.main import _validate_critical_handlers

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            _validate_critical_handlers(mock_mediator, mock_config)

        # Verificar que lista todos los handlers críticos
        error_message = str(exc_info.value)
        assert "Critical handlers missing" in error_message
        assert "RunFetchPipelineCommand" in error_message
        assert "StartFetchSessionCommand" in error_message
        assert "RunProcessingPipelineCommand" in error_message
        assert "RunScrapingPipelineCommand" in error_message

    def test_validation_includes_all_critical_commands(self):
        """Debería validar exactamente los 4 comandos críticos especificados."""
        # Arrange
        mock_mediator = Mock()
        mock_mediator._handler_registry = {}

        # Mock config en modo development
        mock_config = Mock(spec=AppConfig)
        mock_config.is_development = True

        # Import the function
        from src.main import _validate_critical_handlers

        # Act
        with pytest.raises(RuntimeError) as exc_info:
            _validate_critical_handlers(mock_mediator, mock_config)

        # Assert - Verificar que menciona exactamente 4 comandos
        error_message = str(exc_info.value)

        # Contar cuántos comandos se mencionan
        critical_commands = [
            "RunFetchPipelineCommand",
            "StartFetchSessionCommand",
            "RunProcessingPipelineCommand",
            "RunScrapingPipelineCommand",
        ]

        for command in critical_commands:
            assert (
                command in error_message
            ), f"Comando crítico {command} no está en el mensaje de error"

    def test_logs_warning_in_production_when_handlers_missing(self):
        """Debería loggear warning en production cuando faltan handlers (no lanzar error)."""
        # Arrange
        from src.app.commands.pipelines.run_fetch_pipeline.command import (
            RunFetchPipelineCommand,
        )

        # Mock mediator con solo un handler registrado
        mock_mediator = Mock()
        mock_mediator._handler_registry = {
            RunFetchPipelineCommand: Mock(),
        }

        # Mock config en modo production
        mock_config = Mock(spec=AppConfig)
        mock_config.is_development = False

        # Import the function
        from src.main import _validate_critical_handlers

        # Act & Assert - No debería lanzar excepción en production
        try:
            _validate_critical_handlers(mock_mediator, mock_config)
        except RuntimeError:
            pytest.fail(
                "No debería lanzar RuntimeError en modo production - debería loggear warning y continuar"
            )
