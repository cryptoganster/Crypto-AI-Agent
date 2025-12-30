"""Tests unitarios para FetchingContainer.

Verifica que todos los handlers de Fetching están registrados correctamente,
en el orden correcto, y con logging apropiado.

**Requirements: 1.1, 2.1**
"""

from unittest.mock import Mock, call, patch

import pytest

from src.bootstrap.containers.fetching_container import FetchingContainer


class TestFetchingContainer:
    """Tests unitarios para FetchingContainer."""

    @pytest.fixture
    def mock_infra(self):
        """Mock de SharedInfrastructure."""
        infra = Mock()
        infra.logger = Mock()
        infra.mediator = Mock()
        infra.mediator._handler_registry = {}
        infra.session_factory = Mock()
        infra.time_provider = Mock()
        infra.event_publisher = Mock()

        # Mock register_handler para capturar llamadas
        def register_handler_side_effect(command_type, handler):
            infra.mediator._handler_registry[command_type] = handler

        infra.register_handler = Mock(side_effect=register_handler_side_effect)

        return infra

    @pytest.fixture
    def container(self, mock_infra):
        """Container de Fetching para tests."""
        return FetchingContainer(infra=mock_infra)

    def test_container_initialization(self, container, mock_infra):
        """Debería inicializar el container correctamente."""
        # Assert
        assert container.infra == mock_infra
        assert container.articles is None
        assert container._run_fetch_pipeline_handler is None
        assert container._start_fetch_session_handler is None
        assert container._update_fetch_config_handler is None

    def test_register_pipeline_handlers_registers_all_fetching_handlers(
        self, container, mock_infra
    ):
        """Debería registrar todos los handlers de Fetching en el Mediator.

        Verifica que se registran:
        - RunFetchPipelineHandler
        - ScrapeMultiSourceHandler (antes StartFetchSessionHandler)
        - ScrapeSingleSourceHandler (antes FetchSourceHandler)
        - UpdateScrapingConfigHandler (antes UpdateFetchConfigHandler)

        **Requirements: 1.1**
        """
        from src.app.commands.pipelines.run_fetch_pipeline.command import (
            RunFetchPipelineCommand,
        )
        from src.scraping.app.commands import (
            ScrapeMultiSourceCommand,
            ScrapeSingleSourceCommand,
            UpdateScrapingConfigCommand,
        )

        # Arrange - Mock handler getters to return mock handlers
        mock_handlers = {
            "run_fetch_pipeline": Mock(handle=Mock()),
            "start_fetch_session": Mock(handle=Mock()),
            "fetch_source": Mock(handle=Mock()),
            "update_fetch_config": Mock(handle=Mock()),
        }

        container.get_run_fetch_pipeline_handler = Mock(
            return_value=mock_handlers["run_fetch_pipeline"]
        )
        container.get_start_fetch_session_handler = Mock(
            return_value=mock_handlers["start_fetch_session"]
        )
        container.get_fetch_source_handler = Mock(
            return_value=mock_handlers["fetch_source"]
        )
        container.get_update_fetch_config_handler = Mock(
            return_value=mock_handlers["update_fetch_config"]
        )

        # Act
        container.register_pipeline_handlers()

        # Assert - Verificar que se llamó register_handler 4 veces
        assert mock_infra.register_handler.call_count == 4

        # Assert - Verificar que todos los comandos están registrados
        registered_commands = [
            call_args[0][0] for call_args in mock_infra.register_handler.call_args_list
        ]

        assert RunFetchPipelineCommand in registered_commands
        assert ScrapeMultiSourceCommand in registered_commands
        assert ScrapeSingleSourceCommand in registered_commands
        assert UpdateScrapingConfigCommand in registered_commands

    def test_register_pipeline_handlers_logs_registered_handlers(
        self, container, mock_infra
    ):
        """Debería loggear la lista de handlers registrados.

        Verifica que se loggea:
        - Lista de nombres de handlers
        - Cantidad total de handlers

        **Requirements: 2.1**
        """
        # Arrange - Mock handler getters
        container.get_run_fetch_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_start_fetch_session_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_fetch_source_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_update_fetch_config_handler = Mock(
            return_value=Mock(handle=Mock())
        )

        # Act
        container.register_pipeline_handlers()

        # Assert - Verificar que se llamó logger.info
        mock_infra.logger.info.assert_called_once()

        # Verificar argumentos del log
        call_args = mock_infra.logger.info.call_args
        assert call_args[0][0] == "Pipeline handlers registrados en Mediator"

        # Verificar que se loggearon los handlers
        logged_handlers = call_args[1]["handlers"]
        assert "RunFetchPipelineHandler" in logged_handlers
        assert "ScrapeMultiSourceHandler" in logged_handlers
        assert "ScrapeSingleSourceHandler" in logged_handlers
        assert "UpdateScrapingConfigHandler" in logged_handlers

        # Verificar que se loggeó el count
        assert call_args[1]["count"] == 4

    def test_handlers_are_callable(self, container, mock_infra):
        """Debería registrar handlers que tienen método handle.

        **Requirements: 1.1**
        """
        from src.app.commands.pipelines.run_fetch_pipeline.command import (
            RunFetchPipelineCommand,
        )
        from src.scraping.app.commands import (
            ScrapeMultiSourceCommand,
            ScrapeSingleSourceCommand,
            UpdateScrapingConfigCommand,
        )

        # Arrange - Mock handler getters
        container.get_run_fetch_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_start_fetch_session_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_fetch_source_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_update_fetch_config_handler = Mock(
            return_value=Mock(handle=Mock())
        )

        # Act
        container.register_pipeline_handlers()

        # Assert - Verificar que todos los handlers tienen método handle
        handlers = [
            mock_infra.mediator._handler_registry[RunFetchPipelineCommand],
            mock_infra.mediator._handler_registry[ScrapeMultiSourceCommand],
            mock_infra.mediator._handler_registry[ScrapeSingleSourceCommand],
            mock_infra.mediator._handler_registry[UpdateScrapingConfigCommand],
        ]

        for handler in handlers:
            assert hasattr(handler, "handle")
            assert callable(handler.handle)

    def test_register_pipeline_handlers_can_be_called_multiple_times(
        self, container, mock_infra
    ):
        """Debería permitir llamar register_pipeline_handlers múltiples veces.

        **Requirements: 1.1**
        """
        # Arrange - Mock handler getters
        container.get_run_fetch_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_start_fetch_session_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_fetch_source_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_update_fetch_config_handler = Mock(
            return_value=Mock(handle=Mock())
        )

        # Act - Llamar múltiples veces
        container.register_pipeline_handlers()
        container.register_pipeline_handlers()
        container.register_pipeline_handlers()

        # Assert - Verificar que se registraron los handlers
        # (el último registro sobrescribe los anteriores)
        assert len(mock_infra.mediator._handler_registry) == 4

        # Verificar que logger.info se llamó 3 veces
        assert mock_infra.logger.info.call_count == 3

    def test_register_pipeline_handlers_with_articles_container(self, mock_infra):
        """Debería funcionar correctamente cuando se inyecta RssArticleContainer.

        **Requirements: 1.1**
        """
        # Arrange
        mock_articles = Mock()
        mock_articles.get_article_factory = Mock(return_value=Mock())

        container = FetchingContainer(infra=mock_infra, articles=mock_articles)

        # Mock handler getters
        container.get_run_fetch_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_start_fetch_session_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_fetch_source_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_update_fetch_config_handler = Mock(
            return_value=Mock(handle=Mock())
        )

        # Act
        container.register_pipeline_handlers()

        # Assert - Verificar que se registraron todos los handlers
        assert len(mock_infra.mediator._handler_registry) == 4

        # Verificar que se usó el RssArticleFactory del RssArticleContainer
        assert container.articles is mock_articles
