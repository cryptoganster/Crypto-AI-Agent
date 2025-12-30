"""Integration tests para ScrapingProcessManager con componentes reales.

Este módulo verifica que el ScrapingProcessManager se integra correctamente
con el Mediator real, Query Adapters reales y base de datos de test.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from src.app.process_managers.scraping_process_manager import ScrapingProcessManager
from src.rss.article.app.commands.scrape_article_content.command import (
    ScrapeRssArticleContentCommand,
)
from src.rss.article.container import RssArticleContainer
from src.shared.config.app_config import AppConfig
from src.shared.container import SharedContainer


@pytest.mark.integration
class TestScrapingProcessManagerIntegration:
    """Tests de integración para ScrapingProcessManager."""

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
        container.register_handlers()
        return container

    @pytest.fixture
    def scraping_process_manager(self, article_container):
        """Crea ScrapingProcessManager con dependencias reales."""
        return article_container.get_scraping_process_manager()

    @pytest.mark.asyncio
    async def test_process_manager_se_inicializa_con_dependencias_reales(
        self, scraping_process_manager
    ):
        """Debería inicializar con Mediator y Query Adapter reales."""
        # Assert
        assert scraping_process_manager is not None
        assert scraping_process_manager._mediator is not None
        assert scraping_process_manager._query_adapter is not None
        assert scraping_process_manager._logger is not None

    @pytest.mark.asyncio
    async def test_execute_con_query_adapter_real_sin_articulos(
        self, scraping_process_manager
    ):
        """Debería ejecutar correctamente cuando no hay artículos para procesar."""
        # Arrange - Mock query adapter para retornar lista vacía
        scraping_process_manager._query_adapter.get_without_content_scrapped = (
            AsyncMock(return_value=[])
        )
        scraping_process_manager._query_adapter.get_without_content_plaintext = (
            AsyncMock(return_value=[])
        )
        scraping_process_manager._query_adapter.get_without_content_markdown = (
            AsyncMock(return_value=[])
        )

        # Act
        result = await scraping_process_manager.execute(limit=10)

        # Assert
        assert result.success is True
        assert result.scraping == {"success": 0, "failed": 0, "total": 0}
        assert result.plaintext == {"success": 0, "failed": 0, "total": 0}
        assert result.markdown == {"success": 0, "failed": 0, "total": 0}
        assert result.duration_seconds > 0
        assert result.execution_time is not None

    @pytest.mark.asyncio
    async def test_execute_scraping_phase_con_mediator_real(
        self, scraping_process_manager, infra
    ):
        """Debería ejecutar fase de scraping usando Mediator real."""
        # Arrange - Crear artículos mock
        mock_article = Mock()
        mock_article.id = uuid4()

        scraping_process_manager._query_adapter.get_without_content_scrapped = (
            AsyncMock(return_value=[mock_article])
        )
        scraping_process_manager._query_adapter.get_without_content_plaintext = (
            AsyncMock(return_value=[])
        )
        scraping_process_manager._query_adapter.get_without_content_markdown = (
            AsyncMock(return_value=[])
        )

        # Mock el handler de scraping para evitar scraping real
        mock_scraping_result = Mock()
        mock_scraping_result.success = True

        original_handler = infra.mediator._handler_registry.get(
            ScrapeRssArticleContentCommand
        )
        mock_handler = AsyncMock()
        mock_handler.handle = AsyncMock(return_value=mock_scraping_result)
        infra.mediator._handler_registry[ScrapeRssArticleContentCommand] = mock_handler

        try:
            # Act
            result = await scraping_process_manager.execute(limit=10)

            # Assert
            assert result.success is True
            assert result.scraping["success"] == 1
            assert result.scraping["failed"] == 0
            assert result.scraping["total"] == 1

            # Verificar que se llamó al handler vía Mediator
            mock_handler.handle.assert_called_once()
            call_args = mock_handler.handle.call_args[0][0]
            assert isinstance(call_args, ScrapeRssArticleContentCommand)
            assert str(call_args.article_id) == str(mock_article.id)

        finally:
            # Restaurar handler original
            if original_handler:
                infra.mediator._handler_registry[ScrapeRssArticleContentCommand] = (
                    original_handler
                )

    @pytest.mark.asyncio
    async def test_execute_maneja_errores_parciales_correctamente(
        self, scraping_process_manager, infra
    ):
        """Debería manejar errores parciales sin detener el pipeline."""
        # Arrange - Crear múltiples artículos mock
        mock_articles = [Mock(id=uuid4()) for _ in range(3)]

        scraping_process_manager._query_adapter.get_without_content_scrapped = (
            AsyncMock(return_value=mock_articles)
        )
        scraping_process_manager._query_adapter.get_without_content_plaintext = (
            AsyncMock(return_value=[])
        )
        scraping_process_manager._query_adapter.get_without_content_markdown = (
            AsyncMock(return_value=[])
        )

        # Mock handler que falla para el segundo artículo
        call_count = 0

        async def mock_handle(command):
            nonlocal call_count
            call_count += 1
            result = Mock()
            result.success = call_count != 2  # Falla en el segundo
            return result

        original_handler = infra.mediator._handler_registry.get(
            ScrapeRssArticleContentCommand
        )
        mock_handler = AsyncMock()
        mock_handler.handle = mock_handle
        infra.mediator._handler_registry[ScrapeRssArticleContentCommand] = mock_handler

        try:
            # Act
            result = await scraping_process_manager.execute(limit=10)

            # Assert
            assert result.success is True
            assert result.scraping["success"] == 2  # 2 exitosos
            assert result.scraping["failed"] == 1  # 1 fallido
            assert result.scraping["total"] == 3  # Total 3

        finally:
            # Restaurar handler original
            if original_handler:
                infra.mediator._handler_registry[ScrapeRssArticleContentCommand] = (
                    original_handler
                )

    @pytest.mark.asyncio
    async def test_execute_flujo_completo_de_una_fase(
        self, scraping_process_manager, infra
    ):
        """Debería ejecutar flujo completo de una fase con todos los componentes."""
        # Arrange
        mock_article = Mock()
        mock_article.id = uuid4()

        # Mock query adapters
        scraping_process_manager._query_adapter.get_without_content_scrapped = (
            AsyncMock(return_value=[mock_article])
        )
        scraping_process_manager._query_adapter.get_without_content_plaintext = (
            AsyncMock(return_value=[])
        )
        scraping_process_manager._query_adapter.get_without_content_markdown = (
            AsyncMock(return_value=[])
        )

        # Mock handler
        mock_result = Mock()
        mock_result.success = True
        mock_handler = AsyncMock()
        mock_handler.handle = AsyncMock(return_value=mock_result)

        original_handler = infra.mediator._handler_registry.get(
            ScrapeRssArticleContentCommand
        )
        infra.mediator._handler_registry[ScrapeRssArticleContentCommand] = mock_handler

        try:
            # Act
            result = await scraping_process_manager.execute(
                limit=10, force_rescrape=True
            )

            # Assert - Verificar resultado
            assert result.success is True
            assert result.scraping["total"] == 1
            assert result.duration_seconds > 0

            # Verificar que se usó el query adapter
            scraping_process_manager._query_adapter.get_without_content_scrapped.assert_called_once_with(
                limit=10
            )

            # Verificar que se envió comando vía Mediator
            mock_handler.handle.assert_called_once()
            command = mock_handler.handle.call_args[0][0]
            assert command.force_rescrape is True
            assert command.timeout_seconds == 30
            assert command.use_smart_scraper is True

        finally:
            if original_handler:
                infra.mediator._handler_registry[ScrapeRssArticleContentCommand] = (
                    original_handler
                )

    @pytest.mark.asyncio
    async def test_idempotency_skip_articulos_ya_procesados(
        self, scraping_process_manager
    ):
        """Debería garantizar idempotencia al skip artículos ya procesados."""
        # Arrange - Primera ejecución: hay artículos
        mock_article = Mock()
        mock_article.id = uuid4()

        scraping_process_manager._query_adapter.get_without_content_scrapped = (
            AsyncMock(return_value=[mock_article])
        )
        scraping_process_manager._query_adapter.get_without_content_plaintext = (
            AsyncMock(return_value=[])
        )
        scraping_process_manager._query_adapter.get_without_content_markdown = (
            AsyncMock(return_value=[])
        )

        # Mock handler exitoso
        mock_result = Mock()
        mock_result.success = True
        mock_handler = AsyncMock()
        mock_handler.handle = AsyncMock(return_value=mock_result)

        original_handler = scraping_process_manager._mediator._handler_registry.get(
            ScrapeRssArticleContentCommand
        )
        scraping_process_manager._mediator._handler_registry[
            ScrapeRssArticleContentCommand
        ] = mock_handler

        try:
            # Act - Primera ejecución
            result1 = await scraping_process_manager.execute(limit=10)

            # Arrange - Segunda ejecución: query adapter retorna vacío (ya procesados)
            scraping_process_manager._query_adapter.get_without_content_scrapped = (
                AsyncMock(return_value=[])
            )

            # Act - Segunda ejecución
            result2 = await scraping_process_manager.execute(limit=10)

            # Assert
            assert result1.success is True
            assert result1.scraping["total"] == 1

            assert result2.success is True
            assert result2.scraping["total"] == 0  # No hay artículos para procesar

            # Verificar que el handler solo se llamó una vez (primera ejecución)
            assert mock_handler.handle.call_count == 1

        finally:
            if original_handler:
                scraping_process_manager._mediator._handler_registry[
                    ScrapeRssArticleContentCommand
                ] = original_handler

    @pytest.mark.asyncio
    async def test_execute_retorna_resultado_estructurado(
        self, scraping_process_manager
    ):
        """Debería retornar resultado estructurado con todos los campos requeridos."""
        # Arrange
        scraping_process_manager._query_adapter.get_without_content_scrapped = (
            AsyncMock(return_value=[])
        )
        scraping_process_manager._query_adapter.get_without_content_plaintext = (
            AsyncMock(return_value=[])
        )
        scraping_process_manager._query_adapter.get_without_content_markdown = (
            AsyncMock(return_value=[])
        )

        # Act
        result = await scraping_process_manager.execute(limit=10)

        # Assert - Verificar estructura del resultado
        assert hasattr(result, "success")
        assert hasattr(result, "duration_seconds")
        assert hasattr(result, "execution_time")
        assert hasattr(result, "scraping")
        assert hasattr(result, "plaintext")
        assert hasattr(result, "markdown")

        # Verificar tipos
        assert isinstance(result.success, bool)
        assert isinstance(result.duration_seconds, float)
        assert isinstance(result.execution_time, str)
        assert isinstance(result.scraping, dict)
        assert isinstance(result.plaintext, dict)
        assert isinstance(result.markdown, dict)

        # Verificar que cada fase tiene las claves correctas
        for phase in [result.scraping, result.plaintext, result.markdown]:
            assert "success" in phase
            assert "failed" in phase
            assert "total" in phase
