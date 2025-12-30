"""Property-based tests para verificar resultados estructurados de Process Managers.

Estos tests verifican que todos los Process Managers retornan resultados
con la estructura correcta y todos los campos requeridos.

Feature: refactor-scheduling-jobs
"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.app.process_managers.base_process_manager import (
    FetchPipelineResult,
    ProcessingPipelineResult,
    ProcessResult,
    ScrapingPipelineResult,
)
from src.app.process_managers.fetch_process_manager import (
    FetchProcessManager,
)
from src.app.process_managers.processing_process_manager import (
    ProcessingProcessManager,
)
from src.app.process_managers.scraping_process_manager import (
    ScrapingProcessManager,
)
from src.domain.interfaces.queries.articles.get_articles_requiring_processing import (
    IGetArticlesRequiringProcessing,
)
from src.domain.interfaces.queries.sources.get_sources_list import (
    IGetSourcesList,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.feed.domain.value_objects import RssFeedId
from src.shared.kernel.bus import IMediator
from src.shared.kernel.logger import ILogger

# ============================================================================
# HELPERS
# ============================================================================


def create_test_article() -> RssArticle:
    """Crea un artículo de prueba con valores válidos."""
    return RssArticle(
        title=RssArticleTitle("Test RssArticle"),
        url=RssArticleUrl(f"https://example.com/article/{uuid4()}"),
        source_id=RssFeedId(str(uuid4())),
        article_id=RssArticleId(str(uuid4())),
    )


def create_test_source_dict() -> dict:
    """Crea un diccionario de source de prueba con valores válidos."""
    return {
        "id": str(uuid4()),
        "name": "Test RssFeed",
        "url": f"https://example.com/feed/{uuid4()}",
    }


def create_mock_mediator(success_rate: float = 1.0) -> Mock:
    """Crea un mock del mediator con tasa de éxito configurable."""
    mediator = Mock(spec=IMediator)

    call_count = [0]

    async def send_with_success_rate(command):
        current = call_count[0]
        call_count[0] += 1

        should_succeed = (current % 100) < (success_rate * 100)

        # Para FetchProcessManager, retornar un resultado con success=False
        # en lugar de lanzar excepción
        result = Mock()
        result.success = should_succeed
        result.session_id = f"session-{current}" if should_succeed else None
        result.articles_fetched = 0
        result.error = (
            None if should_succeed else f"Simulated failure at call {current}"
        )

        return result

    mediator.send = AsyncMock(side_effect=send_with_success_rate)
    return mediator


def create_mock_logger() -> Mock:
    """Crea un mock del logger."""
    logger = Mock(spec=ILogger)
    logger.bind.return_value = logger
    return logger


# ============================================================================
# PROPERTY TESTS
# ============================================================================


class TestStructuredResultsProperty:
    """Property-based tests para verificar resultados estructurados."""

    @given(
        article_count=st.integers(min_value=0, max_value=30),
        success_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_property_scraping_process_manager_returns_structured_result(
        self, article_count: int, success_rate: float
    ):
        """
        **Feature: refactor-scheduling-jobs, Property 3: Process Manager returns structured result**
        **Validates: Requirements 2.4**

        Property: Para cualquier ejecución del ScrapingProcessManager,
        el resultado debe contener todos los campos requeridos:
        - success (bool)
        - duration_seconds (float)
        - execution_time (str)
        - error (str | None)
        - scraping (Dict[str, int])
        - plaintext (Dict[str, int])
        - markdown (Dict[str, int])

        Además, cada diccionario de fase debe contener:
        - success (int)
        - failed (int)
        - total (int)
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        mediator = create_mock_mediator(success_rate)
        logger = create_mock_logger()

        query_adapter = Mock(spec=IGetArticlesRequiringProcessing)
        query_adapter.get_without_content_scrapped = AsyncMock(return_value=articles)
        query_adapter.get_without_content_plaintext = AsyncMock(return_value=articles)
        query_adapter.get_without_content_markdown = AsyncMock(return_value=articles)

        process_manager = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Property: Resultado debe ser instancia de ScrapingPipelineResult
        assert isinstance(
            result, ScrapingPipelineResult
        ), f"Result should be ScrapingPipelineResult, got {type(result)}"

        # Assert - Property: Campos base requeridos (de ProcessResult)
        assert hasattr(result, "success"), "Result must have 'success' field"
        assert isinstance(result.success, bool), "success must be bool"

        assert hasattr(
            result, "duration_seconds"
        ), "Result must have 'duration_seconds' field"
        assert isinstance(
            result.duration_seconds, (int, float)
        ), "duration_seconds must be numeric"
        assert result.duration_seconds >= 0, "duration_seconds must be non-negative"

        assert hasattr(
            result, "execution_time"
        ), "Result must have 'execution_time' field"
        assert isinstance(result.execution_time, str), "execution_time must be str"
        assert len(result.execution_time) > 0, "execution_time must not be empty"

        assert hasattr(result, "error"), "Result must have 'error' field"
        assert result.error is None or isinstance(
            result.error, str
        ), "error must be None or str"

        # Assert - Property: Campos específicos de ScrapingPipelineResult
        assert hasattr(result, "scraping"), "Result must have 'scraping' field"
        assert isinstance(result.scraping, dict), "scraping must be dict"

        assert hasattr(result, "plaintext"), "Result must have 'plaintext' field"
        assert isinstance(result.plaintext, dict), "plaintext must be dict"

        assert hasattr(result, "markdown"), "Result must have 'markdown' field"
        assert isinstance(result.markdown, dict), "markdown must be dict"

        # Assert - Property: Cada fase debe tener campos requeridos
        for phase_name in ["scraping", "plaintext", "markdown"]:
            phase_stats = getattr(result, phase_name)

            assert "success" in phase_stats, f"{phase_name} must have 'success' key"
            assert isinstance(
                phase_stats["success"], int
            ), f"{phase_name}.success must be int"
            assert (
                phase_stats["success"] >= 0
            ), f"{phase_name}.success must be non-negative"

            assert "failed" in phase_stats, f"{phase_name} must have 'failed' key"
            assert isinstance(
                phase_stats["failed"], int
            ), f"{phase_name}.failed must be int"
            assert (
                phase_stats["failed"] >= 0
            ), f"{phase_name}.failed must be non-negative"

            assert "total" in phase_stats, f"{phase_name} must have 'total' key"
            assert isinstance(
                phase_stats["total"], int
            ), f"{phase_name}.total must be int"
            assert phase_stats["total"] >= 0, f"{phase_name}.total must be non-negative"

            # Assert - Property: total = success + failed
            assert (
                phase_stats["total"] == phase_stats["success"] + phase_stats["failed"]
            ), f"{phase_name}: total must equal success + failed"

    @given(
        article_count=st.integers(min_value=0, max_value=30),
        success_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_property_processing_process_manager_returns_structured_result(
        self, article_count: int, success_rate: float
    ):
        """
        **Feature: refactor-scheduling-jobs, Property 3: Process Manager returns structured result**
        **Validates: Requirements 2.4**

        Property: Para cualquier ejecución del ProcessingProcessManager,
        el resultado debe contener todos los campos requeridos:
        - success (bool)
        - duration_seconds (float)
        - execution_time (str)
        - error (str | None)
        - metrics (Dict[str, int])
        - language (Dict[str, int])
        - summary (Dict[str, int])
        - keywords (Dict[str, int])
        - crypto_coins (Dict[str, int])
        - quality (Dict[str, int])
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        mediator = create_mock_mediator(success_rate)
        logger = create_mock_logger()

        query_adapter = Mock(spec=IGetArticlesRequiringProcessing)
        query_adapter.get_without_metrics = AsyncMock(return_value=articles)
        query_adapter.get_without_language = AsyncMock(return_value=articles)
        query_adapter.get_without_summary = AsyncMock(return_value=articles)
        query_adapter.get_without_keywords = AsyncMock(return_value=articles)
        query_adapter.get_without_crypto_coins = AsyncMock(return_value=articles)
        query_adapter.get_without_quality_score = AsyncMock(return_value=articles)

        process_manager = ProcessingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Property: Resultado debe ser instancia de ProcessingPipelineResult
        assert isinstance(
            result, ProcessingPipelineResult
        ), f"Result should be ProcessingPipelineResult, got {type(result)}"

        # Assert - Property: Campos base requeridos (de ProcessResult)
        assert hasattr(result, "success"), "Result must have 'success' field"
        assert isinstance(result.success, bool), "success must be bool"

        assert hasattr(
            result, "duration_seconds"
        ), "Result must have 'duration_seconds' field"
        assert isinstance(
            result.duration_seconds, (int, float)
        ), "duration_seconds must be numeric"
        assert result.duration_seconds >= 0, "duration_seconds must be non-negative"

        assert hasattr(
            result, "execution_time"
        ), "Result must have 'execution_time' field"
        assert isinstance(result.execution_time, str), "execution_time must be str"
        assert len(result.execution_time) > 0, "execution_time must not be empty"

        assert hasattr(result, "error"), "Result must have 'error' field"
        assert result.error is None or isinstance(
            result.error, str
        ), "error must be None or str"

        # Assert - Property: Campos específicos de ProcessingPipelineResult
        phases = [
            "metrics",
            "language",
            "summary",
            "keywords",
            "crypto_coins",
            "quality",
        ]

        for phase_name in phases:
            assert hasattr(result, phase_name), f"Result must have '{phase_name}' field"
            phase_stats = getattr(result, phase_name)
            assert isinstance(phase_stats, dict), f"{phase_name} must be dict"

            # Assert - Property: Cada fase debe tener campos requeridos
            assert "success" in phase_stats, f"{phase_name} must have 'success' key"
            assert isinstance(
                phase_stats["success"], int
            ), f"{phase_name}.success must be int"
            assert (
                phase_stats["success"] >= 0
            ), f"{phase_name}.success must be non-negative"

            assert "failed" in phase_stats, f"{phase_name} must have 'failed' key"
            assert isinstance(
                phase_stats["failed"], int
            ), f"{phase_name}.failed must be int"
            assert (
                phase_stats["failed"] >= 0
            ), f"{phase_name}.failed must be non-negative"

            assert "total" in phase_stats, f"{phase_name} must have 'total' key"
            assert isinstance(
                phase_stats["total"], int
            ), f"{phase_name}.total must be int"
            assert phase_stats["total"] >= 0, f"{phase_name}.total must be non-negative"

            # Assert - Property: total = success + failed
            assert (
                phase_stats["total"] == phase_stats["success"] + phase_stats["failed"]
            ), f"{phase_name}: total must equal success + failed"

    @given(
        source_count=st.integers(min_value=0, max_value=20),
        success_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_property_fetch_process_manager_returns_structured_result(
        self, source_count: int, success_rate: float
    ):
        """
        **Feature: refactor-scheduling-jobs, Property 3: Process Manager returns structured result**
        **Validates: Requirements 2.4**

        Property: Para cualquier ejecución del FetchProcessManager,
        el resultado debe contener todos los campos requeridos:
        - success (bool)
        - duration_seconds (float)
        - execution_time (str)
        - error (str | None)
        - sources_processed (int)
        - sources_success (int)
        - sources_failed (int)
        - total_articles_fetched (int)
        - fetch_sessions (list[str])
        """
        # Arrange
        sources = [create_test_source_dict() for _ in range(source_count)]

        mediator = create_mock_mediator(success_rate)
        logger = create_mock_logger()

        query_adapter = Mock(spec=IGetSourcesList)
        query_adapter.get_active = AsyncMock(return_value=sources)

        process_manager = FetchProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(source_ids=None, max_concurrent=5)

        # Assert - Property: Resultado debe ser instancia de FetchPipelineResult
        assert isinstance(
            result, FetchPipelineResult
        ), f"Result should be FetchPipelineResult, got {type(result)}"

        # Assert - Property: Campos base requeridos (de ProcessResult)
        assert hasattr(result, "success"), "Result must have 'success' field"
        assert isinstance(result.success, bool), "success must be bool"

        assert hasattr(
            result, "duration_seconds"
        ), "Result must have 'duration_seconds' field"
        assert isinstance(
            result.duration_seconds, (int, float)
        ), "duration_seconds must be numeric"
        assert result.duration_seconds >= 0, "duration_seconds must be non-negative"

        assert hasattr(
            result, "execution_time"
        ), "Result must have 'execution_time' field"
        assert isinstance(result.execution_time, str), "execution_time must be str"
        assert len(result.execution_time) > 0, "execution_time must not be empty"

        assert hasattr(result, "error"), "Result must have 'error' field"
        assert result.error is None or isinstance(
            result.error, str
        ), "error must be None or str"

        # Assert - Property: Campos específicos de FetchPipelineResult
        assert hasattr(
            result, "sources_processed"
        ), "Result must have 'sources_processed' field"
        assert isinstance(
            result.sources_processed, int
        ), "sources_processed must be int"
        assert result.sources_processed >= 0, "sources_processed must be non-negative"

        assert hasattr(
            result, "sources_success"
        ), "Result must have 'sources_success' field"
        assert isinstance(result.sources_success, int), "sources_success must be int"
        assert result.sources_success >= 0, "sources_success must be non-negative"

        assert hasattr(
            result, "sources_failed"
        ), "Result must have 'sources_failed' field"
        assert isinstance(result.sources_failed, int), "sources_failed must be int"
        assert result.sources_failed >= 0, "sources_failed must be non-negative"

        assert hasattr(
            result, "total_articles_fetched"
        ), "Result must have 'total_articles_fetched' field"
        assert isinstance(
            result.total_articles_fetched, int
        ), "total_articles_fetched must be int"
        assert (
            result.total_articles_fetched >= 0
        ), "total_articles_fetched must be non-negative"

        assert hasattr(
            result, "fetch_sessions"
        ), "Result must have 'fetch_sessions' field"
        assert isinstance(result.fetch_sessions, list), "fetch_sessions must be list"

        # Assert - Property: sources_processed = sources_success + sources_failed
        assert (
            result.sources_processed == result.sources_success + result.sources_failed
        ), (
            f"sources_processed ({result.sources_processed}) must equal "
            f"sources_success ({result.sources_success}) + sources_failed ({result.sources_failed})"
        )

        # Assert - Property: sources_processed debe ser igual al número de sources
        assert (
            result.sources_processed == source_count
        ), f"sources_processed ({result.sources_processed}) must equal source_count ({source_count})"

    @given(
        article_count=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_result_structure_consistent_across_executions(
        self, article_count: int
    ):
        """
        Property: La estructura del resultado debe ser consistente
        independientemente del número de artículos procesados o el resultado
        de la ejecución (éxito/fallo).

        Esta propiedad verifica que:
        - Todos los campos requeridos están presentes siempre
        - Los tipos de datos son consistentes
        - La estructura no cambia entre ejecuciones
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        mediator = create_mock_mediator(1.0)  # Todos exitosos
        logger = create_mock_logger()

        query_adapter = Mock(spec=IGetArticlesRequiringProcessing)
        query_adapter.get_without_content_scrapped = AsyncMock(return_value=articles)
        query_adapter.get_without_content_plaintext = AsyncMock(return_value=articles)
        query_adapter.get_without_content_markdown = AsyncMock(return_value=articles)

        process_manager = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act - Primera ejecución
        result1 = await process_manager.execute(limit=100)

        # Act - Segunda ejecución (con diferentes artículos)
        new_articles = [create_test_article() for _ in range(article_count + 5)]
        query_adapter.get_without_content_scrapped = AsyncMock(
            return_value=new_articles
        )
        query_adapter.get_without_content_plaintext = AsyncMock(
            return_value=new_articles
        )
        query_adapter.get_without_content_markdown = AsyncMock(
            return_value=new_articles
        )

        result2 = await process_manager.execute(limit=100)

        # Assert - Property: Ambos resultados tienen la misma estructura
        assert type(result1) == type(result2), "Results must have same type"

        # Assert - Property: Ambos tienen los mismos campos
        result1_fields = set(vars(result1).keys())
        result2_fields = set(vars(result2).keys())
        assert result1_fields == result2_fields, (
            f"Results must have same fields. "
            f"result1: {result1_fields}, result2: {result2_fields}"
        )

        # Assert - Property: Los tipos de los campos son consistentes
        for field_name in result1_fields:
            value1 = getattr(result1, field_name)
            value2 = getattr(result2, field_name)
            assert type(value1) == type(value2), (
                f"Field '{field_name}' must have consistent type. "
                f"result1: {type(value1)}, result2: {type(value2)}"
            )
