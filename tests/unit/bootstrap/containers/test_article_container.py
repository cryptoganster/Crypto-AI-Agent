"""Tests unitarios para RssArticleContainer.

Verifica que todos los handlers de RssArticle están registrados correctamente,
en el orden correcto, y con logging apropiado.

**Requirements: 1.1, 2.1**
"""

from unittest.mock import Mock

import pytest

from src.bootstrap.containers.article_container import RssArticleContainer


class TestRssArticleContainer:
    """Tests unitarios para RssArticleContainer."""

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
    def mock_domain_services(self):
        """Mock de DomainServicesContainer."""
        domain_services = Mock()
        domain_services.get_article_quality_service = Mock(return_value=Mock())
        domain_services.get_article_keyword_service = Mock(return_value=Mock())
        domain_services.get_article_hashing_service = Mock(return_value=Mock())
        return domain_services

    @pytest.fixture
    def container(self, mock_infra, mock_domain_services):
        """Container de Article para tests."""
        return RssArticleContainer(
            infra=mock_infra, domain_services=mock_domain_services
        )

    def test_container_initialization(
        self, container, mock_infra, mock_domain_services
    ):
        """Debería inicializar el container correctamente."""
        # Assert
        assert container.infra == mock_infra
        assert container.domain_services == mock_domain_services
        assert container._run_scraping_pipeline_handler is None
        assert container._run_processing_pipeline_handler is None
        assert container._scrape_content_handler is None
        assert container._extract_plaintext_handler is None
        assert container._convert_to_markdown_handler is None
        assert container._calculate_metrics_handler is None
        assert container._detect_language_handler is None
        assert container._generate_summary_handler is None
        assert container._extract_keywords_handler is None
        assert container._calculate_quality_handler is None

    def test_register_pipeline_handlers_registers_all_article_handlers(
        self, container, mock_infra
    ):
        """Debería registrar todos los handlers de RssArticle en el Mediator.

        Verifica que se registran:
        - RunScrapingPipelineHandler
        - RunProcessingPipelineHandler
        - ScrapeArticleContentHandler
        - ExtractArticlePlaintextHandler
        - ConvertArticleToMarkdownHandler
        - CalculateArticleMetricsHandler
        - DetectArticleLanguageHandler
        - GenerateArticleSummaryHandler
        - ExtractArticleKeywordsHandler
        - CalculateArticleQualityHandler

        **Requirements: 1.1**
        """
        from src.app.commands.pipelines.run_processing_pipeline.command import (
            RunProcessingPipelineCommand,
        )
        from src.app.commands.pipelines.run_scraping_pipeline.command import (
            RunScrapingPipelineCommand,
        )
        from src.rss.article.app.commands.calculate_article_metrics.command import (
            CalculateArticleMetricsCommand,
        )
        from src.rss.article.app.commands.calculate_article_quality.command import (
            CalculateArticleQualityCommand,
        )
        from src.rss.article.app.commands.convert_article_to_markdown.command import (
            ConvertArticleToMarkdownCommand,
        )
        from src.rss.article.app.commands.detect_article_language.command import (
            DetectArticleLanguageCommand,
        )
        from src.rss.article.app.commands.extract_article_keywords.command import (
            ExtractArticleKeywordsCommand,
        )
        from src.rss.article.app.commands.extract_article_plaintext.command import (
            ExtractArticlePlaintextCommand,
        )
        from src.rss.article.app.commands.generate_article_summary.command import (
            GenerateArticleSummaryCommand,
        )
        from src.rss.article.app.commands.scrape_article_content.command import (
            ScrapeRssArticleContentCommand,
        )

        # Arrange - Mock handler getters to return mock handlers
        mock_handlers = {
            "run_scraping_pipeline": Mock(handle=Mock()),
            "run_processing_pipeline": Mock(handle=Mock()),
            "scrape_content": Mock(handle=Mock()),
            "extract_plaintext": Mock(handle=Mock()),
            "convert_to_markdown": Mock(handle=Mock()),
            "calculate_metrics": Mock(handle=Mock()),
            "detect_language": Mock(handle=Mock()),
            "generate_summary": Mock(handle=Mock()),
            "extract_keywords": Mock(handle=Mock()),
            "calculate_quality": Mock(handle=Mock()),
        }

        container.get_run_scraping_pipeline_handler = Mock(
            return_value=mock_handlers["run_scraping_pipeline"]
        )
        container.get_run_processing_pipeline_handler = Mock(
            return_value=mock_handlers["run_processing_pipeline"]
        )
        container.get_scrape_content_handler = Mock(
            return_value=mock_handlers["scrape_content"]
        )
        container.get_extract_plaintext_handler = Mock(
            return_value=mock_handlers["extract_plaintext"]
        )
        container.get_convert_to_markdown_handler = Mock(
            return_value=mock_handlers["convert_to_markdown"]
        )
        container.get_calculate_metrics_handler = Mock(
            return_value=mock_handlers["calculate_metrics"]
        )
        container.get_detect_language_handler = Mock(
            return_value=mock_handlers["detect_language"]
        )
        container.get_generate_summary_handler = Mock(
            return_value=mock_handlers["generate_summary"]
        )
        container.get_extract_keywords_handler = Mock(
            return_value=mock_handlers["extract_keywords"]
        )
        container.get_calculate_quality_handler = Mock(
            return_value=mock_handlers["calculate_quality"]
        )

        # Act
        container.register_pipeline_handlers()

        # Assert - Verificar que se llamó register_handler 10 veces
        assert mock_infra.register_handler.call_count == 10

        # Assert - Verificar que todos los comandos están registrados
        registered_commands = [
            call_args[0][0] for call_args in mock_infra.register_handler.call_args_list
        ]

        assert RunScrapingPipelineCommand in registered_commands
        assert RunProcessingPipelineCommand in registered_commands
        assert ScrapeRssArticleContentCommand in registered_commands
        assert ExtractArticlePlaintextCommand in registered_commands
        assert ConvertArticleToMarkdownCommand in registered_commands
        assert CalculateArticleMetricsCommand in registered_commands
        assert DetectArticleLanguageCommand in registered_commands
        assert GenerateArticleSummaryCommand in registered_commands
        assert ExtractArticleKeywordsCommand in registered_commands
        assert CalculateArticleQualityCommand in registered_commands

        # Assert - Verificar que los handlers no son None
        assert (
            mock_infra.mediator._handler_registry[RunScrapingPipelineCommand]
            is not None
        )
        assert (
            mock_infra.mediator._handler_registry[RunProcessingPipelineCommand]
            is not None
        )
        assert (
            mock_infra.mediator._handler_registry[ScrapeRssArticleContentCommand]
            is not None
        )
        assert (
            mock_infra.mediator._handler_registry[ExtractArticlePlaintextCommand]
            is not None
        )
        assert (
            mock_infra.mediator._handler_registry[ConvertArticleToMarkdownCommand]
            is not None
        )
        assert (
            mock_infra.mediator._handler_registry[CalculateArticleMetricsCommand]
            is not None
        )
        assert (
            mock_infra.mediator._handler_registry[DetectArticleLanguageCommand]
            is not None
        )
        assert (
            mock_infra.mediator._handler_registry[GenerateArticleSummaryCommand]
            is not None
        )
        assert (
            mock_infra.mediator._handler_registry[ExtractArticleKeywordsCommand]
            is not None
        )
        assert (
            mock_infra.mediator._handler_registry[CalculateArticleQualityCommand]
            is not None
        )

    def test_register_pipeline_handlers_registers_in_correct_order(
        self, container, mock_infra
    ):
        """Debería registrar handlers en el orden correcto.

        Orden esperado:
        1. RunScrapingPipelineCommand (pipeline handler)
        2. RunProcessingPipelineCommand (pipeline handler)
        3. ScrapeRssArticleContentCommand (scraping pipeline)
        4. ExtractArticlePlaintextCommand (scraping pipeline)
        5. ConvertArticleToMarkdownCommand (scraping pipeline)
        6. CalculateArticleMetricsCommand (processing pipeline)
        7. DetectArticleLanguageCommand (processing pipeline)
        8. GenerateArticleSummaryCommand (processing pipeline)
        9. ExtractArticleKeywordsCommand (processing pipeline)
        10. CalculateArticleQualityCommand (processing pipeline)

        **Requirements: 1.1**
        """
        from src.app.commands.pipelines.run_processing_pipeline.command import (
            RunProcessingPipelineCommand,
        )
        from src.app.commands.pipelines.run_scraping_pipeline.command import (
            RunScrapingPipelineCommand,
        )
        from src.rss.article.app.commands.calculate_article_metrics.command import (
            CalculateArticleMetricsCommand,
        )
        from src.rss.article.app.commands.calculate_article_quality.command import (
            CalculateArticleQualityCommand,
        )
        from src.rss.article.app.commands.convert_article_to_markdown.command import (
            ConvertArticleToMarkdownCommand,
        )
        from src.rss.article.app.commands.detect_article_language.command import (
            DetectArticleLanguageCommand,
        )
        from src.rss.article.app.commands.extract_article_keywords.command import (
            ExtractArticleKeywordsCommand,
        )
        from src.rss.article.app.commands.extract_article_plaintext.command import (
            ExtractArticlePlaintextCommand,
        )
        from src.rss.article.app.commands.generate_article_summary.command import (
            GenerateArticleSummaryCommand,
        )
        from src.rss.article.app.commands.scrape_article_content.command import (
            ScrapeRssArticleContentCommand,
        )

        # Arrange - Mock handler getters
        container.get_run_scraping_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_run_processing_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_scrape_content_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_plaintext_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_convert_to_markdown_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_calculate_metrics_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_detect_language_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_generate_summary_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_keywords_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_calculate_quality_handler = Mock(return_value=Mock(handle=Mock()))

        # Act
        container.register_pipeline_handlers()

        # Assert - Verificar orden de registro
        call_args_list = mock_infra.register_handler.call_args_list

        assert call_args_list[0][0][0] == RunScrapingPipelineCommand
        assert call_args_list[1][0][0] == RunProcessingPipelineCommand
        assert call_args_list[2][0][0] == ScrapeRssArticleContentCommand
        assert call_args_list[3][0][0] == ExtractArticlePlaintextCommand
        assert call_args_list[4][0][0] == ConvertArticleToMarkdownCommand
        assert call_args_list[5][0][0] == CalculateArticleMetricsCommand
        assert call_args_list[6][0][0] == DetectArticleLanguageCommand
        assert call_args_list[7][0][0] == GenerateArticleSummaryCommand
        assert call_args_list[8][0][0] == ExtractArticleKeywordsCommand
        assert call_args_list[9][0][0] == CalculateArticleQualityCommand

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
        container.get_run_scraping_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_run_processing_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_scrape_content_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_plaintext_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_convert_to_markdown_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_calculate_metrics_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_detect_language_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_generate_summary_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_keywords_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_calculate_quality_handler = Mock(return_value=Mock(handle=Mock()))

        # Act
        container.register_pipeline_handlers()

        # Assert - Verificar que se llamó logger.info
        mock_infra.logger.info.assert_called_once()

        # Verificar argumentos del log
        call_args = mock_infra.logger.info.call_args
        assert call_args[0][0] == "Pipeline handlers registrados en Mediator"

        # Verificar que se loggearon los handlers
        logged_handlers = call_args[1]["handlers"]
        assert "RunScrapingPipelineHandler" in logged_handlers
        assert "RunProcessingPipelineHandler" in logged_handlers
        assert "ScrapeArticleContentHandler" in logged_handlers
        assert "ExtractArticlePlaintextHandler" in logged_handlers
        assert "ConvertArticleToMarkdownHandler" in logged_handlers
        assert "CalculateArticleMetricsHandler" in logged_handlers
        assert "DetectArticleLanguageHandler" in logged_handlers
        assert "GenerateArticleSummaryHandler" in logged_handlers
        assert "ExtractArticleKeywordsHandler" in logged_handlers
        assert "CalculateArticleQualityHandler" in logged_handlers

        # Verificar que se loggeó el count
        assert call_args[1]["count"] == 10

    def test_register_pipeline_handlers_logs_correct_handler_names(
        self, container, mock_infra
    ):
        """Debería loggear los nombres correctos de los handlers.

        **Requirements: 2.1**
        """
        # Arrange - Mock handler getters
        container.get_run_scraping_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_run_processing_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_scrape_content_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_plaintext_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_convert_to_markdown_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_calculate_metrics_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_detect_language_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_generate_summary_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_keywords_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_calculate_quality_handler = Mock(return_value=Mock(handle=Mock()))

        # Act
        container.register_pipeline_handlers()

        # Assert
        call_args = mock_infra.logger.info.call_args
        logged_handlers = call_args[1]["handlers"]

        # Verificar nombres exactos en orden
        expected_handlers = [
            "RunScrapingPipelineHandler",
            "RunProcessingPipelineHandler",
            "ScrapeArticleContentHandler",
            "ExtractArticlePlaintextHandler",
            "ConvertArticleToMarkdownHandler",
            "CalculateArticleMetricsHandler",
            "DetectArticleLanguageHandler",
            "GenerateArticleSummaryHandler",
            "ExtractArticleKeywordsHandler",
            "CalculateArticleQualityHandler",
        ]

        assert logged_handlers == expected_handlers

    def test_handlers_are_callable(self, container, mock_infra):
        """Debería registrar handlers que tienen método handle.

        **Requirements: 1.1**
        """
        from src.app.commands.pipelines.run_processing_pipeline.command import (
            RunProcessingPipelineCommand,
        )
        from src.app.commands.pipelines.run_scraping_pipeline.command import (
            RunScrapingPipelineCommand,
        )
        from src.rss.article.app.commands.calculate_article_metrics.command import (
            CalculateArticleMetricsCommand,
        )
        from src.rss.article.app.commands.calculate_article_quality.command import (
            CalculateArticleQualityCommand,
        )
        from src.rss.article.app.commands.convert_article_to_markdown.command import (
            ConvertArticleToMarkdownCommand,
        )
        from src.rss.article.app.commands.detect_article_language.command import (
            DetectArticleLanguageCommand,
        )
        from src.rss.article.app.commands.extract_article_keywords.command import (
            ExtractArticleKeywordsCommand,
        )
        from src.rss.article.app.commands.extract_article_plaintext.command import (
            ExtractArticlePlaintextCommand,
        )
        from src.rss.article.app.commands.generate_article_summary.command import (
            GenerateArticleSummaryCommand,
        )
        from src.rss.article.app.commands.scrape_article_content.command import (
            ScrapeRssArticleContentCommand,
        )

        # Arrange - Mock handler getters
        container.get_run_scraping_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_run_processing_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_scrape_content_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_plaintext_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_convert_to_markdown_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_calculate_metrics_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_detect_language_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_generate_summary_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_keywords_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_calculate_quality_handler = Mock(return_value=Mock(handle=Mock()))

        # Act
        container.register_pipeline_handlers()

        # Assert - Verificar que todos los handlers tienen método handle
        handlers = [
            mock_infra.mediator._handler_registry[RunScrapingPipelineCommand],
            mock_infra.mediator._handler_registry[RunProcessingPipelineCommand],
            mock_infra.mediator._handler_registry[ScrapeRssArticleContentCommand],
            mock_infra.mediator._handler_registry[ExtractArticlePlaintextCommand],
            mock_infra.mediator._handler_registry[ConvertArticleToMarkdownCommand],
            mock_infra.mediator._handler_registry[CalculateArticleMetricsCommand],
            mock_infra.mediator._handler_registry[DetectArticleLanguageCommand],
            mock_infra.mediator._handler_registry[GenerateArticleSummaryCommand],
            mock_infra.mediator._handler_registry[ExtractArticleKeywordsCommand],
            mock_infra.mediator._handler_registry[CalculateArticleQualityCommand],
        ]

        for handler in handlers:
            assert hasattr(handler, "handle")
            assert callable(handler.handle)

    def test_handlers_are_singletons(self, container, mock_infra):
        """Debería retornar la misma instancia de handler en múltiples llamadas.

        **Requirements: 1.1**
        """
        # Arrange - Mock handler getters to return same instances
        mock_handler1 = Mock(handle=Mock())
        mock_handler2 = Mock(handle=Mock())

        container.get_run_scraping_pipeline_handler = Mock(return_value=mock_handler1)
        container.get_run_processing_pipeline_handler = Mock(return_value=mock_handler2)
        container.get_scrape_content_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_plaintext_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_convert_to_markdown_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_calculate_metrics_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_detect_language_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_generate_summary_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_keywords_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_calculate_quality_handler = Mock(return_value=Mock(handle=Mock()))

        # Act - Registrar handlers dos veces
        container.register_pipeline_handlers()

        # Guardar referencias a handlers
        from src.app.commands.pipelines.run_processing_pipeline.command import (
            RunProcessingPipelineCommand,
        )
        from src.app.commands.pipelines.run_scraping_pipeline.command import (
            RunScrapingPipelineCommand,
        )

        handler1 = mock_infra.mediator._handler_registry[RunScrapingPipelineCommand]
        handler2 = mock_infra.mediator._handler_registry[RunProcessingPipelineCommand]

        # Registrar de nuevo
        container.register_pipeline_handlers()

        # Assert - Verificar que son las mismas instancias
        handler1_again = mock_infra.mediator._handler_registry[
            RunScrapingPipelineCommand
        ]
        handler2_again = mock_infra.mediator._handler_registry[
            RunProcessingPipelineCommand
        ]

        assert handler1 is handler1_again
        assert handler2 is handler2_again

        # Verificar que los getters se llamaron 2 veces cada uno
        assert container.get_run_scraping_pipeline_handler.call_count == 2
        assert container.get_run_processing_pipeline_handler.call_count == 2

    def test_register_pipeline_handlers_can_be_called_multiple_times(
        self, container, mock_infra
    ):
        """Debería permitir llamar register_pipeline_handlers múltiples veces.

        **Requirements: 1.1**
        """
        # Arrange - Mock handler getters
        container.get_run_scraping_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_run_processing_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_scrape_content_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_plaintext_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_convert_to_markdown_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_calculate_metrics_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_detect_language_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_generate_summary_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_keywords_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_calculate_quality_handler = Mock(return_value=Mock(handle=Mock()))

        # Act - Llamar múltiples veces
        container.register_pipeline_handlers()
        container.register_pipeline_handlers()
        container.register_pipeline_handlers()

        # Assert - Verificar que se registraron los handlers
        # (el último registro sobrescribe los anteriores)
        assert len(mock_infra.mediator._handler_registry) == 10

        # Verificar que logger.info se llamó 3 veces
        assert mock_infra.logger.info.call_count == 3

    def test_scraping_pipeline_handlers_are_grouped_together(
        self, container, mock_infra
    ):
        """Debería registrar handlers de scraping pipeline juntos.

        **Requirements: 1.1**
        """
        from src.rss.article.app.commands.convert_article_to_markdown.command import (
            ConvertArticleToMarkdownCommand,
        )
        from src.rss.article.app.commands.extract_article_plaintext.command import (
            ExtractArticlePlaintextCommand,
        )
        from src.rss.article.app.commands.scrape_article_content.command import (
            ScrapeRssArticleContentCommand,
        )

        # Arrange - Mock handler getters
        container.get_run_scraping_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_run_processing_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_scrape_content_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_plaintext_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_convert_to_markdown_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_calculate_metrics_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_detect_language_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_generate_summary_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_keywords_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_calculate_quality_handler = Mock(return_value=Mock(handle=Mock()))

        # Act
        container.register_pipeline_handlers()

        # Assert - Verificar que handlers de scraping están en posiciones 2, 3, 4
        call_args_list = mock_infra.register_handler.call_args_list

        scraping_commands = [
            call_args_list[2][0][0],
            call_args_list[3][0][0],
            call_args_list[4][0][0],
        ]

        assert ScrapeRssArticleContentCommand in scraping_commands
        assert ExtractArticlePlaintextCommand in scraping_commands
        assert ConvertArticleToMarkdownCommand in scraping_commands

    def test_processing_pipeline_handlers_are_grouped_together(
        self, container, mock_infra
    ):
        """Debería registrar handlers de processing pipeline juntos.

        **Requirements: 1.1**
        """
        from src.rss.article.app.commands.calculate_article_metrics.command import (
            CalculateArticleMetricsCommand,
        )
        from src.rss.article.app.commands.calculate_article_quality.command import (
            CalculateArticleQualityCommand,
        )
        from src.rss.article.app.commands.detect_article_language.command import (
            DetectArticleLanguageCommand,
        )
        from src.rss.article.app.commands.extract_article_keywords.command import (
            ExtractArticleKeywordsCommand,
        )
        from src.rss.article.app.commands.generate_article_summary.command import (
            GenerateArticleSummaryCommand,
        )

        # Arrange - Mock handler getters
        container.get_run_scraping_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_run_processing_pipeline_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_scrape_content_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_plaintext_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_convert_to_markdown_handler = Mock(
            return_value=Mock(handle=Mock())
        )
        container.get_calculate_metrics_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_detect_language_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_generate_summary_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_extract_keywords_handler = Mock(return_value=Mock(handle=Mock()))
        container.get_calculate_quality_handler = Mock(return_value=Mock(handle=Mock()))

        # Act
        container.register_pipeline_handlers()

        # Assert - Verificar que handlers de processing están en posiciones 5-9
        call_args_list = mock_infra.register_handler.call_args_list

        processing_commands = [
            call_args_list[5][0][0],
            call_args_list[6][0][0],
            call_args_list[7][0][0],
            call_args_list[8][0][0],
            call_args_list[9][0][0],
        ]

        assert CalculateArticleMetricsCommand in processing_commands
        assert DetectArticleLanguageCommand in processing_commands
        assert GenerateArticleSummaryCommand in processing_commands
        assert ExtractArticleKeywordsCommand in processing_commands
        assert CalculateArticleQualityCommand in processing_commands
