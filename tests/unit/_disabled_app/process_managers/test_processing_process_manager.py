"""Tests unitarios para ProcessingProcessManager."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.app.process_managers.base_process_manager import ProcessingPipelineResult
from src.app.process_managers.processing_process_manager import (
    ProcessingProcessManager,
)
from src.domain.interfaces.queries.articles.get_articles_requiring_processing import (
    IGetArticlesRequiringProcessing,
)
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


class TestProcessingProcessManager:
    """Tests para ProcessingProcessManager."""

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
        adapter.get_without_metrics = AsyncMock(return_value=[])
        adapter.get_without_language = AsyncMock(return_value=[])
        adapter.get_without_summary = AsyncMock(return_value=[])
        adapter.get_without_keywords = AsyncMock(return_value=[])
        adapter.get_without_quality_score = AsyncMock(return_value=[])
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
    ) -> ProcessingProcessManager:
        """Crea una instancia de ProcessingProcessManager para testing."""
        return ProcessingProcessManager(
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
        process_manager: ProcessingProcessManager,
        mock_query_adapter: Mock,
    ):
        """Debería retornar estadísticas vacías cuando no hay artículos."""
        # Arrange
        mock_query_adapter.get_without_metrics.return_value = []
        mock_query_adapter.get_without_language.return_value = []
        mock_query_adapter.get_without_summary.return_value = []
        mock_query_adapter.get_without_keywords.return_value = []
        mock_query_adapter.get_without_quality_score.return_value = []

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is True
        assert result.metrics == {"success": 0, "failed": 0, "total": 0}
        assert result.language == {"success": 0, "failed": 0, "total": 0}
        assert result.summary == {"success": 0, "failed": 0, "total": 0}
        assert result.keywords == {"success": 0, "failed": 0, "total": 0}
        assert result.quality == {"success": 0, "failed": 0, "total": 0}

    @pytest.mark.asyncio
    async def test_execute_successful_metrics_phase(
        self,
        process_manager: ProcessingProcessManager,
        mock_mediator: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería ejecutar fase de metrics exitosamente."""
        # Arrange
        articles = [
            self.create_test_article("article-1"),
            self.create_test_article("article-2"),
            self.create_test_article("article-3"),
        ]
        mock_query_adapter.get_without_metrics.return_value = articles

        # Mock successful command results
        mock_result = Mock()
        mock_result.success = True
        mock_mediator.send.return_value = mock_result

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is True
        assert result.metrics["success"] == 3
        assert result.metrics["failed"] == 0
        assert result.metrics["total"] == 3
        assert mock_mediator.send.call_count >= 3

    @pytest.mark.asyncio
    async def test_execute_handles_partial_failures_in_language(
        self,
        process_manager: ProcessingProcessManager,
        mock_mediator: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería manejar fallos parciales en fase de language."""
        # Arrange
        articles = [
            self.create_test_article("article-1"),
            self.create_test_article("article-2"),
            self.create_test_article("article-3"),
        ]
        mock_query_adapter.get_without_language.return_value = articles

        # Mock mixed results: success, failure, success
        success_result = Mock()
        success_result.success = True

        failure_result = Mock()
        failure_result.success = False

        # First call for metrics (no articles), then language phase
        mock_mediator.send.side_effect = [
            success_result,
            failure_result,
            success_result,
        ]

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is True
        assert result.language["success"] == 2
        assert result.language["failed"] == 1
        assert result.language["total"] == 3

    @pytest.mark.asyncio
    async def test_execute_handles_exceptions_in_summary(
        self,
        process_manager: ProcessingProcessManager,
        mock_mediator: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería manejar excepciones en fase de summary."""
        # Arrange
        articles = [
            self.create_test_article("article-1"),
            self.create_test_article("article-2"),
        ]
        mock_query_adapter.get_without_summary.return_value = articles

        # Mock exception on first call, success on second
        success_result = Mock()
        success_result.success = True

        mock_mediator.send.side_effect = [
            Exception("AI service unavailable"),
            success_result,
        ]

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is True
        assert result.summary["success"] == 1
        assert result.summary["failed"] == 1
        assert result.summary["total"] == 2

    @pytest.mark.asyncio
    async def test_execute_accumulates_statistics_correctly(
        self,
        process_manager: ProcessingProcessManager,
        mock_mediator: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería acumular estadísticas correctamente (total = success + failed)."""
        # Arrange
        metrics_articles = [self.create_test_article(f"m-{i}") for i in range(10)]
        language_articles = [self.create_test_article(f"l-{i}") for i in range(8)]
        summary_articles = [self.create_test_article(f"s-{i}") for i in range(5)]
        keywords_articles = [self.create_test_article(f"k-{i}") for i in range(6)]
        quality_articles = [self.create_test_article(f"q-{i}") for i in range(7)]

        mock_query_adapter.get_without_metrics.return_value = metrics_articles
        mock_query_adapter.get_without_language.return_value = language_articles
        mock_query_adapter.get_without_summary.return_value = summary_articles
        mock_query_adapter.get_without_keywords.return_value = keywords_articles
        mock_query_adapter.get_without_quality_score.return_value = quality_articles

        # Mock results with different success/failure patterns
        success_result = Mock()
        success_result.success = True
        failure_result = Mock()
        failure_result.success = False

        mock_mediator.send.side_effect = (
            [success_result] * 7
            + [failure_result] * 3  # metrics: 7 success, 3 failed
            + [success_result] * 6
            + [failure_result] * 2  # language: 6 success, 2 failed
            + [success_result] * 4
            + [failure_result] * 1  # summary: 4 success, 1 failed
            + [success_result] * 5
            + [failure_result] * 1  # keywords: 5 success, 1 failed
            + [success_result] * 5
            + [failure_result] * 2  # quality: 5 success, 2 failed
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is True

        # Metrics stats
        assert result.metrics["success"] == 7
        assert result.metrics["failed"] == 3
        assert result.metrics["total"] == 10
        assert (
            result.metrics["total"]
            == result.metrics["success"] + result.metrics["failed"]
        )

        # Language stats
        assert result.language["success"] == 6
        assert result.language["failed"] == 2
        assert result.language["total"] == 8
        assert (
            result.language["total"]
            == result.language["success"] + result.language["failed"]
        )

        # Summary stats
        assert result.summary["success"] == 4
        assert result.summary["failed"] == 1
        assert result.summary["total"] == 5
        assert (
            result.summary["total"]
            == result.summary["success"] + result.summary["failed"]
        )

        # Keywords stats
        assert result.keywords["success"] == 5
        assert result.keywords["failed"] == 1
        assert result.keywords["total"] == 6
        assert (
            result.keywords["total"]
            == result.keywords["success"] + result.keywords["failed"]
        )

        # Quality stats
        assert result.quality["success"] == 5
        assert result.quality["failed"] == 2
        assert result.quality["total"] == 7
        assert (
            result.quality["total"]
            == result.quality["success"] + result.quality["failed"]
        )

    @pytest.mark.asyncio
    async def test_execute_uses_query_adapter_correctly(
        self,
        process_manager: ProcessingProcessManager,
        mock_query_adapter: Mock,
    ):
        """Debería usar query adapter correctamente para cada fase."""
        # Arrange
        mock_query_adapter.get_without_metrics.return_value = []
        mock_query_adapter.get_without_language.return_value = []
        mock_query_adapter.get_without_summary.return_value = []
        mock_query_adapter.get_without_keywords.return_value = []
        mock_query_adapter.get_without_quality_score.return_value = []

        # Act
        await process_manager.execute(limit=50)

        # Assert
        mock_query_adapter.get_without_metrics.assert_called_once_with(limit=50)
        mock_query_adapter.get_without_language.assert_called_once_with(limit=50)
        mock_query_adapter.get_without_summary.assert_called_once_with(limit=50)
        mock_query_adapter.get_without_keywords.assert_called_once_with(limit=50)
        mock_query_adapter.get_without_quality_score.assert_called_once_with(limit=50)

    @pytest.mark.asyncio
    async def test_execute_sends_correct_commands_via_mediator(
        self,
        process_manager: ProcessingProcessManager,
        mock_mediator: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería enviar comandos correctos vía mediator."""
        # Arrange
        article = self.create_test_article()
        article_id = str(article.identity_vo.article_id)

        mock_query_adapter.get_without_metrics.return_value = [article]
        mock_query_adapter.get_without_language.return_value = [article]
        mock_query_adapter.get_without_summary.return_value = [article]
        mock_query_adapter.get_without_keywords.return_value = [article]
        mock_query_adapter.get_without_quality_score.return_value = [article]

        success_result = Mock()
        success_result.success = True
        mock_mediator.send.return_value = success_result

        # Act
        await process_manager.execute(limit=100)

        # Assert
        assert mock_mediator.send.call_count == 5  # 6 phases - 1 (crypto skipped)

        # Verify metrics command
        metrics_call = mock_mediator.send.call_args_list[0]
        metrics_command = metrics_call[0][0]
        assert isinstance(metrics_command, CalculateArticleMetricsCommand)
        assert metrics_command.article_id == article_id

        # Verify language command
        language_call = mock_mediator.send.call_args_list[1]
        language_command = language_call[0][0]
        assert isinstance(language_command, DetectArticleLanguageCommand)
        assert language_command.article_id == article_id

        # Verify summary command
        summary_call = mock_mediator.send.call_args_list[2]
        summary_command = summary_call[0][0]
        assert isinstance(summary_command, GenerateArticleSummaryCommand)
        assert summary_command.article_id == article_id

        # Verify keywords command
        keywords_call = mock_mediator.send.call_args_list[3]
        keywords_command = keywords_call[0][0]
        assert isinstance(keywords_command, ExtractArticleKeywordsCommand)
        assert keywords_command.article_id == article_id

        # Verify quality command
        quality_call = mock_mediator.send.call_args_list[4]
        quality_command = quality_call[0][0]
        assert isinstance(quality_command, CalculateArticleQualityCommand)
        assert quality_command.article_id == article_id

    @pytest.mark.asyncio
    async def test_execute_returns_structured_result(
        self,
        process_manager: ProcessingProcessManager,
        mock_query_adapter: Mock,
    ):
        """Debería retornar resultado estructurado con todos los campos."""
        # Arrange
        mock_query_adapter.get_without_metrics.return_value = []
        mock_query_adapter.get_without_language.return_value = []
        mock_query_adapter.get_without_summary.return_value = []
        mock_query_adapter.get_without_keywords.return_value = []
        mock_query_adapter.get_without_quality_score.return_value = []

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert isinstance(result, ProcessingPipelineResult)
        assert hasattr(result, "success")
        assert hasattr(result, "duration_seconds")
        assert hasattr(result, "execution_time")
        assert hasattr(result, "error")
        assert hasattr(result, "metrics")
        assert hasattr(result, "language")
        assert hasattr(result, "summary")
        assert hasattr(result, "keywords")
        assert hasattr(result, "quality")
        assert result.success is True
        assert result.error is None
        assert isinstance(result.duration_seconds, float)
        assert isinstance(result.execution_time, str)

    @pytest.mark.asyncio
    async def test_execute_handles_critical_failure(
        self,
        process_manager: ProcessingProcessManager,
        mock_query_adapter: Mock,
    ):
        """Debería manejar fallo crítico y retornar resultado con error."""
        # Arrange
        mock_query_adapter.get_without_metrics.side_effect = Exception(
            "Database connection failed"
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert
        assert result.success is False
        assert result.error == "Database connection failed"
        assert result.metrics == {}
        assert result.language == {}
        assert result.summary == {}
        assert result.keywords == {}
        assert result.quality == {}

    @pytest.mark.asyncio
    async def test_execute_respects_limit_parameter(
        self,
        process_manager: ProcessingProcessManager,
        mock_query_adapter: Mock,
    ):
        """Debería respetar el parámetro limit en todas las fases."""
        # Arrange
        mock_query_adapter.get_without_metrics.return_value = []
        mock_query_adapter.get_without_language.return_value = []
        mock_query_adapter.get_without_summary.return_value = []
        mock_query_adapter.get_without_keywords.return_value = []
        mock_query_adapter.get_without_quality_score.return_value = []

        # Act
        await process_manager.execute(limit=25)

        # Assert
        mock_query_adapter.get_without_metrics.assert_called_once_with(limit=25)
        mock_query_adapter.get_without_language.assert_called_once_with(limit=25)
        mock_query_adapter.get_without_summary.assert_called_once_with(limit=25)
        mock_query_adapter.get_without_keywords.assert_called_once_with(limit=25)
        mock_query_adapter.get_without_quality_score.assert_called_once_with(limit=25)

    @pytest.mark.asyncio
    async def test_execute_logs_phase_start_and_complete(
        self,
        process_manager: ProcessingProcessManager,
        mock_logger: Mock,
        mock_query_adapter: Mock,
    ):
        """Debería loggear inicio y completado de cada fase."""
        # Arrange
        mock_query_adapter.get_without_metrics.return_value = []
        mock_query_adapter.get_without_language.return_value = []
        mock_query_adapter.get_without_summary.return_value = []
        mock_query_adapter.get_without_keywords.return_value = []
        mock_query_adapter.get_without_quality_score.return_value = []

        # Act
        await process_manager.execute(limit=100)

        # Assert
        # Verificar que se llamó info múltiples veces (inicio de pipeline + fases)
        assert mock_logger.info.call_count >= 10  # 5 starts + 5 completes

        # Verificar que se llamó success al final
        mock_logger.success.assert_called_once()
