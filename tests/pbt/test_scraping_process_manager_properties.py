"""Property-based tests para ScrapingProcessManager usando Hypothesis.

Estos tests verifican propiedades universales que deben cumplirse
para todas las entradas válidas del ScrapingProcessManager.

Feature: refactor-scheduling-jobs
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.app.process_managers.base_process_manager import ScrapingPipelineResult
from src.app.process_managers.scraping_process_manager import (
    ScrapingProcessManager,
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


@st.composite
def article_list_strategy(draw, min_size=0, max_size=50):
    """Genera listas de artículos."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return [create_test_article() for _ in range(size)]


@st.composite
def failure_rate_strategy(draw):
    """Genera tasa de fallos entre 0.0 y 1.0."""
    return draw(st.floats(min_value=0.0, max_value=1.0))


# ============================================================================
# PROPERTY TESTS
# ============================================================================


class TestScrapingProcessManagerProperties:
    """Property-based tests para ScrapingProcessManager."""

    def create_mock_mediator_with_failure_rate(self, failure_rate: float) -> Mock:
        """Crea un mock del mediator que falla según la tasa especificada."""
        mediator = Mock(spec=IMediator)

        call_count = 0

        async def send_with_failures(command):
            nonlocal call_count
            call_count += 1

            # Determinar si este comando debe fallar
            # Usamos un patrón determinístico basado en el contador
            should_fail = (call_count % 100) < (failure_rate * 100)

            result = Mock()
            result.success = not should_fail
            return result

        mediator.send = AsyncMock(side_effect=send_with_failures)
        return mediator

    def create_mock_logger(self) -> Mock:
        """Crea un mock del logger."""
        logger = Mock(spec=ILogger)
        logger.bind.return_value = logger
        return logger

    def create_mock_query_adapter(
        self,
        scraping_articles=None,
        plaintext_articles=None,
        markdown_articles=None,
    ) -> Mock:
        """Crea un mock del query adapter con artículos específicos."""
        adapter = Mock(spec=IGetArticlesRequiringProcessing)
        adapter.get_without_content_scrapped = AsyncMock(
            return_value=scraping_articles or []
        )
        adapter.get_without_content_plaintext = AsyncMock(
            return_value=plaintext_articles or []
        )
        adapter.get_without_content_markdown = AsyncMock(
            return_value=markdown_articles or []
        )
        return adapter

    @given(
        article_count=st.integers(min_value=1, max_value=50),
        failure_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_property_statistics_accuracy(
        self, article_count: int, failure_rate: float
    ):
        """
        **Feature: refactor-scheduling-jobs, Property 5: Statistics accuracy**
        **Validates: Requirements 7.2**

        Property: Para cualquier ejecución del pipeline, las estadísticas
        deben cumplir: total = success + failed en cada fase.

        Esta propiedad verifica que el Process Manager acumula correctamente
        las estadísticas de éxito y fallo, sin perder ni duplicar contadores.
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        mediator = self.create_mock_mediator_with_failure_rate(failure_rate)
        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(
            scraping_articles=articles,
            plaintext_articles=articles,
            markdown_articles=articles,
        )

        process_manager = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Property: total = success + failed para cada fase
        assert result.success is True, "Pipeline should complete successfully"

        # Scraping phase
        scraping_total = result.scraping.get("total", 0)
        scraping_success = result.scraping.get("success", 0)
        scraping_failed = result.scraping.get("failed", 0)
        assert scraping_total == scraping_success + scraping_failed, (
            f"Scraping: total ({scraping_total}) != success ({scraping_success}) + "
            f"failed ({scraping_failed})"
        )
        assert (
            scraping_total == article_count
        ), f"Scraping: total ({scraping_total}) != article_count ({article_count})"

        # Plaintext phase
        plaintext_total = result.plaintext.get("total", 0)
        plaintext_success = result.plaintext.get("success", 0)
        plaintext_failed = result.plaintext.get("failed", 0)
        assert plaintext_total == plaintext_success + plaintext_failed, (
            f"Plaintext: total ({plaintext_total}) != success ({plaintext_success}) + "
            f"failed ({plaintext_failed})"
        )
        assert (
            plaintext_total == article_count
        ), f"Plaintext: total ({plaintext_total}) != article_count ({article_count})"

        # Markdown phase
        markdown_total = result.markdown.get("total", 0)
        markdown_success = result.markdown.get("success", 0)
        markdown_failed = result.markdown.get("failed", 0)
        assert markdown_total == markdown_success + markdown_failed, (
            f"Markdown: total ({markdown_total}) != success ({markdown_success}) + "
            f"failed ({markdown_failed})"
        )
        assert (
            markdown_total == article_count
        ), f"Markdown: total ({markdown_total}) != article_count ({article_count})"

        # Verify non-negative counters
        assert scraping_success >= 0, "Success count cannot be negative"
        assert scraping_failed >= 0, "Failed count cannot be negative"
        assert plaintext_success >= 0, "Success count cannot be negative"
        assert plaintext_failed >= 0, "Failed count cannot be negative"
        assert markdown_success >= 0, "Success count cannot be negative"
        assert markdown_failed >= 0, "Failed count cannot be negative"

    @given(
        article_count=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_empty_phases_have_zero_stats(self, article_count: int):
        """
        Property: Cuando una fase no tiene artículos para procesar,
        las estadísticas deben ser todas cero.

        Esto verifica que el Process Manager maneja correctamente
        el caso de fases vacías sin generar estadísticas incorrectas.
        """
        # Arrange - Solo scraping tiene artículos, otras fases vacías
        scraping_articles = [create_test_article() for _ in range(article_count)]

        mediator = self.create_mock_mediator_with_failure_rate(0.0)
        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(
            scraping_articles=scraping_articles,
            plaintext_articles=[],  # Vacío
            markdown_articles=[],  # Vacío
        )

        process_manager = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Fases vacías deben tener estadísticas en cero
        assert result.plaintext["total"] == 0
        assert result.plaintext["success"] == 0
        assert result.plaintext["failed"] == 0

        assert result.markdown["total"] == 0
        assert result.markdown["success"] == 0
        assert result.markdown["failed"] == 0

        # Scraping debe tener estadísticas correctas
        if article_count > 0:
            assert result.scraping["total"] == article_count
            assert (
                result.scraping["success"] + result.scraping["failed"] == article_count
            )

    @given(
        article_count=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_all_success_means_zero_failures(self, article_count: int):
        """
        Property: Cuando todos los comandos tienen éxito (failure_rate=0),
        el contador de fallos debe ser cero y success debe ser igual a total.
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        mediator = self.create_mock_mediator_with_failure_rate(0.0)  # Sin fallos
        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(
            scraping_articles=articles,
            plaintext_articles=articles,
            markdown_articles=articles,
        )

        process_manager = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Sin fallos, success debe ser igual a total
        assert result.scraping["failed"] == 0
        assert result.scraping["success"] == article_count
        assert result.scraping["total"] == article_count

        assert result.plaintext["failed"] == 0
        assert result.plaintext["success"] == article_count
        assert result.plaintext["total"] == article_count

        assert result.markdown["failed"] == 0
        assert result.markdown["success"] == article_count
        assert result.markdown["total"] == article_count

    @given(
        article_count=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_all_failures_means_zero_success(self, article_count: int):
        """
        Property: Cuando todos los comandos fallan (failure_rate=1.0),
        el contador de éxitos debe ser cero y failed debe ser igual a total.
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        mediator = self.create_mock_mediator_with_failure_rate(1.0)  # Todos fallan
        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(
            scraping_articles=articles,
            plaintext_articles=articles,
            markdown_articles=articles,
        )

        process_manager = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Todos fallan, success debe ser cero
        assert result.scraping["success"] == 0
        assert result.scraping["failed"] == article_count
        assert result.scraping["total"] == article_count

        assert result.plaintext["success"] == 0
        assert result.plaintext["failed"] == article_count
        assert result.plaintext["total"] == article_count

        assert result.markdown["success"] == 0
        assert result.markdown["failed"] == article_count
        assert result.markdown["total"] == article_count

    @given(
        article_count=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_idempotency(self, article_count: int):
        """
        **Feature: refactor-scheduling-jobs, Property 7: Pipeline idempotency**
        **Validates: Requirements 9.4**

        Property: Ejecutar el pipeline múltiples veces con los mismos artículos
        debe producir el mismo resultado final.

        Esta propiedad verifica que el Process Manager es idempotente:
        - Los artículos ya procesados se detectan y se omiten
        - Las estadísticas reflejan correctamente el trabajo realizado
        - No se duplica el procesamiento

        Nota: En este test, simulamos idempotencia haciendo que el query adapter
        retorne menos artículos en la segunda ejecución (simulando que ya fueron
        procesados). En un sistema real, el query adapter consultaría la base de
        datos y filtrarí artículos ya procesados.
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        mediator = self.create_mock_mediator_with_failure_rate(0.0)
        logger = self.create_mock_logger()

        # Primera ejecución: todos los artículos necesitan procesamiento
        query_adapter_first = self.create_mock_query_adapter(
            scraping_articles=articles,
            plaintext_articles=articles,
            markdown_articles=articles,
        )

        process_manager_first = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter_first,
            logger=logger,
        )

        # Act - Primera ejecución
        result_first = await process_manager_first.execute(limit=100)

        # Assert - Primera ejecución procesa todos los artículos
        assert result_first.success is True
        assert result_first.scraping["total"] == article_count
        assert result_first.plaintext["total"] == article_count
        assert result_first.markdown["total"] == article_count

        # Arrange - Segunda ejecución: artículos ya procesados (query adapter retorna vacío)
        query_adapter_second = self.create_mock_query_adapter(
            scraping_articles=[],  # Ya procesados
            plaintext_articles=[],  # Ya procesados
            markdown_articles=[],  # Ya procesados
        )

        process_manager_second = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter_second,
            logger=logger,
        )

        # Act - Segunda ejecución (idempotente)
        result_second = await process_manager_second.execute(limit=100)

        # Assert - Segunda ejecución no procesa nada (idempotencia)
        assert result_second.success is True
        assert (
            result_second.scraping["total"] == 0
        ), "Idempotency: segunda ejecución no debe procesar artículos ya procesados"
        assert result_second.plaintext["total"] == 0
        assert result_second.markdown["total"] == 0

        # Property: El estado final es el mismo después de múltiples ejecuciones
        # En este caso, verificamos que la segunda ejecución no genera trabajo adicional
        assert result_second.scraping["success"] == 0
        assert result_second.scraping["failed"] == 0
        assert result_second.plaintext["success"] == 0
        assert result_second.plaintext["failed"] == 0
        assert result_second.markdown["success"] == 0
        assert result_second.markdown["failed"] == 0

    @given(
        first_batch=st.integers(min_value=1, max_value=15),
        second_batch=st.integers(min_value=0, max_value=15),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_incremental_processing(
        self, first_batch: int, second_batch: int
    ):
        """
        Property: El pipeline debe procesar incrementalmente nuevos artículos
        sin re-procesar los anteriores.

        Esta propiedad verifica que:
        - Primera ejecución procesa first_batch artículos
        - Segunda ejecución procesa solo second_batch artículos nuevos
        - No hay duplicación de trabajo
        """
        # Arrange - Primera ejecución
        first_articles = [create_test_article() for _ in range(first_batch)]

        mediator = self.create_mock_mediator_with_failure_rate(0.0)
        logger = self.create_mock_logger()

        query_adapter_first = self.create_mock_query_adapter(
            scraping_articles=first_articles,
            plaintext_articles=first_articles,
            markdown_articles=first_articles,
        )

        process_manager_first = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter_first,
            logger=logger,
        )

        # Act - Primera ejecución
        result_first = await process_manager_first.execute(limit=100)

        # Assert - Primera ejecución
        assert result_first.scraping["total"] == first_batch

        # Arrange - Segunda ejecución con nuevos artículos
        second_articles = [create_test_article() for _ in range(second_batch)]

        query_adapter_second = self.create_mock_query_adapter(
            scraping_articles=second_articles,  # Solo nuevos artículos
            plaintext_articles=second_articles,
            markdown_articles=second_articles,
        )

        process_manager_second = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter_second,
            logger=logger,
        )

        # Act - Segunda ejecución
        result_second = await process_manager_second.execute(limit=100)

        # Assert - Segunda ejecución procesa solo nuevos artículos
        assert result_second.scraping["total"] == second_batch
        assert result_second.plaintext["total"] == second_batch
        assert result_second.markdown["total"] == second_batch

        # Property: Total procesado = first_batch + second_batch (sin duplicados)
        total_processed = (
            result_first.scraping["total"] + result_second.scraping["total"]
        )
        assert total_processed == first_batch + second_batch
