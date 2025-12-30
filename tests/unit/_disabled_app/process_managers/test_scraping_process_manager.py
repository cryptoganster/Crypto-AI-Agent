"""Tests unitarios para ScrapingProcessManager."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, call
from uuid import uuid4

import pytest

from src.app.process_managers.base_process_manager import ScrapingPipelineResult
from src.app.process_managers.scraping_process_manager import (
    ScrapingProcessManager,
)
from src.domain.interfaces.queries.articles.get_articles_requiring_processing import (
    IGetArticlesRequiringProcessing,
)
from src.rss.article.app.commands.convert_article_to_markdown.command import (
    ConvertArticleToMarkdownCommand,
)
from src.rss.article.app.commands.extract_article_plaintext.command import (
    ExtractArticlePlaintextCommand,
)
from src.rss.article.app.commands.scrape_article_content.command import (
    ScrapeRssArticleContentCommand,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.article.domain.value_objects.metadata import RssArticleMetadata
from src.rss.feed.domain.value_objects import RssFeedId
from src.shared.kernel.bus import IMediator
from src.shared.kernel.logger import ILogger


class TestScrapingProcessManager:
    """Tests para ScrapingProcessManager."""

    @pytest.fixture
    def mock_mediator(self) -> Mock:
        """Crea un mock del Mediator."""
        mediator = Mock(spec=IMediator)
        mediator.send = AsyncMock()
        return mediator

    @pytest.fixture
    def mock_query_adapter(self) -> Mock:
        """Crea un mock del Query Adapter."""
        adapter = Mock(spec=IGetArticlesRequiringProcessing)
        adapter.get_without_content_scrapped = AsyncMock(return_value=[])
        adapter.get_without_content_plaintext = AsyncMock(return_value=[])
        adapter.get_without_content_markdown = AsyncMock(return_value=[])
        return adapter

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
        mock_query_adapter: Mock,
        mock_logger: Mock,
    ) -> ScrapingProcessManager:
        """Crea una instancia de ScrapingProcessManager para testing."""
        return ScrapingProcessManager(
            mediator=mock_mediator,
            query_adapter=mock_query_adapter,
            logger=mock_logger,
        )

    def create_test_article(self, article_id: str = None) -> RssArticle:
        """Crea un artículo de prueba."""
        if article_id is None:
            article_id = str(uuid4())
        else:
            # Ensure article_id is a valid UUID
            article_id = str(uuid4())

        article = RssArticle(
            identity=RssArticleMetadata(
                article_id=RssArticleId(article_id),
                url=RssArticleUrl("https://example.com/article"),
                source_id=RssFeedId(str(uuid4())),
            ),
            metadata=RssArticleMetadata(
                title=RssArticleTitle("Test RssArticle"),
            ),
        )
        # Store the ID for later reference
        article._test_id = article_id
        return article

    @pytest.mark.asyncio
    async def test_execute_with_no_articles_returns_empty_stats(
        self,
        process_manager: ScrapingProcessManager,
        mock_query_adapter: Mock,
    ):
        """Debería retornar estadísticas vacías cuando no hay artículos."""
        # Arrange
        mock_query_adapter.get_without_content_scrapped.return_value = []
        mock_query_adapter.get_without_content_plaintext.return_value = []
        mock_query_adapter.get_without_content_markdown.return_value = []

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is True
        assert result.scraping == {"success": 0, "failed": 0, "total": 0}
        assert result.plaintext == {"success": 0, "failed": 0, "total": 0}
        assert result.markdown == {"success": 0, "failed": 0, "total": 0}

    @pytest.mark.asyncio
    async def test_execute_successful_scraping_phase(
        self,
        process_manager: ScrapingProcessManager,
        mock_mediator: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería ejecutar fase de scraping exitosamente."""
        # Arrange
        articles = [
            self.create_test_article("article-1"),
            self.create_test_article("article-2"),
            self.create_test_article("article-3"),
        ]
        mock_query_adapter.get_without_content_scrapped.return_value = articles
        mock_query_adapter.get_without_content_plaintext.return_value = []
        mock_query_adapter.get_without_content_markdown.return_value = []

        # Mock successful command results
        mock_result = Mock()
        mock_result.success = True
        mock_mediator.send.return_value = mock_result

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is True
        assert result.scraping["success"] == 3
        assert result.scraping["failed"] == 0
        assert result.scraping["total"] == 3
        assert mock_mediator.send.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_handles_partial_failures_in_scraping(
        self,
        process_manager: ScrapingProcessManager,
        mock_mediator: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería manejar fallos parciales en fase de scraping."""
        # Arrange
        articles = [
            self.create_test_article("article-1"),
            self.create_test_article("article-2"),
            self.create_test_article("article-3"),
        ]
        mock_query_adapter.get_without_content_scrapped.return_value = articles
        mock_query_adapter.get_without_content_plaintext.return_value = []
        mock_query_adapter.get_without_content_markdown.return_value = []

        # Mock mixed results: success, failure, success
        success_result = Mock()
        success_result.success = True

        failure_result = Mock()
        failure_result.success = False

        mock_mediator.send.side_effect = [
            success_result,
            failure_result,
            success_result,
        ]

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is True
        assert result.scraping["success"] == 2
        assert result.scraping["failed"] == 1
        assert result.scraping["total"] == 3

    @pytest.mark.asyncio
    async def test_execute_handles_exceptions_in_scraping(
        self,
        process_manager: ScrapingProcessManager,
        mock_mediator: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería manejar excepciones en fase de scraping."""
        # Arrange
        articles = [
            self.create_test_article("article-1"),
            self.create_test_article("article-2"),
        ]
        mock_query_adapter.get_without_content_scrapped.return_value = articles
        mock_query_adapter.get_without_content_plaintext.return_value = []
        mock_query_adapter.get_without_content_markdown.return_value = []

        # Mock exception on first call, success on second
        success_result = Mock()
        success_result.success = True

        mock_mediator.send.side_effect = [
            Exception("Network error"),
            success_result,
        ]

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is True
        assert result.scraping["success"] == 1
        assert result.scraping["failed"] == 1
        assert result.scraping["total"] == 2

    @pytest.mark.asyncio
    async def test_execute_accumulates_statistics_correctly(
        self,
        process_manager: ScrapingProcessManager,
        mock_mediator: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería acumular estadísticas correctamente (total = success + failed)."""
        # Arrange
        scraping_articles = [self.create_test_article(f"s-{i}") for i in range(10)]
        plaintext_articles = [self.create_test_article(f"p-{i}") for i in range(8)]
        markdown_articles = [self.create_test_article(f"m-{i}") for i in range(5)]

        mock_query_adapter.get_without_content_scrapped.return_value = scraping_articles
        mock_query_adapter.get_without_content_plaintext.return_value = (
            plaintext_articles
        )
        mock_query_adapter.get_without_content_markdown.return_value = markdown_articles

        # Mock results: 7 success, 3 failed for scraping
        # 6 success, 2 failed for plaintext
        # 4 success, 1 failed for markdown
        success_result = Mock()
        success_result.success = True
        failure_result = Mock()
        failure_result.success = False

        mock_mediator.send.side_effect = (
            [success_result] * 7
            + [failure_result] * 3  # scraping
            + [success_result] * 6
            + [failure_result] * 2  # plaintext
            + [success_result] * 4
            + [failure_result] * 1  # markdown
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is True

        # Scraping stats
        assert result.scraping["success"] == 7
        assert result.scraping["failed"] == 3
        assert result.scraping["total"] == 10
        assert (
            result.scraping["total"]
            == result.scraping["success"] + result.scraping["failed"]
        )

        # Plaintext stats
        assert result.plaintext["success"] == 6
        assert result.plaintext["failed"] == 2
        assert result.plaintext["total"] == 8
        assert (
            result.plaintext["total"]
            == result.plaintext["success"] + result.plaintext["failed"]
        )

        # Markdown stats
        assert result.markdown["success"] == 4
        assert result.markdown["failed"] == 1
        assert result.markdown["total"] == 5
        assert (
            result.markdown["total"]
            == result.markdown["success"] + result.markdown["failed"]
        )

    @pytest.mark.asyncio
    async def test_execute_uses_query_adapter_correctly(
        self,
        process_manager: ScrapingProcessManager,
        mock_query_adapter: Mock,
    ):
        """Debería usar query adapter correctamente para cada fase."""
        # Arrange
        mock_query_adapter.get_without_content_scrapped.return_value = []
        mock_query_adapter.get_without_content_plaintext.return_value = []
        mock_query_adapter.get_without_content_markdown.return_value = []

        # Act
        await process_manager.execute(limit=50)

        # Assert
        mock_query_adapter.get_without_content_scrapped.assert_called_once_with(
            limit=50
        )
        mock_query_adapter.get_without_content_plaintext.assert_called_once_with(
            limit=50
        )
        mock_query_adapter.get_without_content_markdown.assert_called_once_with(
            limit=50
        )

    @pytest.mark.asyncio
    async def test_execute_sends_correct_commands_via_mediator(
        self,
        process_manager: ScrapingProcessManager,
        mock_mediator: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería enviar comandos correctos vía mediator."""
        # Arrange
        article = self.create_test_article()
        article_id = str(article.identity_vo.article_id)

        mock_query_adapter.get_without_content_scrapped.return_value = [article]
        mock_query_adapter.get_without_content_plaintext.return_value = [article]
        mock_query_adapter.get_without_content_markdown.return_value = [article]

        success_result = Mock()
        success_result.success = True
        mock_mediator.send.return_value = success_result

        # Act
        await process_manager.execute(limit=100, force_rescrape=True)

        # Assert
        assert mock_mediator.send.call_count == 3

        # Verify scraping command
        scraping_call = mock_mediator.send.call_args_list[0]
        scraping_command = scraping_call[0][0]
        assert isinstance(scraping_command, ScrapeRssArticleContentCommand)
        assert scraping_command.article_id == article_id
        assert scraping_command.force_rescrape is True
        assert scraping_command.update_article is True
        assert scraping_command.timeout_seconds == 30
        assert scraping_command.use_smart_scraper is True

        # Verify plaintext command
        plaintext_call = mock_mediator.send.call_args_list[1]
        plaintext_command = plaintext_call[0][0]
        assert isinstance(plaintext_command, ExtractArticlePlaintextCommand)
        assert plaintext_command.article_id == article_id
        assert plaintext_command.override_existing is False

        # Verify markdown command
        markdown_call = mock_mediator.send.call_args_list[2]
        markdown_command = markdown_call[0][0]
        assert isinstance(markdown_command, ConvertArticleToMarkdownCommand)
        assert markdown_command.article_id == article_id

    @pytest.mark.asyncio
    async def test_execute_returns_structured_result(
        self,
        process_manager: ScrapingProcessManager,
        mock_query_adapter: Mock,
    ):
        """Debería retornar resultado estructurado con todos los campos."""
        # Arrange
        mock_query_adapter.get_without_content_scrapped.return_value = []
        mock_query_adapter.get_without_content_plaintext.return_value = []
        mock_query_adapter.get_without_content_markdown.return_value = []

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert isinstance(result, ScrapingPipelineResult)
        assert hasattr(result, "success")
        assert hasattr(result, "duration_seconds")
        assert hasattr(result, "execution_time")
        assert hasattr(result, "error")
        assert hasattr(result, "scraping")
        assert hasattr(result, "plaintext")
        assert hasattr(result, "markdown")
        assert result.success is True
        assert result.error is None
        assert isinstance(result.duration_seconds, float)
        assert isinstance(result.execution_time, str)

    @pytest.mark.asyncio
    async def test_execute_handles_critical_failure(
        self,
        process_manager: ScrapingProcessManager,
        mock_query_adapter: Mock,
    ):
        """Debería manejar fallo crítico y retornar resultado con error."""
        # Arrange
        mock_query_adapter.get_without_content_scrapped.side_effect = Exception(
            "Database connection failed"
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is False
        assert result.error == "Database connection failed"
        assert result.scraping == {}
        assert result.plaintext == {}
        assert result.markdown == {}

    @pytest.mark.asyncio
    async def test_execute_respects_limit_parameter(
        self,
        process_manager: ScrapingProcessManager,
        mock_query_adapter: Mock,
    ):
        """Debería respetar el parámetro limit en todas las fases."""
        # Arrange
        mock_query_adapter.get_without_content_scrapped.return_value = []
        mock_query_adapter.get_without_content_plaintext.return_value = []
        mock_query_adapter.get_without_content_markdown.return_value = []

        # Act
        await process_manager.execute(limit=25)

        # Assert
        mock_query_adapter.get_without_content_scrapped.assert_called_once_with(
            limit=25
        )
        mock_query_adapter.get_without_content_plaintext.assert_called_once_with(
            limit=25
        )
        mock_query_adapter.get_without_content_markdown.assert_called_once_with(
            limit=25
        )

    @pytest.mark.asyncio
    async def test_execute_logs_phase_start_and_complete(
        self,
        process_manager: ScrapingProcessManager,
        mock_logger: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería loggear inicio y completado de cada fase."""
        # Arrange
        mock_query_adapter.get_without_content_scrapped.return_value = []
        mock_query_adapter.get_without_content_plaintext.return_value = []
        mock_query_adapter.get_without_content_markdown.return_value = []

        # Act
        await process_manager.execute(limit=100)

        # Assert
        # Verificar que se llamó info múltiples veces (inicio de pipeline + fases)
        assert mock_logger.info.call_count >= 6  # 3 starts + 3 completes

        # Verificar que se llamó success al final
        mock_logger.success.assert_called_once()
