"""Tests unitarios para BaseProcessManager."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

import pytest

from src.app.process_managers.base_process_manager import (
    BaseProcessManager,
    FetchPipelineResult,
    ProcessingPipelineResult,
    ProcessResult,
    ScrapingPipelineResult,
)
from src.shared.kernel.bus import IMediator
from src.shared.kernel.logger import ILogger


class ConcreteProcessManager(BaseProcessManager):
    """Implementación concreta de BaseProcessManager para testing."""

    async def execute(self) -> ProcessResult:
        """Implementación de ejemplo para testing."""
        return ProcessResult(
            success=True,
            duration_seconds=1.5,
            execution_time="2024-01-01T12:00:00+00:00",
        )


class TestBaseProcessManager:
    """Tests para BaseProcessManager."""

    @pytest.fixture
    def mock_mediator(self) -> Mock:
        """Crea un mock del Mediator."""
        return Mock(spec=IMediator)

    @pytest.fixture
    def mock_logger(self) -> Mock:
        """Crea un mock del Logger."""
        logger = Mock(spec=ILogger)
        # El método bind debe retornar el mismo logger para encadenamiento
        logger.bind.return_value = logger
        return logger

    @pytest.fixture
    def process_manager(
        self, mock_mediator: Mock, mock_logger: Mock
    ) -> ConcreteProcessManager:
        """Crea una instancia de ConcreteProcessManager para testing."""
        return ConcreteProcessManager(mediator=mock_mediator, logger=mock_logger)

    def test_init_binds_logger_with_component_name(
        self, mock_mediator: Mock, mock_logger: Mock
    ):
        """Debería vincular el logger con el nombre del componente."""
        # Act
        manager = ConcreteProcessManager(mediator=mock_mediator, logger=mock_logger)

        # Assert
        mock_logger.bind.assert_called_once_with(component="ConcreteProcessManager")

    def test_log_phase_start_logs_with_phase_name(
        self, process_manager: ConcreteProcessManager, mock_logger: Mock
    ):
        """Debería loggear el inicio de fase con el nombre de la fase."""
        # Act
        process_manager._log_phase_start("scraping")

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Starting phase: scraping" in call_args[0]
        assert call_args[1]["phase"] == "scraping"

    def test_log_phase_start_includes_context(
        self, process_manager: ConcreteProcessManager, mock_logger: Mock
    ):
        """Debería incluir contexto adicional en el log de inicio."""
        # Act
        process_manager._log_phase_start("scraping", limit=100, force_rescrape=True)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[1]["phase"] == "scraping"
        assert call_args[1]["limit"] == 100
        assert call_args[1]["force_rescrape"] is True

    def test_log_phase_complete_logs_with_phase_name(
        self, process_manager: ConcreteProcessManager, mock_logger: Mock
    ):
        """Debería loggear el completado de fase con el nombre de la fase."""
        # Arrange
        stats = {"success": 95, "failed": 5, "total": 100}

        # Act
        process_manager._log_phase_complete("scraping", stats)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Phase complete: scraping" in call_args[0]
        assert call_args[1]["phase"] == "scraping"

    def test_log_phase_complete_includes_stats(
        self, process_manager: ConcreteProcessManager, mock_logger: Mock
    ):
        """Debería incluir estadísticas en el log de completado."""
        # Arrange
        stats = {"success": 95, "failed": 5, "total": 100}

        # Act
        process_manager._log_phase_complete("scraping", stats)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[1]["success"] == 95
        assert call_args[1]["failed"] == 5
        assert call_args[1]["total"] == 100


class TestProcessResult:
    """Tests para ProcessResult dataclass."""

    def test_create_process_result_with_success(self):
        """Debería crear ProcessResult exitoso correctamente."""
        # Act
        result = ProcessResult(
            success=True,
            duration_seconds=2.5,
            execution_time="2024-01-01T12:00:00+00:00",
        )

        # Assert
        assert result.success is True
        assert result.duration_seconds == 2.5
        assert result.execution_time == "2024-01-01T12:00:00+00:00"
        assert result.error is None

    def test_create_process_result_with_error(self):
        """Debería crear ProcessResult con error correctamente."""
        # Act
        result = ProcessResult(
            success=False,
            duration_seconds=1.0,
            execution_time="2024-01-01T12:00:00+00:00",
            error="Database connection failed",
        )

        # Assert
        assert result.success is False
        assert result.error == "Database connection failed"

    def test_process_result_has_all_required_fields(self):
        """Debería tener todos los campos requeridos."""
        # Act
        result = ProcessResult(
            success=True,
            duration_seconds=1.5,
            execution_time="2024-01-01T12:00:00+00:00",
        )

        # Assert
        assert hasattr(result, "success")
        assert hasattr(result, "duration_seconds")
        assert hasattr(result, "execution_time")
        assert hasattr(result, "error")


class TestScrapingPipelineResult:
    """Tests para ScrapingPipelineResult dataclass."""

    def test_create_scraping_pipeline_result(self):
        """Debería crear ScrapingPipelineResult correctamente."""
        # Act
        result = ScrapingPipelineResult(
            success=True,
            duration_seconds=10.5,
            execution_time="2024-01-01T12:00:00+00:00",
            scraping={"success": 95, "failed": 5, "total": 100},
            plaintext={"success": 90, "failed": 10, "total": 100},
            markdown={"success": 88, "failed": 12, "total": 100},
        )

        # Assert
        assert result.success is True
        assert result.scraping["success"] == 95
        assert result.plaintext["success"] == 90
        assert result.markdown["success"] == 88

    def test_scraping_pipeline_result_has_default_empty_dicts(self):
        """Debería tener dicts vacíos por defecto."""
        # Act
        result = ScrapingPipelineResult(
            success=True,
            duration_seconds=1.0,
            execution_time="2024-01-01T12:00:00+00:00",
        )

        # Assert
        assert result.scraping == {}
        assert result.plaintext == {}
        assert result.markdown == {}

    def test_scraping_pipeline_result_inherits_from_process_result(self):
        """Debería heredar de ProcessResult."""
        # Act
        result = ScrapingPipelineResult(
            success=True,
            duration_seconds=1.0,
            execution_time="2024-01-01T12:00:00+00:00",
        )

        # Assert
        assert isinstance(result, ProcessResult)
        assert hasattr(result, "success")
        assert hasattr(result, "duration_seconds")
        assert hasattr(result, "execution_time")
        assert hasattr(result, "error")


class TestProcessingPipelineResult:
    """Tests para ProcessingPipelineResult dataclass."""

    def test_create_processing_pipeline_result(self):
        """Debería crear ProcessingPipelineResult correctamente."""
        # Act
        result = ProcessingPipelineResult(
            success=True,
            duration_seconds=20.0,
            execution_time="2024-01-01T12:00:00+00:00",
            metrics={"success": 100, "failed": 0, "total": 100},
            language={"success": 98, "failed": 2, "total": 100},
            summary={"success": 95, "failed": 5, "total": 100},
            keywords={"success": 97, "failed": 3, "total": 100},
            quality={"success": 99, "failed": 1, "total": 100},
        )

        # Assert
        assert result.success is True
        assert result.metrics["success"] == 100
        assert result.language["success"] == 98
        assert result.summary["success"] == 95
        assert result.keywords["success"] == 97
        assert result.quality["success"] == 99

    def test_processing_pipeline_result_has_default_empty_dicts(self):
        """Debería tener dicts vacíos por defecto."""
        # Act
        result = ProcessingPipelineResult(
            success=True,
            duration_seconds=1.0,
            execution_time="2024-01-01T12:00:00+00:00",
        )

        # Assert
        assert result.metrics == {}
        assert result.language == {}
        assert result.summary == {}
        assert result.keywords == {}
        assert result.quality == {}

    def test_processing_pipeline_result_inherits_from_process_result(self):
        """Debería heredar de ProcessResult."""
        # Act
        result = ProcessingPipelineResult(
            success=True,
            duration_seconds=1.0,
            execution_time="2024-01-01T12:00:00+00:00",
        )

        # Assert
        assert isinstance(result, ProcessResult)


class TestFetchPipelineResult:
    """Tests para FetchPipelineResult dataclass."""

    def test_create_fetch_pipeline_result(self):
        """Debería crear FetchPipelineResult correctamente."""
        # Act
        result = FetchPipelineResult(
            success=True,
            duration_seconds=15.0,
            execution_time="2024-01-01T12:00:00+00:00",
            sources_processed=10,
            sources_success=8,
            sources_failed=2,
            total_articles_fetched=150,
            fetch_sessions=["session-1", "session-2", "session-3"],
        )

        # Assert
        assert result.success is True
        assert result.sources_processed == 10
        assert result.sources_success == 8
        assert result.sources_failed == 2
        assert result.total_articles_fetched == 150
        assert len(result.fetch_sessions) == 3

    def test_fetch_pipeline_result_has_default_values(self):
        """Debería tener valores por defecto."""
        # Act
        result = FetchPipelineResult(
            success=True,
            duration_seconds=1.0,
            execution_time="2024-01-01T12:00:00+00:00",
        )

        # Assert
        assert result.sources_processed == 0
        assert result.sources_success == 0
        assert result.sources_failed == 0
        assert result.total_articles_fetched == 0
        assert result.fetch_sessions == []

    def test_fetch_pipeline_result_inherits_from_process_result(self):
        """Debería heredar de ProcessResult."""
        # Act
        result = FetchPipelineResult(
            success=True,
            duration_seconds=1.0,
            execution_time="2024-01-01T12:00:00+00:00",
        )

        # Assert
        assert isinstance(result, ProcessResult)
