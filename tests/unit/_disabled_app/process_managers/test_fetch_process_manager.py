"""Tests unitarios para FetchProcessManager."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.app.process_managers.base_process_manager import FetchPipelineResult
from src.app.process_managers.fetch_process_manager import FetchProcessManager
from src.rss.feed.domain.interfaces.repositories.source_read_repository import (
    IRssFeedReadRepository,
)
from src.scraping.app.commands import ScrapeMultiSourceCommand
from src.shared.kernel.bus import IMediator
from src.shared.kernel.logger import ILogger


class TestFetchProcessManager:
    """Tests para FetchProcessManager."""

    @pytest.fixture
    def mock_mediator(self) -> Mock:
        """Crea un mock del Mediator."""
        mediator = Mock(spec=IMediator)
        mediator.send = AsyncMock()
        return mediator

    @pytest.fixture
    def mock_source_read_repository(self) -> Mock:
        """Crea un mock del Source Read Repository."""
        repo = Mock(spec=IRssFeedReadRepository)
        repo.find_active = AsyncMock(return_value=[])
        repo.find_all = AsyncMock(return_value=[])
        repo.find_by_id = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def mock_logger(self) -> Mock:
        """Crea un mock del Logger."""
        logger = Mock(spec=ILogger)
        logger.bind.return_value = logger
        return logger

    @pytest.fixture
    def process_manager(
        self,
        mock_mediator: Mock,
        mock_source_read_repository: Mock,
        mock_logger: Mock,
    ) -> FetchProcessManager:
        """Crea una instancia de FetchProcessManager para testing."""
        return FetchProcessManager(
            mediator=mock_mediator,
            source_read_repository=mock_source_read_repository,
            logger=mock_logger,
        )

    def create_test_source(self, source_id: str = None) -> Mock:
        """Crea un source de prueba (mock de Source aggregate)."""
        from uuid import UUID

        if source_id is None:
            source_id = str(uuid4())

        # Crear mock con __str__ para que str(source.id) funcione
        source = Mock()
        mock_id = Mock()
        mock_id.__str__ = Mock(return_value=source_id)
        source.id = mock_id

        mock_name = Mock()
        mock_name.__str__ = Mock(return_value="Test RssFeed")
        source.name = mock_name

        mock_url = Mock()
        mock_url.__str__ = Mock(return_value="https://example.com/feed.xml")
        source.url = mock_url

        mock_status = Mock()
        mock_status.__str__ = Mock(return_value="active")
        source.status = mock_status

        source.is_active = True
        return source

    @pytest.mark.asyncio
    async def test_execute_with_no_sources_returns_empty_stats(
        self,
        process_manager: FetchProcessManager,
        mock_source_read_repository: Mock,
    ):
        """Debería retornar estadísticas vacías cuando no hay sources."""
        # Arrange
        mock_source_read_repository.find_active.return_value = []

        # Act
        result = await process_manager.execute()

        # Assert
        assert isinstance(result, FetchPipelineResult)
        assert result.success is True
        assert result.sources_processed == 0
        assert result.sources_success == 0
        assert result.sources_failed == 0
        assert result.total_articles_fetched == 0
        assert result.fetch_sessions == []
        assert result.error is None

    @pytest.mark.asyncio
    async def test_execute_with_sources_sends_commands_via_mediator(
        self,
        process_manager: FetchProcessManager,
        mock_mediator: Mock,
        mock_source_read_repository: Mock,
    ):
        """Debería enviar comandos vía Mediator para cada source."""
        # Arrange
        source1 = self.create_test_source("src-1")
        source2 = self.create_test_source("src-2")
        mock_source_read_repository.find_active.return_value = [source1, source2]

        # Mock successful results
        mock_result = Mock()
        mock_result.success = True
        mock_result.scraping_id = str(uuid4())
        mock_result.articles_fetched = 10
        mock_mediator.send.return_value = mock_result

        # Act
        result = await process_manager.execute(max_concurrent=5)

        # Assert
        assert result.success is True
        assert result.sources_processed == 2
        assert result.sources_success == 2
        assert result.sources_failed == 0

        # Verificar que se enviaron los comandos correctos
        assert mock_mediator.send.call_count == 2

        # Verificar que los comandos son ScrapeMultiSourceCommand
        for call in mock_mediator.send.call_args_list:
            command = call[0][0]
            assert isinstance(command, ScrapeMultiSourceCommand)

    @pytest.mark.asyncio
    async def test_execute_handles_partial_failures(
        self,
        process_manager: FetchProcessManager,
        mock_mediator: Mock,
        mock_source_read_repository: Mock,
    ):
        """Debería manejar fallos parciales sin detener el procesamiento."""
        # Arrange
        source1 = self.create_test_source("src-1")
        source2 = self.create_test_source("src-2")
        source3 = self.create_test_source("src-3")
        mock_source_read_repository.find_active.return_value = [
            source1,
            source2,
            source3,
        ]

        # Mock: primer source exitoso, segundo falla, tercero exitoso
        success_result = Mock()
        success_result.success = True
        success_result.scraping_id = str(uuid4())
        success_result.articles_fetched = 5

        failed_result = Mock()
        failed_result.success = False
        failed_result.error = "Connection timeout"

        mock_mediator.send.side_effect = [
            success_result,  # src-1 exitoso
            failed_result,  # src-2 falla
            success_result,  # src-3 exitoso
        ]

        # Act
        result = await process_manager.execute()

        # Assert
        assert result.success is True
        assert result.sources_processed == 3
        assert result.sources_success == 2
        assert result.sources_failed == 1
        assert result.error is None

    @pytest.mark.asyncio
    async def test_execute_handles_exceptions_in_commands(
        self,
        process_manager: FetchProcessManager,
        mock_mediator: Mock,
        mock_source_read_repository: Mock,
    ):
        """Debería manejar excepciones en comandos individuales."""
        # Arrange
        source1 = self.create_test_source("src-1")
        source2 = self.create_test_source("src-2")
        mock_source_read_repository.find_active.return_value = [source1, source2]

        # Mock: primer source lanza excepción, segundo exitoso
        success_result = Mock()
        success_result.success = True
        success_result.scraping_id = str(uuid4())
        success_result.articles_fetched = 8

        mock_mediator.send.side_effect = [
            Exception("Network error"),  # src-1 lanza excepción
            success_result,  # src-2 exitoso
        ]

        # Act
        result = await process_manager.execute()

        # Assert
        assert result.success is True
        assert result.sources_processed == 2
        assert result.sources_success == 1
        assert result.sources_failed == 1

    @pytest.mark.asyncio
    async def test_execute_with_specific_source_ids(
        self,
        process_manager: FetchProcessManager,
        mock_mediator: Mock,
        mock_source_read_repository: Mock,
    ):
        """Debería procesar solo los source_ids especificados."""
        # Arrange
        source1 = self.create_test_source("00000000-0000-0000-0000-000000000001")
        source3 = self.create_test_source("00000000-0000-0000-0000-000000000003")

        # find_by_id retorna sources específicos
        async def mock_find_by_id(source_id):
            sid = str(source_id)
            if sid == "00000000-0000-0000-0000-000000000001":
                return source1
            elif sid == "00000000-0000-0000-0000-000000000003":
                return source3
            return None

        mock_source_read_repository.find_by_id = AsyncMock(side_effect=mock_find_by_id)

        # Mock successful result
        mock_result = Mock()
        mock_result.success = True
        mock_result.scraping_id = str(uuid4())
        mock_result.articles_fetched = 5
        mock_mediator.send.return_value = mock_result

        # Act - Solo procesar src-1 y src-3
        result = await process_manager.execute(
            source_ids=[
                "00000000-0000-0000-0000-000000000001",
                "00000000-0000-0000-0000-000000000003",
            ]
        )

        # Assert
        assert result.success is True
        assert result.sources_processed == 2  # Solo 2 sources
        assert result.sources_success == 2
        assert result.sources_failed == 0

        # Verificar que se enviaron comandos
        assert mock_mediator.send.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_uses_repository_correctly(
        self,
        process_manager: FetchProcessManager,
        mock_source_read_repository: Mock,
    ):
        """Debería usar el repository correctamente."""
        # Arrange
        source1 = self.create_test_source()
        mock_source_read_repository.find_active.return_value = [source1]

        # Act
        await process_manager.execute()

        # Assert
        mock_source_read_repository.find_active.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_priority_mode(
        self,
        process_manager: FetchProcessManager,
        mock_mediator: Mock,
        mock_source_read_repository: Mock,
    ):
        """Debería pasar el priority_mode al comando como triggered_by."""
        # Arrange
        source1 = self.create_test_source("src-1")
        mock_source_read_repository.find_active.return_value = [source1]

        mock_result = Mock()
        mock_result.success = True
        mock_result.scraping_id = str(uuid4())
        mock_result.articles_fetched = 3
        mock_mediator.send.return_value = mock_result

        # Act
        await process_manager.execute(priority_mode="high_priority")

        # Assert
        command = mock_mediator.send.call_args[0][0]
        assert command.triggered_by == "high_priority"

    @pytest.mark.asyncio
    async def test_execute_returns_structured_result(
        self,
        process_manager: FetchProcessManager,
        mock_mediator: Mock,
        mock_source_read_repository: Mock,
    ):
        """Debería retornar un resultado estructurado con todos los campos."""
        # Arrange
        source1 = self.create_test_source("src-1")
        mock_source_read_repository.find_active.return_value = [source1]

        mock_result = Mock()
        mock_result.success = True
        mock_result.scraping_id = "session-123"
        mock_result.articles_fetched = 15
        mock_mediator.send.return_value = mock_result

        # Act
        result = await process_manager.execute()

        # Assert
        assert isinstance(result, FetchPipelineResult)
        assert hasattr(result, "success")
        assert hasattr(result, "duration_seconds")
        assert hasattr(result, "execution_time")
        assert hasattr(result, "sources_processed")
        assert hasattr(result, "sources_success")
        assert hasattr(result, "sources_failed")
        assert hasattr(result, "total_articles_fetched")
        assert hasattr(result, "fetch_sessions")
        assert hasattr(result, "error")

        assert result.success is True
        assert result.sources_processed == 1
        assert result.sources_success == 1
        assert result.sources_failed == 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_execute_handles_critical_failure(
        self,
        process_manager: FetchProcessManager,
        mock_source_read_repository: Mock,
    ):
        """Debería manejar fallos críticos del repository."""
        # Arrange
        mock_source_read_repository.find_active.side_effect = Exception(
            "Database connection failed"
        )

        # Act
        result = await process_manager.execute()

        # Assert
        assert result.success is False
        assert result.error == "Database connection failed"
        assert result.sources_processed == 0
        assert result.sources_success == 0
        assert result.sources_failed == 0

    @pytest.mark.asyncio
    async def test_statistics_accuracy(
        self,
        process_manager: FetchProcessManager,
        mock_mediator: Mock,
        mock_source_read_repository: Mock,
    ):
        """Debería acumular estadísticas correctamente: total = success + failed."""
        # Arrange
        sources = [self.create_test_source(f"src-{i}") for i in range(5)]
        mock_source_read_repository.find_active.return_value = sources

        # Mock: 3 exitosos, 2 fallidos
        success_result = Mock()
        success_result.success = True
        success_result.scraping_id = str(uuid4())
        success_result.articles_fetched = 10

        failed_result = Mock()
        failed_result.success = False
        failed_result.error = "Error"

        mock_mediator.send.side_effect = [
            success_result,  # 1
            success_result,  # 2
            failed_result,  # 3
            success_result,  # 4
            failed_result,  # 5
        ]

        # Act
        result = await process_manager.execute()

        # Assert
        assert result.sources_processed == 5
        assert result.sources_success == 3
        assert result.sources_failed == 2
        # Verificar invariante: total = success + failed
        assert (
            result.sources_processed == result.sources_success + result.sources_failed
        )
