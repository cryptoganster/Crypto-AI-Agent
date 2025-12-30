"""Tests unitarios para RunFetchPipelineHandler.

Estos tests verifican que el handler delega correctamente al Process Manager
y convierte el resultado apropiadamente.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.app.commands.pipelines.run_fetch_pipeline.command import (
    RunFetchPipelineCommand,
)
from src.app.commands.pipelines.run_fetch_pipeline.handler import (
    RunFetchPipelineHandler,
)
from src.app.commands.pipelines.run_fetch_pipeline.result import (
    RunFetchPipelineResult,
)
from src.app.process_managers.base_process_manager import FetchPipelineResult


class TestRunFetchPipelineHandler:
    """Tests para RunFetchPipelineHandler."""

    @pytest.fixture
    def mock_process_manager(self):
        """Crea un mock del FetchProcessManager."""
        return Mock()

    @pytest.fixture
    def handler(self, mock_process_manager):
        """Crea un handler con el process manager mockeado."""
        return RunFetchPipelineHandler(process_manager=mock_process_manager)

    @pytest.mark.asyncio
    async def test_handle_delegates_to_process_manager(
        self, handler, mock_process_manager
    ):
        """Debería delegar la ejecución al Process Manager."""
        # Arrange
        command = RunFetchPipelineCommand(
            source_ids=["src-1", "src-2"],
            max_concurrent=3,
            priority_mode="high_priority",
        )

        mock_process_result = FetchPipelineResult(
            success=True,
            duration_seconds=30.5,
            execution_time="2024-01-01T12:00:00+00:00",
            sources_processed=2,
            sources_success=2,
            sources_failed=0,
            total_articles_fetched=50,
            fetch_sessions=["session-1", "session-2"],
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        mock_process_manager.execute.assert_called_once_with(
            source_ids=["src-1", "src-2"],
            max_concurrent=3,
            priority_mode="high_priority",
        )
        assert isinstance(result, RunFetchPipelineResult)

    @pytest.mark.asyncio
    async def test_handle_converts_result_correctly(
        self, handler, mock_process_manager
    ):
        """Debería convertir el resultado del Process Manager correctamente."""
        # Arrange
        command = RunFetchPipelineCommand(source_ids=["src-1"])

        mock_process_result = FetchPipelineResult(
            success=True,
            duration_seconds=15.0,
            execution_time="2024-01-01T12:00:00+00:00",
            sources_processed=1,
            sources_success=1,
            sources_failed=0,
            total_articles_fetched=25,
            fetch_sessions=["session-1"],
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.duration_seconds == 15.0
        assert result.execution_time == "2024-01-01T12:00:00+00:00"
        assert result.error is None
        assert result.sources_processed == 1
        assert result.sources_success == 1
        assert result.sources_failed == 0
        assert result.total_articles_fetched == 25
        assert result.fetch_sessions == ["session-1"]

    @pytest.mark.asyncio
    async def test_handle_with_failed_pipeline(self, handler, mock_process_manager):
        """Debería manejar correctamente un pipeline que falla."""
        # Arrange
        command = RunFetchPipelineCommand(source_ids=["src-1"])

        mock_process_result = FetchPipelineResult(
            success=False,
            duration_seconds=5.0,
            execution_time="2024-01-01T12:00:00+00:00",
            error="Network timeout",
            sources_processed=0,
            sources_success=0,
            sources_failed=0,
            total_articles_fetched=0,
            fetch_sessions=[],
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is False
        assert result.error == "Network timeout"
        assert result.sources_processed == 0
        assert result.fetch_sessions is None

    @pytest.mark.asyncio
    async def test_handle_with_partial_failures(self, handler, mock_process_manager):
        """Debería manejar correctamente fallos parciales."""
        # Arrange
        command = RunFetchPipelineCommand(source_ids=["src-1", "src-2", "src-3"])

        mock_process_result = FetchPipelineResult(
            success=True,
            duration_seconds=45.0,
            execution_time="2024-01-01T12:00:00+00:00",
            sources_processed=3,
            sources_success=2,
            sources_failed=1,
            total_articles_fetched=40,
            fetch_sessions=["session-1", "session-2"],
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        assert result.success is True
        assert result.sources_processed == 3
        assert result.sources_success == 2
        assert result.sources_failed == 1
        assert result.total_articles_fetched == 40

    @pytest.mark.asyncio
    async def test_handle_uses_default_parameters(self, handler, mock_process_manager):
        """Debería usar parámetros por defecto del comando."""
        # Arrange
        command = RunFetchPipelineCommand()  # Usa defaults

        mock_process_result = FetchPipelineResult(
            success=True,
            duration_seconds=60.0,
            execution_time="2024-01-01T12:00:00+00:00",
            sources_processed=10,
            sources_success=10,
            sources_failed=0,
            total_articles_fetched=200,
            fetch_sessions=["session-1", "session-2", "session-3"],
        )

        mock_process_manager.execute = AsyncMock(return_value=mock_process_result)

        # Act
        result = await handler.handle(command)

        # Assert
        mock_process_manager.execute.assert_called_once_with(
            source_ids=None,  # Default (todos los activos)
            max_concurrent=5,  # Default
            priority_mode="normal",  # Default
        )
        assert result.success is True
