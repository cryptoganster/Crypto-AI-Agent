"""Tests para verificar que FetchProcessManager maneja correctamente source_ids None."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.app.process_managers.fetch_process_manager import FetchProcessManager


class TestFetchProcessManagerNoneHandling:
    """Tests para manejo de None en source_ids."""

    @pytest.fixture
    def mock_mediator(self):
        """Crea mock de mediator."""
        return AsyncMock()

    @pytest.fixture
    def mock_query_adapter(self):
        """Crea mock de query adapter."""
        return AsyncMock()

    @pytest.fixture
    def mock_logger(self):
        """Crea mock de logger."""
        logger = Mock()
        logger.bind.return_value = logger
        logger.debug = Mock()
        logger.info = Mock()
        logger.warning = Mock()
        logger.error = Mock()
        return logger

    @pytest.fixture
    def process_manager(self, mock_mediator, mock_query_adapter, mock_logger):
        """Crea process manager con dependencias mockeadas."""
        return FetchProcessManager(
            mediator=mock_mediator,
            query_adapter=mock_query_adapter,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_execute_fetch_phase_filters_sources_without_id(
        self, process_manager, mock_mediator, mock_logger
    ):
        """Debería filtrar sources sin ID válido y continuar con las válidas."""
        # Arrange
        sources = [
            {"id": None, "name": "Invalid Source 1"},  # Sin ID
            {"source_id": str(uuid4()), "name": "Valid Source"},  # ID válido
            {"name": "Invalid Source 2"},  # Sin ID ni source_id
        ]

        # Mock mediator response
        mock_result = Mock()
        mock_result.success = True
        mock_result.articles_fetched = 5
        mock_result.session_id = str(uuid4())
        mock_mediator.send.return_value = mock_result

        # Act
        stats = await process_manager._execute_fetch_phase(
            sources=sources,
            max_concurrent=5,
            priority_mode="normal",
        )

        # Assert
        # Debería haber procesado solo 1 source válida
        assert mock_mediator.send.call_count == 1

        # Debería haber loggeado warnings para las 2 sources inválidas
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if "RssFeed sin ID válido" in str(call)
        ]
        assert len(warning_calls) == 2

        # Stats deberían reflejar 1 éxito y 2 fallos
        assert stats["sources_success"] == 1
        assert stats["sources_failed"] == 2

    @pytest.mark.asyncio
    async def test_execute_fetch_phase_handles_all_invalid_sources(
        self, process_manager, mock_mediator, mock_logger
    ):
        """Debería manejar correctamente cuando todas las sources son inválidas."""
        # Arrange
        sources = [
            {"id": None, "name": "Invalid RssFeed 1"},
            {"name": "Invalid RssFeed 2"},
            {},  # Source vacía
        ]

        # Act
        stats = await process_manager._execute_fetch_phase(
            sources=sources,
            max_concurrent=5,
            priority_mode="normal",
        )

        # Assert
        # No debería haber llamado al mediator
        assert mock_mediator.send.call_count == 0

        # Todas deberían ser fallos
        assert stats["sources_success"] == 0
        assert stats["sources_failed"] == 3

    @pytest.mark.asyncio
    async def test_execute_fetch_phase_uses_source_id_fallback(
        self, process_manager, mock_mediator, mock_logger
    ):
        """Debería usar 'source_id' como fallback cuando 'id' no existe."""
        # Arrange
        valid_id = str(uuid4())
        sources = [
            {"source_id": valid_id, "name": "Source with source_id"},  # Usa source_id
        ]

        # Mock mediator response
        mock_result = Mock()
        mock_result.success = True
        mock_result.articles_fetched = 3
        mock_result.session_id = str(uuid4())
        mock_mediator.send.return_value = mock_result

        # Act
        stats = await process_manager._execute_fetch_phase(
            sources=sources,
            max_concurrent=5,
            priority_mode="normal",
        )

        # Assert
        assert mock_mediator.send.call_count == 1
        assert stats["sources_success"] == 1
        assert stats["sources_failed"] == 0

        # Verificar que se llamó con el source_id correcto
        call_args = mock_mediator.send.call_args
        command = call_args[0][0]
        assert valid_id in command.source_ids
