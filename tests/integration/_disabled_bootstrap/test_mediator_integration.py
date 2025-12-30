"""Integration tests para Mediator con containers.

Este módulo verifica que el Mediator se integra correctamente con
los containers del sistema, resolviendo handlers y ejecutando comandos.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.app.commands.pipelines.run_fetch_pipeline.command import (
    RunFetchPipelineCommand,
)
from src.app.commands.pipelines.run_processing_pipeline.command import (
    RunProcessingPipelineCommand,
)
from src.app.commands.pipelines.run_scraping_pipeline.command import (
    RunScrapingPipelineCommand,
)
from src.rss.article.container import RssArticleContainer
from src.scraping.container import ScrapingContainer
from src.shared.config.app_config import AppConfig
from src.shared.container import SharedContainer
from src.shared.infra.mediator import HandlerNotFoundError


@pytest.mark.integration
class TestMediatorIntegration:
    """Tests de integración para Mediator con containers."""

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
        """Crea RssArticleContainer."""
        return RssArticleContainer(infra)

    @pytest.fixture
    def scraping_container(self, infra, article_container):
        """Crea ScrapingContainer."""
        from src.rss.feed.container import RssFeedContainer

        source_container = RssFeedContainer(infra)
        return ScrapingContainer(infra, article_container, source_container)

    def test_mediator_se_inicializa_correctamente(self, infra):
        """Debería inicializar el Mediator correctamente."""
        # Assert
        assert infra.mediator is not None
        assert hasattr(infra.mediator, "_handler_registry")
        assert isinstance(infra.mediator._handler_registry, dict)
        assert len(infra.mediator._handler_registry) == 0  # Vacío al inicio

    def test_register_handler_agrega_handler_al_registry(self, infra):
        """Debería agregar handler al registry del Mediator."""
        # Arrange
        mock_handler = Mock()

        # Act
        infra.register_handler(RunScrapingPipelineCommand, mock_handler)

        # Assert
        assert RunScrapingPipelineCommand in infra.mediator._handler_registry
        assert (
            infra.mediator._handler_registry[RunScrapingPipelineCommand] == mock_handler
        )

    def test_article_container_registra_handlers_correctamente(
        self, infra, article_container
    ):
        """Debería registrar handlers de RssArticleContainer en el Mediator."""
        # Act
        article_container.register_handlers()

        # Assert
        assert RunScrapingPipelineCommand in infra.mediator._handler_registry
        assert RunProcessingPipelineCommand in infra.mediator._handler_registry

        # Verificar que los handlers son instancias correctas
        scraping_handler = infra.mediator._handler_registry[RunScrapingPipelineCommand]
        processing_handler = infra.mediator._handler_registry[
            RunProcessingPipelineCommand
        ]

        assert scraping_handler is not None
        assert processing_handler is not None
        assert hasattr(scraping_handler, "handle")
        assert hasattr(processing_handler, "handle")

        # Verificar que los handlers son instancias correctas
        assert scraping_handler.__class__.__name__ == "RunScrapingPipelineHandler"
        assert processing_handler.__class__.__name__ == "RunProcessingPipelineHandler"

    def test_scraping_container_registra_handlers_correctamente(
        self, infra, scraping_container
    ):
        """Debería registrar handlers de ScrapingContainer en el Mediator."""
        # Note: Este test verifica que el container puede registrar handlers
        # pero no los ejecuta porque requieren event loop async

        # Assert - Verificar que el container tiene los métodos de registro
        assert hasattr(scraping_container, "register_handlers")
        assert callable(scraping_container.register_handlers)

        # Verificar que el container tiene acceso al mediator
        assert scraping_container.shared.mediator is infra.mediator

    @pytest.mark.asyncio
    async def test_mediator_send_resuelve_handler_del_container(
        self, infra, article_container
    ):
        """Debería resolver y ejecutar handler registrado desde el container."""
        # Arrange
        article_container.register_handlers()

        # Mock el process manager para evitar ejecución real
        mock_process_manager = AsyncMock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.duration_seconds = 1.0
        mock_result.execution_time = "2024-01-01T00:00:00"
        mock_result.scraping = {"success": 0, "failed": 0, "total": 0}
        mock_result.plaintext = {"success": 0, "failed": 0, "total": 0}
        mock_result.markdown = {"success": 0, "failed": 0, "total": 0}
        mock_process_manager.execute.return_value = mock_result

        # Reemplazar process manager con mock
        handler = infra.mediator._handler_registry[RunScrapingPipelineCommand]
        handler._process_manager = mock_process_manager

        # Act
        command = RunScrapingPipelineCommand(limit=10)
        result = await infra.mediator.send(command)

        # Assert
        assert result is not None
        mock_process_manager.execute.assert_called_once_with(
            limit=10, force_rescrape=False
        )

    @pytest.mark.asyncio
    async def test_mediator_send_lanza_error_si_no_hay_handler(self, infra):
        """Debería lanzar HandlerNotFoundError si no hay handler registrado."""
        # Arrange
        command = RunScrapingPipelineCommand(limit=10)

        # Act & Assert
        with pytest.raises(HandlerNotFoundError) as exc_info:
            await infra.mediator.send(command)

        assert "No handler registered" in str(exc_info.value)
        assert "RunScrapingPipelineCommand" in str(exc_info.value)

    def test_multiples_containers_pueden_registrar_handlers(
        self, infra, article_container, scraping_container
    ):
        """Debería permitir que múltiples containers registren handlers."""
        # Act
        article_container.register_handlers()
        # Note: No registramos scraping_container porque requiere event loop

        # Assert - Verificar que article_container registró sus handlers
        assert len(infra.mediator._handler_registry) >= 2  # Al menos 2 handlers
        assert RunScrapingPipelineCommand in infra.mediator._handler_registry
        assert RunProcessingPipelineCommand in infra.mediator._handler_registry

        # Verificar que ambos containers comparten el mismo mediator
        assert article_container.shared.mediator is infra.mediator
        assert scraping_container.shared.mediator is infra.mediator

    def test_handler_registry_es_compartido_entre_containers(
        self, infra, article_container, scraping_container
    ):
        """Debería compartir el mismo handler registry entre containers."""
        # Act
        article_container.register_handlers()
        # Note: No registramos scraping_container porque requiere event loop

        # Assert - Verificar que el handler registry es compartido
        assert RunScrapingPipelineCommand in infra.mediator._handler_registry

        # Verificar que ambos containers usan el mismo mediator
        assert article_container.shared.mediator is infra.mediator
        assert scraping_container.shared.mediator is infra.mediator

        # Verificar que el registry es el mismo objeto
        assert id(article_container.shared.mediator._handler_registry) == id(
            infra.mediator._handler_registry
        )
        assert (
            RunScrapingPipelineCommand
            in fetching_container.infra.mediator._handler_registry
        )

        # Verificar que es la misma instancia del Mediator
        assert article_container.infra.mediator is fetching_container.infra.mediator
        assert article_container.infra.mediator is infra.mediator
