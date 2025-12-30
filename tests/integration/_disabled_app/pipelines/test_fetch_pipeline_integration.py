"""Integration tests para el pipeline de fetch RSS completo.

Este módulo verifica que el pipeline de fetch se integra correctamente
con todos los componentes reales: Mediator, handlers, query adapters, etc.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.app.commands.pipelines.run_fetch_pipeline.command import (
    RunFetchPipelineCommand,
)
from src.rss.article.container import RssArticleContainer
from src.scraping.container import ScrapingContainer
from src.shared.config.app_config import AppConfig
from src.shared.container import SharedContainer


@pytest.mark.integration
class TestFetchPipelineIntegration:
    """Tests de integración para el pipeline de fetch RSS."""

    @pytest.fixture
    def config(self):
        """Crea configuración de test."""
        return AppConfig()

    @pytest.fixture
    def infra(self, config):
        """Crea SharedContainer."""
        return SharedContainer(config)

    @pytest.fixture
    def article_container(self, infra):
        """Crea RssArticleContainer con handlers registrados."""
        # RssArticleContainer ya no necesita DomainServicesContainer
        # Los servicios de dominio están en los bounded contexts
        container = RssArticleContainer(infra)
        return container

    @pytest.fixture
    def scraping_container(self, infra, article_container):
        """Crea ScrapingContainer (antes FetchingContainer)."""
        from src.rss.feed.container import RssFeedContainer

        source_container = RssFeedContainer(infra)
        container = ScrapingContainer(infra, article_container, source_container)
        return container

    @pytest.mark.asyncio
    async def test_pipeline_se_inicializa_con_dependencias_reales(
        self, scraping_container
    ):
        """Debería inicializar el pipeline con todas las dependencias reales."""
        # Arrange - Register handlers
        scraping_container.register_handlers()

        # Assert - Verificar que el handler está registrado
        from src.app.commands.pipelines.run_fetch_pipeline.command import (
            RunFetchPipelineCommand,
        )

        assert (
            RunFetchPipelineCommand
            in fetching_container.infra.mediator._handler_registry
        )

        # Verificar que el handler tiene el process manager
        handler = fetching_container.get_run_fetch_pipeline_handler()
        assert handler is not None
        assert handler._process_manager is not None

    @pytest.mark.asyncio
    async def test_start_fetch_session_command_esta_registrado(
        self, fetching_container
    ):
        """Debería tener ScrapeMultiSourceCommand registrado en el Mediator."""
        # Arrange - Register handlers
        fetching_container.register_pipeline_handlers()

        # Assert
        from src.scraping.app.commands import ScrapeMultiSourceCommand

        assert (
            ScrapeMultiSourceCommand
            in fetching_container.infra.mediator._handler_registry
        )

        handler = fetching_container.infra.mediator._handler_registry[
            ScrapeMultiSourceCommand
        ]
        assert handler is not None

    @pytest.mark.asyncio
    async def test_execute_pipeline_sin_sources_completa_exitosamente(
        self, fetching_container
    ):
        """Debería ejecutar el pipeline correctamente cuando no hay sources."""
        # Arrange - Register handlers
        fetching_container.register_pipeline_handlers()

        # Mock query adapter para retornar lista vacía
        process_manager = fetching_container.get_fetch_process_manager()
        process_manager._query_adapter.get_active = AsyncMock(return_value=[])

        command = RunFetchPipelineCommand(
            source_ids=None,
            max_concurrent=5,
            priority_mode="normal",
        )

        # Act
        result = await fetching_container.infra.mediator.send(command)

        # Assert
        assert result is not None
        assert result.success is True
        assert result.sources_processed == 0
        assert result.sources_success == 0
        assert result.sources_failed == 0
        assert result.total_articles_fetched == 0
        assert result.duration_seconds >= 0
        assert result.execution_time is not None

    @pytest.mark.asyncio
    async def test_execute_pipeline_con_source_usa_start_fetch_session_command(
        self, fetching_container, infra
    ):
        """Debería ejecutar StartFetchSessionCommand vía Mediator para cada source."""
        # Arrange - Register handlers
        fetching_container.register_pipeline_handlers()

        # Crear source mock
        mock_source = {
            "id": str(uuid4()),
            "name": "Test RssFeed",
            "url": "https://example.com/feed.xml",
            "is_active": True,
        }

        # Mock query adapter para retornar el source
        process_manager = fetching_container.get_fetch_process_manager()
        process_manager._query_adapter.get_active = AsyncMock(
            return_value=[mock_source]
        )

        # Mock el handler de ScrapeMultiSourceCommand para evitar fetch real
        from src.scraping.app.commands import ScrapeMultiSourceCommand

        mock_fetch_result = Mock()
        mock_fetch_result.success = True
        mock_fetch_result.scraping_id = str(uuid4())
        mock_fetch_result.articles_fetched = 5

        original_handler = infra.mediator._handler_registry.get(
            ScrapeMultiSourceCommand
        )
        mock_handler = AsyncMock()
        mock_handler.handle = AsyncMock(return_value=mock_fetch_result)
        infra.mediator._handler_registry[ScrapeMultiSourceCommand] = mock_handler

        try:
            # Act
            command = RunFetchPipelineCommand(
                source_ids=None,
                max_concurrent=5,
                priority_mode="normal",
            )
            result = await infra.mediator.send(command)

            # Assert - Verificar resultado del pipeline
            assert result.success is True
            assert result.sources_processed == 1
            assert result.sources_success == 1
            assert result.sources_failed == 0
            assert result.total_articles_fetched == 5
            assert len(result.fetch_sessions) == 1

            # Verificar que se llamó al handler de ScrapeMultiSourceCommand
            mock_handler.handle.assert_called_once()
            call_args = mock_handler.handle.call_args[0][0]
            assert isinstance(call_args, ScrapeMultiSourceCommand)
            assert call_args.source_ids == [mock_source["id"]]
            assert call_args.max_concurrent == 5
            assert call_args.priority_mode == "normal"

        finally:
            # Restaurar handler original
            if original_handler:
                infra.mediator._handler_registry[ScrapeMultiSourceCommand] = (
                    original_handler
                )

    @pytest.mark.asyncio
    async def test_execute_pipeline_con_multiples_sources(
        self, fetching_container, infra
    ):
        """Debería procesar múltiples sources correctamente."""
        # Arrange - Register handlers
        fetching_container.register_pipeline_handlers()

        # Crear múltiples sources mock
        mock_sources = [
            {
                "id": str(uuid4()),
                "name": f"Test RssFeed {i}",
                "url": f"https://example{i}.com/feed.xml",
                "is_active": True,
            }
            for i in range(3)
        ]

        # Mock query adapter
        process_manager = fetching_container.get_fetch_process_manager()
        process_manager._query_adapter.get_active = AsyncMock(return_value=mock_sources)

        # Mock handler de ScrapeMultiSourceCommand
        from src.scraping.app.commands import ScrapeMultiSourceCommand

        call_count = 0

        async def mock_handle(command):
            nonlocal call_count
            call_count += 1
            result = Mock()
            result.success = True
            result.scraping_id = str(uuid4())
            result.articles_fetched = call_count * 2  # Diferentes cantidades
            return result

        original_handler = infra.mediator._handler_registry.get(
            ScrapeMultiSourceCommand
        )
        mock_handler = AsyncMock()
        mock_handler.handle = mock_handle
        infra.mediator._handler_registry[ScrapeMultiSourceCommand] = mock_handler

        try:
            # Act
            command = RunFetchPipelineCommand()
            result = await infra.mediator.send(command)

            # Assert
            assert result.success is True
            assert result.sources_processed == 3
            assert result.sources_success == 3
            assert result.sources_failed == 0
            assert result.total_articles_fetched == 2 + 4 + 6  # 12 total
            assert len(result.fetch_sessions) == 3

        finally:
            if original_handler:
                infra.mediator._handler_registry[ScrapeMultiSourceCommand] = (
                    original_handler
                )

    @pytest.mark.asyncio
    async def test_execute_pipeline_maneja_errores_parciales(
        self, fetching_container, infra
    ):
        """Debería manejar errores parciales sin detener el pipeline."""
        # Arrange - Register handlers
        fetching_container.register_pipeline_handlers()

        # Crear múltiples sources
        mock_sources = [
            {"id": str(uuid4()), "name": f"RssFeed {i}", "is_active": True}
            for i in range(3)
        ]

        process_manager = fetching_container.get_fetch_process_manager()
        process_manager._query_adapter.get_active = AsyncMock(return_value=mock_sources)

        # Mock handler que falla para el segundo source
        from src.scraping.app.commands import ScrapeMultiSourceCommand

        call_count = 0

        async def mock_handle(command):
            nonlocal call_count
            call_count += 1
            result = Mock()
            result.success = call_count != 2  # Falla en el segundo
            result.scraping_id = str(uuid4()) if result.success else None
            result.articles_fetched = 5 if result.success else 0
            result.error = "Scraping failed" if not result.success else None
            return result

        original_handler = infra.mediator._handler_registry.get(
            ScrapeMultiSourceCommand
        )
        mock_handler = AsyncMock()
        mock_handler.handle = mock_handle
        infra.mediator._handler_registry[ScrapeMultiSourceCommand] = mock_handler

        try:
            # Act
            command = RunFetchPipelineCommand()
            result = await infra.mediator.send(command)

            # Assert - Pipeline completa a pesar del error
            assert result.success is True
            assert result.sources_processed == 3
            assert result.sources_success == 2  # 2 exitosos
            assert result.sources_failed == 1  # 1 fallido
            assert result.total_articles_fetched == 10  # 5 + 0 + 5

        finally:
            if original_handler:
                infra.mediator._handler_registry[ScrapeMultiSourceCommand] = (
                    original_handler
                )

    @pytest.mark.asyncio
    async def test_execute_pipeline_con_source_ids_especificos(
        self, fetching_container, infra
    ):
        """Debería filtrar sources por IDs cuando se especifican."""
        # Arrange - Register handlers
        fetching_container.register_pipeline_handlers()

        # Crear múltiples sources
        source_id_1 = str(uuid4())
        source_id_2 = str(uuid4())
        source_id_3 = str(uuid4())

        all_sources = [
            {"id": source_id_1, "name": "RssFeed 1", "is_active": True},
            {"id": source_id_2, "name": "RssFeed 2", "is_active": True},
            {"id": source_id_3, "name": "RssFeed 3", "is_active": True},
        ]

        process_manager = fetching_container.get_fetch_process_manager()
        process_manager._query_adapter.get_active = AsyncMock(return_value=all_sources)

        # Mock handler
        from src.scraping.app.commands import ScrapeMultiSourceCommand

        mock_result = Mock()
        mock_result.success = True
        mock_result.scraping_id = str(uuid4())
        mock_result.articles_fetched = 3

        original_handler = infra.mediator._handler_registry.get(
            ScrapeMultiSourceCommand
        )
        mock_handler = AsyncMock()
        mock_handler.handle = AsyncMock(return_value=mock_result)
        infra.mediator._handler_registry[ScrapeMultiSourceCommand] = mock_handler

        try:
            # Act - Solo procesar source_id_1 y source_id_2
            command = RunFetchPipelineCommand(source_ids=[source_id_1, source_id_2])
            result = await infra.mediator.send(command)

            # Assert - Solo 2 sources procesados
            assert result.success is True
            assert result.sources_processed == 2
            assert result.sources_success == 2
            assert mock_handler.handle.call_count == 2

        finally:
            if original_handler:
                infra.mediator._handler_registry[ScrapeMultiSourceCommand] = (
                    original_handler
                )

    @pytest.mark.asyncio
    async def test_execute_pipeline_retorna_resultado_estructurado(
        self, fetching_container
    ):
        """Debería retornar resultado estructurado con todos los campos requeridos."""
        # Arrange - Register handlers
        fetching_container.register_pipeline_handlers()

        process_manager = fetching_container.get_fetch_process_manager()
        process_manager._query_adapter.get_active = AsyncMock(return_value=[])

        command = RunFetchPipelineCommand()

        # Act
        result = await fetching_container.infra.mediator.send(command)

        # Assert - Verificar estructura del resultado
        assert hasattr(result, "success")
        assert hasattr(result, "duration_seconds")
        assert hasattr(result, "execution_time")
        assert hasattr(result, "error")
        assert hasattr(result, "sources_processed")
        assert hasattr(result, "sources_success")
        assert hasattr(result, "sources_failed")
        assert hasattr(result, "total_articles_fetched")
        assert hasattr(result, "fetch_sessions")

        # Verificar tipos
        assert isinstance(result.success, bool)
        assert isinstance(result.duration_seconds, float)
        assert isinstance(result.execution_time, str)
        assert isinstance(result.sources_processed, int)
        assert isinstance(result.sources_success, int)
        assert isinstance(result.sources_failed, int)
        assert isinstance(result.total_articles_fetched, int)

    @pytest.mark.asyncio
    async def test_execute_pipeline_con_parametros_personalizados(
        self, fetching_container, infra
    ):
        """Debería pasar parámetros personalizados al comando de fetch."""
        # Arrange - Register handlers
        fetching_container.register_pipeline_handlers()

        mock_source = {
            "id": str(uuid4()),
            "name": "Test RssFeed",
            "is_active": True,
        }

        process_manager = fetching_container.get_fetch_process_manager()
        process_manager._query_adapter.get_active = AsyncMock(
            return_value=[mock_source]
        )

        # Mock handler
        from src.scraping.app.commands import ScrapeMultiSourceCommand

        mock_result = Mock()
        mock_result.success = True
        mock_result.scraping_id = str(uuid4())
        mock_result.articles_fetched = 10

        original_handler = infra.mediator._handler_registry.get(
            ScrapeMultiSourceCommand
        )
        mock_handler = AsyncMock()
        mock_handler.handle = AsyncMock(return_value=mock_result)
        infra.mediator._handler_registry[ScrapeMultiSourceCommand] = mock_handler

        try:
            # Act - Usar parámetros personalizados
            command = RunFetchPipelineCommand(
                max_concurrent=10,
                priority_mode="high_priority",
                correlation_id="test_correlation_123",
            )
            result = await infra.mediator.send(command)

            # Assert
            assert result.success is True

            # Verificar que los parámetros se pasaron correctamente
            mock_handler.handle.assert_called_once()
            call_args = mock_handler.handle.call_args[0][0]
            assert call_args.max_concurrent == 10
            assert call_args.priority_mode == "high_priority"

        finally:
            if original_handler:
                infra.mediator._handler_registry[ScrapeMultiSourceCommand] = (
                    original_handler
                )

    @pytest.mark.asyncio
    async def test_execute_pipeline_flujo_completo_end_to_end(
        self, fetching_container, infra
    ):
        """Debería ejecutar flujo completo end-to-end del pipeline de fetch."""
        # Arrange - Register handlers
        fetching_container.register_pipeline_handlers()

        # Setup completo
        mock_sources = [
            {
                "id": str(uuid4()),
                "name": "Tech News",
                "url": "https://technews.com/feed.xml",
                "is_active": True,
            },
            {
                "id": str(uuid4()),
                "name": "Science Daily",
                "url": "https://sciencedaily.com/feed.xml",
                "is_active": True,
            },
        ]

        process_manager = fetching_container.get_fetch_process_manager()
        process_manager._query_adapter.get_active = AsyncMock(return_value=mock_sources)

        # Mock handler con resultados realistas
        from src.scraping.app.commands import ScrapeMultiSourceCommand

        mock_result = Mock()
        mock_result.success = True
        mock_result.scraping_id = str(uuid4())
        mock_result.articles_fetched = 15  # Artículos por source

        original_handler = infra.mediator._handler_registry.get(
            ScrapeMultiSourceCommand
        )
        mock_handler = AsyncMock()
        mock_handler.handle = AsyncMock(return_value=mock_result)
        infra.mediator._handler_registry[ScrapeMultiSourceCommand] = mock_handler

        try:
            # Act - Ejecutar pipeline completo
            command = RunFetchPipelineCommand(
                max_concurrent=5,
                priority_mode="normal",
            )
            result = await infra.mediator.send(command)

            # Assert - Verificar resultado completo
            assert result.success is True
            assert result.sources_processed == 2
            assert result.sources_success == 2
            assert result.sources_failed == 0
            assert result.total_articles_fetched == 30  # 15 * 2
            assert len(result.fetch_sessions) == 2
            assert result.duration_seconds > 0
            assert result.error is None

            # Verificar que se llamó al handler para cada source
            assert mock_handler.handle.call_count == 2

            # Verificar que cada llamada fue con el source correcto
            calls = mock_handler.handle.call_args_list
            source_ids_called = [call[0][0].source_ids[0] for call in calls]
            expected_ids = [s["id"] for s in mock_sources]
            assert set(source_ids_called) == set(expected_ids)

        finally:
            if original_handler:
                infra.mediator._handler_registry[ScrapeMultiSourceCommand] = (
                    original_handler
                )
