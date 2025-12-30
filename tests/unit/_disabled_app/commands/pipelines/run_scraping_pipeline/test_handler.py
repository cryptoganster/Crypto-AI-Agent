"""Tests unitarios para RunScrapingPipelineHandler.

Estos tests verifican que el handler delega correctamente al Process Manager
y convierte el resultado apropiadamente.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from src.app.commands.pipelines.run_scraping_pipeline.command import (
    RunScrapingPipelineCommand,
)
from src.app.commands.pipelines.run_scraping_pipeline.handler import (
    RunScrapingPipelineHandler,
)
from src.app.commands.pipelines.run_scraping_pipeline.result import (
    RunScrapingPipelineResult,
)
from src.app.process_managers.base_process_manager import ScrapingPipelineResult


class TestRunScrapingPipelineHandler:
    """Tests para RunScrapingPipelineHandler."""

    @pytest.fixture
    def mock_process_manager(self):
        """Crea un mock del ScrapingProcessManager."""
        return Mock()

    @pytest.fixture
    def handler(self, mock_process_manager):
        """Crea un handler con el process manager mockeado."""
        return RunScrapingPipelineHandler(process_manager=mock_process_manager)

    @pytest.mark.asyncio
    async def test_handle_delegates_to_process_manager(
        self, handler, mock_process_manager
    ):
        """Debería delegar la ejecución al Process Manager."""
        # Arrange
        command = RunScrapingPipelineCommand(limit=50, force_rescrape=True)

        mock_process_result = ScrapingPipelineResult(
            success=True,
            duration_seconds=45.2,
            execution_time="2024-01-01T12:00:00+00:00",
            scraping={"success": 45, "failed": 5, "total": 50},
            plaintext={"success": 40, "failed": 10, "total": 50},
            markdown={"success": 38, "failed": 12, "total": 50},
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        mock_process_manager.execute.assert_called_once_with(
            limit=50, force_rescrape=True
        )
        assert isinstance(result, RunScrapingPipelineResult)

    @pytest.mark.asyncio
    async def test_handle_converts_result_correctly(
        self, handler, mock_process_manager
    ):
        """Debería convertir el resultado del Process Manager correctamente."""
        # Arrange
        command = RunScrapingPipelineCommand(limit=100)

        mock_process_result = ScrapingPipelineResult(
            success=True,
            duration_seconds=60.5,
            execution_time="2024-01-01T12:00:00+00:00",
            scraping={"success": 95, "failed": 5, "total": 100},
            plaintext={"success": 90, "failed": 10, "total": 100},
            markdown={"success": 88, "failed": 12, "total": 100},
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.duration_seconds == 60.5
        assert result.execution_time == "2024-01-01T12:00:00+00:00"
        assert result.error is None
        assert result.scraping == {"success": 95, "failed": 5, "total": 100}
        assert result.plaintext == {"success": 90, "failed": 10, "total": 100}
        assert result.markdown == {"success": 88, "failed": 12, "total": 100}

    @pytest.mark.asyncio
    async def test_handle_with_failed_pipeline(self, handler, mock_process_manager):
        """Debería manejar correctamente un pipeline que falla."""
        # Arrange
        command = RunScrapingPipelineCommand(limit=100)

        mock_process_result = ScrapingPipelineResult(
            success=False,
            duration_seconds=10.0,
            execution_time="2024-01-01T12:00:00+00:00",
            error="Database connection failed",
            scraping={},
            plaintext={},
            markdown={},
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.error == "Database connection failed"
        assert result.scraping is None
        assert result.plaintext is None
        assert result.markdown is None

    @pytest.mark.asyncio
    async def test_handle_uses_default_parameters(self, handler, mock_process_manager):
        """Debería usar parámetros por defecto del comando."""
        # Arrange
        command = RunScrapingPipelineCommand()  # Usa defaults

        mock_process_result = ScrapingPipelineResult(
            success=True,
            duration_seconds=30.0,
            execution_time="2024-01-01T12:00:00+00:00",
            scraping={"success": 100, "failed": 0, "total": 100},
            plaintext={"success": 100, "failed": 0, "total": 100},
            markdown={"success": 100, "failed": 0, "total": 100},
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        mock_process_manager.execute.assert_called_once_with(
            limit=100,  # Default
            force_rescrape=False,  # Default
        )
        assert result.success is True
