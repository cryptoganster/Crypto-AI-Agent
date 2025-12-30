"""Property-based tests para ProcessingProcessManager usando Hypothesis.

Estos tests verifican propiedades universales que deben cumplirse
para todas las entradas válidas del ProcessingProcessManager.

Feature: refactor-scheduling-jobs
"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.app.process_managers.base_process_manager import ProcessingPipelineResult
from src.app.process_managers.processing_process_manager import (
    ProcessingProcessManager,
)
from src.domain.interfaces.queries.articles.get_articles_requiring_processing import (
    IGetArticlesRequiringProcessing,
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
# ESTRATEGIAS DE GENERACIÓN DE DATOS
# ============================================================================


def create_test_article() -> RssArticle:
    """Crea un artículo de prueba con valores válidos."""
    return RssArticle(
        title=RssArticleTitle("Test RssArticle"),
        url=RssArticleUrl(f"https://example.com/article/{uuid4()}"),
        source_id=RssFeedId(str(uuid4())),
        article_id=RssArticleId(str(uuid4())),
    )


# ============================================================================
# PROPERTY TESTS
# ============================================================================


class TestProcessingProcessManagerProperties:
    """Property-based tests para ProcessingProcessManager."""

    def create_mock_mediator_with_failure_indices(
        self, failure_indices: list[int]
    ) -> Mock:
        """Crea un mock del mediator que falla en índices específicos."""
        mediator = Mock(spec=IMediator)

        call_count = [0]  # Use list to allow mutation in nested function

        async def send_with_selective_failures(command):
            current_index = call_count[0]
            call_count[0] += 1

            # Determinar si este comando debe fallar
            should_fail = current_index in failure_indices

            if should_fail:
                # Simular fallo lanzando excepción
                raise Exception(f"Simulated failure at index {current_index}")

            result = Mock()
            result.success = True
            return result

        mediator.send = AsyncMock(side_effect=send_with_selective_failures)
        return mediator

    def create_mock_logger(self) -> Mock:
        """Crea un mock del logger."""
        logger = Mock(spec=ILogger)
        logger.bind.return_value = logger
        return logger

    def create_mock_query_adapter(
        self,
        metrics_articles=None,
        language_articles=None,
        summary_articles=None,
        keywords_articles=None,
        crypto_articles=None,
        quality_articles=None,
    ) -> Mock:
        """Crea un mock del query adapter con artículos específicos."""
        adapter = Mock(spec=IGetArticlesRequiringProcessing)
        adapter.get_without_metrics = AsyncMock(return_value=metrics_articles or [])
        adapter.get_without_language = AsyncMock(return_value=language_articles or [])
        adapter.get_without_summary = AsyncMock(return_value=summary_articles or [])
        adapter.get_without_keywords = AsyncMock(return_value=keywords_articles or [])
        adapter.get_without_crypto_coins = AsyncMock(return_value=crypto_articles or [])
        adapter.get_without_quality_score = AsyncMock(
            return_value=quality_articles or []
        )
        return adapter

    @given(
        article_count=st.integers(min_value=2, max_value=30),
        failure_indices=st.lists(
            st.integers(min_value=0, max_value=29),
            min_size=0,
            max_size=10,
            unique=True,
        ),
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_property_parallel_failure_isolation(
        self, article_count: int, failure_indices: list[int]
    ):
        """
        **Feature: refactor-scheduling-jobs, Property 9: Parallel failure isolation**
        **Validates: Requirements 12.3**

        Property: Cuando se procesan múltiples artículos y algunos comandos fallan,
        los fallos no deben afectar el procesamiento exitoso de otros comandos.

        Esta propiedad verifica que:
        - Los comandos que fallan se cuentan correctamente como "failed"
        - Los comandos exitosos se cuentan correctamente como "success"
        - El pipeline continúa procesando todos los artículos a pesar de fallos parciales
        - total = success + failed siempre se cumple
        - El pipeline completa exitosamente incluso con fallos parciales

        Nota: En este test, solo usamos la fase de metrics para simplificar.
        El principio se aplica a todas las fases del pipeline.
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        # Filtrar failure_indices que están fuera del rango
        valid_failure_indices = [idx for idx in failure_indices if idx < article_count]

        mediator = self.create_mock_mediator_with_failure_indices(valid_failure_indices)
        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(
            metrics_articles=articles,
            # Otras fases vacías para enfocarnos en metrics
            language_articles=[],
            summary_articles=[],
            keywords_articles=[],
            crypto_articles=[],
            quality_articles=[],
        )

        process_manager = ProcessingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Property: Pipeline completa exitosamente a pesar de fallos parciales
        assert (
            result.success is True
        ), "Pipeline should complete successfully even with partial failures"

        # Assert - Property: total = success + failed
        metrics_total = result.metrics.get("total", 0)
        metrics_success = result.metrics.get("success", 0)
        metrics_failed = result.metrics.get("failed", 0)

        assert metrics_total == metrics_success + metrics_failed, (
            f"Metrics: total ({metrics_total}) != success ({metrics_success}) + "
            f"failed ({metrics_failed})"
        )

        # Assert - Property: total debe ser igual al número de artículos procesados
        assert (
            metrics_total == article_count
        ), f"Metrics: total ({metrics_total}) != article_count ({article_count})"

        # Assert - Property: failed debe ser igual al número de failure_indices válidos
        expected_failures = len(valid_failure_indices)
        assert (
            metrics_failed == expected_failures
        ), f"Metrics: failed ({metrics_failed}) != expected_failures ({expected_failures})"

        # Assert - Property: success debe ser igual a total - failed
        expected_success = article_count - expected_failures
        assert (
            metrics_success == expected_success
        ), f"Metrics: success ({metrics_success}) != expected_success ({expected_success})"

        # Assert - Property: Fallos no detienen el procesamiento de otros artículos
        # Verificamos que se intentó procesar todos los artículos
        assert mediator.send.call_count == article_count, (
            f"Should attempt to process all {article_count} articles, "
            f"but only called send {mediator.send.call_count} times"
        )

        # Assert - Property: Contadores no negativos
        assert metrics_success >= 0, "Success count cannot be negative"
        assert metrics_failed >= 0, "Failed count cannot be negative"
        assert metrics_total >= 0, "Total count cannot be negative"

    @given(
        article_count=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_all_phases_isolated(self, article_count: int):
        """
        Property: Los fallos en una fase no deben afectar otras fases.

        Esta propiedad verifica que cada fase del pipeline es independiente:
        - Si metrics falla, language puede tener éxito
        - Si summary falla, keywords puede tener éxito
        - Cada fase mantiene sus propias estadísticas correctamente
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        # Configurar mediator para que falle solo en la primera fase (metrics)
        # Los primeros article_count comandos son de metrics y fallarán
        # Los siguientes comandos (otras fases) tendrán éxito
        failure_indices = list(range(article_count))  # Solo metrics falla

        mediator = self.create_mock_mediator_with_failure_indices(failure_indices)
        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(
            metrics_articles=articles,
            language_articles=articles,
            summary_articles=[],  # Vacío para simplificar
            keywords_articles=[],
            crypto_articles=[],
            quality_articles=[],
        )

        process_manager = ProcessingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Metrics debe tener todos los fallos
        assert result.metrics["failed"] == article_count
        assert result.metrics["success"] == 0
        assert result.metrics["total"] == article_count

        # Assert - Language debe tener todos los éxitos (no afectado por metrics)
        assert result.language["success"] == article_count
        assert result.language["failed"] == 0
        assert result.language["total"] == article_count

        # Assert - Pipeline completa exitosamente
        assert result.success is True

    @given(
        article_count=st.integers(min_value=1, max_value=25),
        failure_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_property_statistics_accuracy_all_phases(
        self, article_count: int, failure_rate: float
    ):
        """
        Property: Para cualquier ejecución del pipeline de processing,
        las estadísticas deben cumplir: total = success + failed en TODAS las fases.

        Esta propiedad extiende la verificación de estadísticas a las 6 fases
        del pipeline de processing.
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        # Crear mediator con tasa de fallos
        mediator = Mock(spec=IMediator)
        call_count = [0]

        async def send_with_failures(command):
            current = call_count[0]
            call_count[0] += 1

            # Determinar si este comando debe fallar
            should_fail = (current % 100) < (failure_rate * 100)

            if should_fail:
                raise Exception(f"Simulated failure at call {current}")

            result = Mock()
            result.success = True
            return result

        mediator.send = AsyncMock(side_effect=send_with_failures)

        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(
            metrics_articles=articles,
            language_articles=articles,
            summary_articles=articles,
            keywords_articles=articles,
            crypto_articles=[],  # Skip crypto for simplicity
            quality_articles=articles,
        )

        process_manager = ProcessingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Property: total = success + failed para cada fase
        phases = ["metrics", "language", "summary", "keywords", "quality"]

        for phase in phases:
            phase_stats = getattr(result, phase)
            total = phase_stats.get("total", 0)
            success = phase_stats.get("success", 0)
            failed = phase_stats.get("failed", 0)

            assert (
                total == success + failed
            ), f"{phase}: total ({total}) != success ({success}) + failed ({failed})"
            assert (
                total == article_count
            ), f"{phase}: total ({total}) != article_count ({article_count})"
            assert success >= 0, f"{phase}: success cannot be negative"
            assert failed >= 0, f"{phase}: failed cannot be negative"

        # Crypto coins (sin mediator calls, todos success)
        assert result.crypto_coins["total"] == 0
        assert result.crypto_coins["success"] == 0
        assert result.crypto_coins["failed"] == 0

    @given(
        article_count=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_no_articles_means_no_processing(self, article_count: int):
        """
        Property: Si no hay artículos para procesar en ninguna fase,
        todas las estadísticas deben ser cero.
        """
        # Arrange - Todas las fases vacías
        mediator = Mock(spec=IMediator)
        mediator.send = AsyncMock()

        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(
            metrics_articles=[],
            language_articles=[],
            summary_articles=[],
            keywords_articles=[],
            crypto_articles=[],
            quality_articles=[],
        )

        process_manager = ProcessingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Todas las fases deben tener estadísticas en cero
        phases = [
            "metrics",
            "language",
            "summary",
            "keywords",
            "crypto_coins",
            "quality",
        ]

        for phase in phases:
            phase_stats = getattr(result, phase)
            assert phase_stats["total"] == 0, f"{phase}: total should be 0"
            assert phase_stats["success"] == 0, f"{phase}: success should be 0"
            assert phase_stats["failed"] == 0, f"{phase}: failed should be 0"

        # Assert - Mediator no debe ser llamado
        assert (
            mediator.send.call_count == 0
        ), "Mediator should not be called when there are no articles"

        # Assert - Pipeline completa exitosamente
        assert result.success is True
