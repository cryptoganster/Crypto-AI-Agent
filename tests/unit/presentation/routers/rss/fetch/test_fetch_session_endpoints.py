"""Tests para endpoints de fetch sessions."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.presentation.routers.rss.fetch.get_fetch_session import get_fetch_session
from src.presentation.routers.rss.fetch.start_fetch_session import start_fetch_session
from src.presentation.schemas.rss.fetch.start_fetch_session_request import (
    StartFetchSessionRequest,
)
from src.scraping.infra.persistence.models import ScrapingModel as FetchSessionModel


class TestStartFetchSessionEndpoint:
    """Tests para endpoint POST /fetch-sessions."""

    @pytest.mark.asyncio
    async def test_start_fetch_session_with_multiple_sources(self):
        """Debería iniciar sesión con múltiples sources correctamente."""
        # Arrange
        request = StartFetchSessionRequest(
            source_ids=["src-1", "src-2", "src-3"],
            max_concurrent_fetches=5,
        )

        mock_result = MagicMock()
        mock_result.session_id = uuid4()
        mock_result.sources_count = 3
        mock_result.started_at = datetime.now(timezone.utc)

        mock_handler = AsyncMock()
        mock_handler.handle.return_value = mock_result

        mock_system = MagicMock()
        mock_system.app.commands.start_fetch_session_handler = mock_handler

        # Act
        response = await start_fetch_session(request, mock_system)

        # Assert
        assert response.status == "running"
        assert response.sources_count == 3
        assert "3 sources" in response.message
        mock_handler.handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_fetch_session_with_validation_limits(self):
        """Debería validar límites de sources y concurrencia."""
        # Arrange
        request = StartFetchSessionRequest(
            source_ids=["src-1"],
            max_concurrent_fetches=10,
            timeout_config={"connect": 5, "read": 30},
        )

        mock_result = MagicMock()
        mock_result.session_id = uuid4()
        mock_result.sources_count = 1
        mock_result.started_at = datetime.now(timezone.utc)

        mock_handler = AsyncMock()
        mock_handler.handle.return_value = mock_result

        mock_system = MagicMock()
        mock_system.app.commands.start_fetch_session_handler = mock_handler

        # Act
        response = await start_fetch_session(request, mock_system)

        # Assert
        assert response.status == "running"
        assert response.sources_count == 1

    @pytest.mark.asyncio
    async def test_start_fetch_session_handles_validation_error(self):
        """Debería manejar errores de validación con 422."""
        # Arrange
        request = StartFetchSessionRequest(
            source_ids=["src-1"],
            max_concurrent_fetches=5,
        )

        mock_handler = AsyncMock()
        mock_handler.handle.side_effect = ValueError("Invalid source ID")

        mock_system = MagicMock()
        mock_system.app.commands.start_fetch_session_handler = mock_handler

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await start_fetch_session(request, mock_system)

        assert exc_info.value.status_code == 422
        assert "Invalid source ID" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_start_fetch_session_handles_general_error(self):
        """Debería manejar errores generales con 400."""
        # Arrange
        request = StartFetchSessionRequest(
            source_ids=["src-1"],
            max_concurrent_fetches=5,
        )

        mock_handler = AsyncMock()
        mock_handler.handle.side_effect = Exception("Database error")

        mock_system = MagicMock()
        mock_system.app.commands.start_fetch_session_handler = mock_handler

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await start_fetch_session(request, mock_system)

        assert exc_info.value.status_code == 400
        assert "Database error" in str(exc_info.value.detail)


class TestGetFetchSessionEndpoint:
    """Tests para endpoint GET /fetch-sessions/{id}."""

    @pytest.mark.asyncio
    async def test_get_fetch_session_returns_complete_detail(self):
        """Debería retornar detalle completo de la sesión."""
        # Arrange
        session_id = uuid4()

        mock_model = FetchSessionModel(
            fetch_session_id=session_id,
            status="running",
            max_concurrent_fetches=5,
            timeout_seconds=30,
            sources_to_fetch=["src-1", "src-2", "src-3"],
            sources_count=3,
            sources_in_progress=["src-2"],
            sources_completed=["src-1"],
            sources_failed=[],
            articles_discovered=50,
            articles_new=40,
            articles_updated=10,
            sources_successful=1,
            sources_failed_count=0,
            total_processing_time_seconds=25.5,
            average_response_time_ms=850.0,
            error_count=0,
            errors_by_type={},
            fetch_errors=[],
            started_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model

        mock_db_session = AsyncMock()
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.__aenter__.return_value = mock_db_session
        mock_db_session.__aexit__.return_value = None

        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value = mock_db_session

        mock_system = MagicMock()
        mock_system.infra.session_manager = mock_session_manager

        # Act
        response = await get_fetch_session(session_id, mock_system)

        # Assert
        assert response.fetch_session_id == str(session_id)
        assert response.status == "running"
        assert response.source_tracking.sources_count == 3
        assert response.article_metrics.articles_discovered == 50
        assert response.source_metrics.sources_successful == 1
        assert response.performance_metrics.total_processing_time_seconds == 25.5
        assert response.error_summary.error_count == 0

    @pytest.mark.asyncio
    async def test_get_fetch_session_includes_metrics(self):
        """Debería incluir todas las métricas calculadas."""
        # Arrange
        session_id = uuid4()

        mock_model = FetchSessionModel(
            fetch_session_id=session_id,
            status="completed",
            max_concurrent_fetches=5,
            timeout_seconds=30,
            sources_to_fetch=["src-1", "src-2"],
            sources_count=2,
            sources_in_progress=[],
            sources_completed=["src-1", "src-2"],
            sources_failed=[],
            articles_discovered=100,
            articles_new=80,
            articles_updated=20,
            sources_successful=2,
            sources_failed_count=0,
            total_processing_time_seconds=60.0,
            average_response_time_ms=750.0,
            error_count=0,
            errors_by_type={},
            fetch_errors=[],
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model

        mock_db_session = AsyncMock()
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.__aenter__.return_value = mock_db_session
        mock_db_session.__aexit__.return_value = None

        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value = mock_db_session

        mock_system = MagicMock()
        mock_system.infra.session_manager = mock_session_manager

        # Act
        response = await get_fetch_session(session_id, mock_system)

        # Assert
        assert response.progress_percentage == 100.0
        assert response.source_metrics.success_rate == 100.0
        assert response.performance_metrics.throughput_articles_per_minute > 0

    @pytest.mark.asyncio
    async def test_get_fetch_session_includes_errors(self):
        """Debería incluir resumen de errores cuando existen."""
        # Arrange
        session_id = uuid4()

        mock_model = FetchSessionModel(
            fetch_session_id=session_id,
            status="failed",
            max_concurrent_fetches=5,
            timeout_seconds=30,
            sources_to_fetch=["src-1", "src-2"],
            sources_count=2,
            sources_in_progress=[],
            sources_completed=[],
            sources_failed=["src-1", "src-2"],
            articles_discovered=0,
            articles_new=0,
            articles_updated=0,
            sources_successful=0,
            sources_failed_count=2,
            total_processing_time_seconds=0.0,
            average_response_time_ms=0.0,
            error_count=2,
            errors_by_type={"timeout": 1, "http_error": 1},
            last_error_message="Connection timeout",
            fetch_errors=[
                {
                    "source_id": "src-1",
                    "error_type": "timeout",
                    "error_message": "Connection timeout",
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model

        mock_db_session = AsyncMock()
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.__aenter__.return_value = mock_db_session
        mock_db_session.__aexit__.return_value = None

        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value = mock_db_session

        mock_system = MagicMock()
        mock_system.infra.session_manager = mock_session_manager

        # Act
        response = await get_fetch_session(session_id, mock_system)

        # Assert
        assert response.error_summary.error_count == 2
        assert response.error_summary.errors_by_type["timeout"] == 1
        assert response.error_summary.errors_by_type["http_error"] == 1
        assert response.error_summary.last_error_message == "Connection timeout"

    @pytest.mark.asyncio
    async def test_get_fetch_session_returns_404_when_not_found(self):
        """Debería retornar 404 cuando la sesión no existe."""
        # Arrange
        session_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db_session = AsyncMock()
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.__aenter__.return_value = mock_db_session
        mock_db_session.__aexit__.return_value = None

        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value = mock_db_session

        mock_system = MagicMock()
        mock_system.infra.session_manager = mock_session_manager

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_fetch_session(session_id, mock_system)

        assert exc_info.value.status_code == 404
        assert str(session_id) in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_fetch_session_handles_database_error(self):
        """Debería manejar errores de base de datos con 500."""
        # Arrange
        session_id = uuid4()

        mock_db_session = AsyncMock()
        mock_db_session.execute.side_effect = Exception("Database connection error")
        mock_db_session.__aenter__.return_value = mock_db_session
        mock_db_session.__aexit__.return_value = None

        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value = mock_db_session

        mock_system = MagicMock()
        mock_system.infra.session_manager = mock_session_manager

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_fetch_session(session_id, mock_system)

        assert exc_info.value.status_code == 500
        assert "Error retrieving fetch session" in str(exc_info.value.detail)
