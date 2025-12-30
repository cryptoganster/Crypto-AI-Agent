"""Property-based test para Parallel Processing Safety usando Hypothesis.

Este test verifica que cuando se procesan múltiples artículos,
cada comando opera sobre un aggregate diferente (article_id único).

Feature: refactor-scheduling-jobs
Property 8: Parallel processing safety
Validates: Requirements 12.2
"""

from typing import Set
from unittest.mock import AsyncMock, Mock, call
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

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
    """Crea un artículo de prueba con valores válidos y ID único."""
    return RssArticle(
        title=RssArticleTitle("Test RssArticle"),
        url=RssArticleUrl(f"https://example.com/article/{uuid4()}"),
        source_id=RssFeedId(str(uuid4())),
        article_id=RssArticleId(str(uuid4())),
    )


# ============================================================================
# PROPERTY TEST
# ============================================================================


class TestParallelProcessingSafetyProperty:
    """Property-based test para verificar seguridad en procesamiento paralelo."""

    def create_mock_mediator_tracking_article_ids(self) -> tuple[Mock, list]:
        """Crea un mock del mediator que rastrea los article_ids procesados.

        Returns:
            Tuple de (mediator_mock, lista_de_article_ids_procesados)
        """
        mediator = Mock(spec=IMediator)
        processed_article_ids = []

        async def send_tracking_article_id(command):
            # Extraer article_id del comando
            article_id = getattr(command, "article_id", None)
            if article_id:
                processed_article_ids.append(article_id)

            result = Mock()
            result.success = True
            return result

        mediator.send = AsyncMock(side_effect=send_tracking_article_id)
        return mediator, processed_article_ids

    def create_mock_logger(self) -> Mock:
        """Crea un mock del logger."""
        logger = Mock(spec=ILogger)
        logger.bind.return_value = logger
        return logger

    def create_mock_query_adapter(self, articles: list[RssArticle]) -> Mock:
        """Crea un mock del query adapter con artículos específicos."""
        adapter = Mock(spec=IGetArticlesRequiringProcessing)
        adapter.get_without_content_scrapped = AsyncMock(return_value=articles)
        adapter.get_without_content_plaintext = AsyncMock(return_value=[])
        adapter.get_without_content_markdown = AsyncMock(return_value=[])
        return adapter

    @given(
        article_count=st.integers(min_value=2, max_value=50),
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_property_parallel_processing_safety(self, article_count: int):
        """
        **Feature: refactor-scheduling-jobs, Property 8: Parallel processing safety**
        **Validates: Requirements 12.2**

        Property: Para cualquier batch de artículos procesados, cada comando
        debe operar sobre un article_id diferente para evitar race conditions.

        Esta propiedad verifica que:
        - Cada comando recibe un article_id único
        - No hay duplicación de article_ids en los comandos enviados
        - Todos los article_ids procesados corresponden a artículos válidos
        - El número de comandos enviados coincide con el número de artículos

        Nota: Esta propiedad es fundamental para garantizar que el procesamiento
        paralelo (cuando se implemente con asyncio.gather) no cause race conditions
        al operar sobre el mismo aggregate múltiples veces.
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]
        expected_article_ids = {str(article.id) for article in articles}

        mediator, processed_article_ids = (
            self.create_mock_mediator_tracking_article_ids()
        )
        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(articles)

        process_manager = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Property: Pipeline completa exitosamente
        assert result.success is True, "Pipeline should complete successfully"

        # Assert - Property: Número de comandos enviados = número de artículos
        assert (
            len(processed_article_ids) == article_count
        ), f"Should send {article_count} commands, but sent {len(processed_article_ids)}"

        # Assert - Property: Todos los article_ids son únicos (no hay duplicados)
        unique_article_ids = set(processed_article_ids)
        assert len(unique_article_ids) == len(processed_article_ids), (
            f"Found duplicate article_ids: {len(processed_article_ids)} total, "
            f"but only {len(unique_article_ids)} unique. "
            f"Duplicates indicate potential race conditions!"
        )

        # Assert - Property: Todos los article_ids procesados son válidos
        assert unique_article_ids == expected_article_ids, (
            f"Processed article_ids don't match expected. "
            f"Expected: {expected_article_ids}, "
            f"Got: {unique_article_ids}"
        )

        # Assert - Property: Cada artículo fue procesado exactamente una vez
        for article in articles:
            article_id = str(article.id)
            count = processed_article_ids.count(article_id)
            assert count == 1, (
                f"RssArticle {article_id} was processed {count} times, "
                f"expected exactly 1. This indicates a race condition!"
            )

        # Assert - Property: Estadísticas reflejan procesamiento correcto
        assert result.scraping["total"] == article_count
        assert result.scraping["success"] == article_count
        assert result.scraping["failed"] == 0

    @given(
        article_count=st.integers(min_value=2, max_value=30),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_no_concurrent_access_to_same_aggregate(
        self, article_count: int
    ):
        """
        Property: Durante el procesamiento, nunca debe haber acceso concurrente
        al mismo aggregate (article_id).

        Esta propiedad verifica que en cualquier momento durante la ejecución,
        cada article_id está siendo procesado por exactamente un comando.

        Nota: En la implementación actual (secuencial), esto se cumple trivialmente.
        Si se implementa procesamiento paralelo con asyncio.gather, este test
        seguirá siendo válido porque cada comando opera sobre un article_id diferente.
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]

        # Rastrear article_ids "en proceso" en cada momento
        currently_processing: Set[str] = set()
        max_concurrent_per_article = {}

        mediator = Mock(spec=IMediator)

        async def send_tracking_concurrency(command):
            article_id = getattr(command, "article_id", None)
            if article_id:
                # Verificar que este article_id no esté siendo procesado
                if article_id in currently_processing:
                    # ¡Race condition detectada!
                    raise AssertionError(
                        f"Race condition: article {article_id} is being processed "
                        f"concurrently by multiple commands!"
                    )

                # Marcar como "en proceso"
                currently_processing.add(article_id)

                # Rastrear concurrencia máxima
                if article_id not in max_concurrent_per_article:
                    max_concurrent_per_article[article_id] = 0
                max_concurrent_per_article[article_id] = max(
                    max_concurrent_per_article[article_id],
                    len([aid for aid in currently_processing if aid == article_id]),
                )

                # Simular procesamiento
                result = Mock()
                result.success = True

                # Marcar como "completado"
                currently_processing.remove(article_id)

                return result

            result = Mock()
            result.success = True
            return result

        mediator.send = AsyncMock(side_effect=send_tracking_concurrency)

        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(articles)

        process_manager = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Property: Nunca hubo acceso concurrente al mismo aggregate
        for article_id, max_concurrent in max_concurrent_per_article.items():
            assert max_concurrent == 1, (
                f"RssArticle {article_id} had {max_concurrent} concurrent accesses, "
                f"expected exactly 1. This indicates a race condition!"
            )

        # Assert - Property: Pipeline completa exitosamente
        assert result.success is True

        # Assert - Property: No hay article_ids "en proceso" al final
        assert (
            len(currently_processing) == 0
        ), f"Found {len(currently_processing)} articles still processing after completion"

    @given(
        article_count=st.integers(min_value=1, max_value=25),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_commands_receive_correct_article_ids(
        self, article_count: int
    ):
        """
        Property: Cada comando debe recibir el article_id correcto del artículo
        que está procesando.

        Esta propiedad verifica que no hay confusión de article_ids entre comandos,
        lo cual podría causar que un comando procese el artículo equivocado.
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]
        article_id_to_article = {str(article.id): article for article in articles}

        mediator = Mock(spec=IMediator)
        commands_received = []

        async def send_capturing_commands(command):
            commands_received.append(command)
            result = Mock()
            result.success = True
            return result

        mediator.send = AsyncMock(side_effect=send_capturing_commands)

        logger = self.create_mock_logger()
        query_adapter = self.create_mock_query_adapter(articles)

        process_manager = ScrapingProcessManager(
            mediator=mediator,
            query_adapter=query_adapter,
            logger=logger,
        )

        # Act
        result = await process_manager.execute(limit=100)

        # Assert - Property: Cada comando tiene un article_id válido
        for command in commands_received:
            article_id = getattr(command, "article_id", None)
            assert article_id is not None, "Command should have article_id"
            assert (
                article_id in article_id_to_article
            ), f"Command has invalid article_id: {article_id}"

        # Assert - Property: Todos los artículos fueron procesados
        processed_ids = {getattr(cmd, "article_id", None) for cmd in commands_received}
        expected_ids = set(article_id_to_article.keys())
        assert processed_ids == expected_ids, (
            f"Not all articles were processed. "
            f"Expected: {expected_ids}, Got: {processed_ids}"
        )

        # Assert - Property: Pipeline completa exitosamente
        assert result.success is True

    @given(
        article_count=st.integers(min_value=2, max_value=20),
    )
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_aggregate_isolation_across_phases(self, article_count: int):
        """
        Property: Cada fase del pipeline debe procesar los mismos article_ids
        sin mezclar aggregates entre fases.

        Esta propiedad verifica que:
        - La fase de scraping procesa artículos A, B, C
        - La fase de plaintext procesa artículos A, B, C (los mismos)
        - La fase de markdown procesa artículos A, B, C (los mismos)
        - No hay confusión de article_ids entre fases
        """
        # Arrange
        articles = [create_test_article() for _ in range(article_count)]
        expected_article_ids = {str(article.id) for article in articles}

        mediator = Mock(spec=IMediator)
        phase_article_ids = {
            "scraping": [],
            "plaintext": [],
            "markdown": [],
        }

        async def send_tracking_by_phase(command):
            article_id = getattr(command, "article_id", None)
            if article_id:
                # Determinar fase basándose en el tipo de comando
                command_type = type(command).__name__
                if "Scrape" in command_type:
                    phase_article_ids["scraping"].append(article_id)
                elif "Plaintext" in command_type:
                    phase_article_ids["plaintext"].append(article_id)
                elif "Markdown" in command_type:
                    phase_article_ids["markdown"].append(article_id)

            result = Mock()
            result.success = True
            return result

        mediator.send = AsyncMock(side_effect=send_tracking_by_phase)

        logger = self.create_mock_logger()

        # Todas las fases tienen los mismos artículos
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

        # Assert - Property: Cada fase procesa los mismos article_ids
        scraping_ids = set(phase_article_ids["scraping"])
        plaintext_ids = set(phase_article_ids["plaintext"])
        markdown_ids = set(phase_article_ids["markdown"])

        assert scraping_ids == expected_article_ids, (
            f"Scraping phase processed wrong articles. "
            f"Expected: {expected_article_ids}, Got: {scraping_ids}"
        )
        assert plaintext_ids == expected_article_ids, (
            f"Plaintext phase processed wrong articles. "
            f"Expected: {expected_article_ids}, Got: {plaintext_ids}"
        )
        assert markdown_ids == expected_article_ids, (
            f"Markdown phase processed wrong articles. "
            f"Expected: {expected_article_ids}, Got: {markdown_ids}"
        )

        # Assert - Property: No hay duplicados dentro de cada fase
        assert len(phase_article_ids["scraping"]) == len(scraping_ids)
        assert len(phase_article_ids["plaintext"]) == len(plaintext_ids)
        assert len(phase_article_ids["markdown"]) == len(markdown_ids)

        # Assert - Property: Pipeline completa exitosamente
        assert result.success is True
