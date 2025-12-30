"""Tests unitarios para RunProcessingPipelineHandler.

Estos tests verifican que el handler delega correctamente al Process Manager
y convierte el resultado apropiadamente.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.app.commands.pipelines.run_processing_pipeline.command import (
    RunProcessingPipelineCommand,
)
from src.app.commands.pipelines.run_processing_pipeline.handler import (
    RunProcessingPipelineHandler,
)
from src.app.commands.pipelines.run_processing_pipeline.result import (
    RunProcessingPipelineResult,
)
from src.app.process_managers.base_process_manager import ProcessingPipelineResult


class TestRunProcessingPipelineHandler:
    """Tests para RunProcessingPipelineHandler."""

    @pytest.fixture
    def mock_process_manager(self):
        """Crea un mock del ProcessingProcessManager."""
        return Mock()

    @pytest.fixture
    def handler(self, mock_process_manager):
        """Crea un handler con el process manager mockeado."""
        return RunProcessingPipelineHandler(process_manager=mock_process_manager)

    @pytest.mark.asyncio
    async def test_handle_delegates_to_process_manager(
        self, handler, mock_process_manager
    ):
        """Debería delegar la ejecución al Process Manager."""
        # Arrange
        command = RunProcessingPipelineCommand(limit=50)

        mock_process_result = ProcessingPipelineResult(
            success=True,
            duration_seconds=120.5,
            execution_time="2024-01-01T12:00:00+00:00",
            metrics={"success": 45, "failed": 5, "total": 50},
            language={"success": 48, "failed": 2, "total": 50},
            summary={"success": 40, "failed": 10, "total": 50},
            keywords={"success": 42, "failed": 8, "total": 50},
            quality={"success": 44, "failed": 6, "total": 50},
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        mock_process_manager.execute.assert_called_once_with(limit=50)
        assert isinstance(result, RunProcessingPipelineResult)

    @pytest.mark.asyncio
    async def test_handle_converts_result_correctly(
        self, handler, mock_process_manager
    ):
        """Debería convertir el resultado del Process Manager correctamente."""
        # Arrange
        command = RunProcessingPipelineCommand(limit=100)

        mock_process_result = ProcessingPipelineResult(
            success=True,
            duration_seconds=180.0,
            execution_time="2024-01-01T12:00:00+00:00",
            metrics={"success": 95, "failed": 5, "total": 100},
            language={"success": 98, "failed": 2, "total": 100},
            summary={"success": 90, "failed": 10, "total": 100},
            keywords={"success": 92, "failed": 8, "total": 100},
            quality={"success": 94, "failed": 6, "total": 100},
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.duration_seconds == 180.0
        assert result.execution_time == "2024-01-01T12:00:00+00:00"
        assert result.error is None
        assert result.metrics == {"success": 95, "failed": 5, "total": 100}
        assert result.language == {"success": 98, "failed": 2, "total": 100}
        assert result.summary == {"success": 90, "failed": 10, "total": 100}
        assert result.keywords == {"success": 92, "failed": 8, "total": 100}
        assert result.quality == {"success": 94, "failed": 6, "total": 100}

    @pytest.mark.asyncio
    async def test_handle_with_failed_pipeline(self, handler, mock_process_manager):
        """Debería manejar correctamente un pipeline que falla."""
        # Arrange
        command = RunProcessingPipelineCommand(limit=100)

        mock_process_result = ProcessingPipelineResult(
            success=False,
            duration_seconds=5.0,
            execution_time="2024-01-01T12:00:00+00:00",
            error="AI service unavailable",
            metrics={},
            language={},
            summary={},
            keywords={},
            quality={},
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.error == "AI service unavailable"
        assert result.metrics is None
        assert result.language is None
        assert result.summary is None
        assert result.keywords is None
        assert result.quality is None

    @pytest.mark.asyncio
    async def test_handle_uses_default_parameters(self, handler, mock_process_manager):
        """Debería usar parámetros por defecto del comando."""
        # Arrange
        command = RunProcessingPipelineCommand()  # Usa defaults

        mock_process_result = ProcessingPipelineResult(
            success=True,
            duration_seconds=150.0,
            execution_time="2024-01-01T12:00:00+00:00",
            metrics={"success": 100, "failed": 0, "total": 100},
            language={"success": 100, "failed": 0, "total": 100},
            summary={"success": 100, "failed": 0, "total": 100},
            keywords={"success": 100, "failed": 0, "total": 100},
            quality={"success": 100, "failed": 0, "total": 100},
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        mock_process_manager.execute.assert_called_once_with(limit=100)  # Default
        assert result.success is True
