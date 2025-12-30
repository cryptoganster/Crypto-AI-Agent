"""Property-based tests para comandos de procesamiento de artículos usando Hypothesis.

Estos tests verifican propiedades universales que deben cumplirse
para todas las entradas válidas de los comandos de procesamiento de artículos.
"""

from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# Importar componentes del sistema
from src.rss.article.app.commands.calculate_article_quality import (
    CalculateArticleQualityCommand,
    CalculateArticleQualityHandler,
    CalculateArticleQualityResult,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.value_objects import RssArticleId
from src.rss.feed.domain.value_objects import RssFeedId
from src.shared.domain.value_objects import Level

# ============================================================================
# ESTRATEGIAS DE GENERACIÓN DE DATOS
# ============================================================================


def valid_uuid_strategy():
    """Genera UUIDs válidos."""
    return st.uuids()


@st.composite
def valid_article_id_strategy(draw):
    """Genera article_id válidos como strings."""
    uuid_val = draw(valid_uuid_strategy())
    return str(uuid_val)


@st.composite
def valid_calculate_quality_command_strategy(draw):
    """Genera CalculateArticleQualityCommand válidos."""
    article_id = draw(valid_article_id_strategy())
    force_recalculate = draw(st.booleans())
    update_article = draw(st.booleans())

    # Generar correlation_id opcional
    correlation_id_text = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    if correlation_id_text is not None and not correlation_id_text.strip():
        correlation_id = None
    else:
        correlation_id = correlation_id_text

    return CalculateArticleQualityCommand(
        article_id=article_id,
        force_recalculate=force_recalculate,
        update_article=update_article,
        correlation_id=correlation_id,
    )


@st.composite
def valid_article_strategy(draw):
    """Genera Article válidos para testing."""
    article_id = RssArticleId(str(draw(valid_uuid_strategy())))
    source_id = RssFeedId(str(draw(valid_uuid_strategy())))

    # Generar título no vacío
    title = draw(
        st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        )
    )
    if not title.strip():
        title = "Test RssArticle"

    # Generar URL válida
    url = f"https://example.com/article/{uuid4()}"

    # Generar contenido markdown no vacío
    content_markdown = draw(
        st.text(
            min_size=10,
            max_size=1000,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        )
    )
    if not content_markdown.strip():
        content_markdown = "This is test content for the article."

    # Generar quality score opcional
    quality_score = draw(st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0)))

    # Crear artículo
    article = RssArticle(
        id=article_id,
        source_id=source_id,
        title=title,
        url=url,
        content_markdown=content_markdown,
        published_at=datetime.now(timezone.utc),
        quality_score=quality_score,
    )

    # Si tiene quality_score, asignar quality_level
    if quality_score is not None:
        article.update_quality_assessment(quality_level=Level.from_score(quality_score))

    return article


# ============================================================================
# PROPERTY TEST: ARTICLE PROCESSING COMMAND EXECUTION
# ============================================================================


class TestRssArticleProcessingCommandExecution:
    """**Feature: resolve-todos, Property 6: RssArticle Processing Command Execution**

    **Validates: Requirements 3.2**

    Para cualquier artículo, el comando de procesamiento debe ejecutarse y completarse.
    """

    @settings(max_examples=100)
    @given(command=valid_calculate_quality_command_strategy())
    @pytest.mark.asyncio
    async def test_article_processing_command_executes_and_completes(self, command):
        """Para cualquier comando de procesamiento válido, debe ejecutarse y completarse."""
        # Arrange - Crear artículo mock con contenido
        mock_article = await self._create_mock_article_with_content(command.article_id)

        # Mock query adapter que retorna el artículo
        mock_query = AsyncMock()
        mock_query.get_by_id = AsyncMock(return_value=mock_article)

        # Mock repository
        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        # Mock quality service que retorna un score válido
        mock_quality_service = Mock()
        mock_quality_service.calculate_content_quality_score = Mock(return_value=0.75)

        # Mock logger
        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        mock_logger.exception = Mock()
        mock_logger.debug = Mock()

        # Crear handler
        handler = CalculateArticleQualityHandler(
            article_repository=mock_repository,
            article_read_repository=mock_query,
            quality_service=mock_quality_service,
            logger=mock_logger,
        )

        # Act - Ejecutar comando
        result = await handler.handle(command)

        # Assert - El comando debe ejecutarse y completarse
        assert result is not None, "El handler debe retornar un resultado"
        assert isinstance(
            result, CalculateArticleQualityResult
        ), "El resultado debe ser una instancia de CalculateArticleQualityResult"
        # El comando debe completarse (success=True o success=False con error específico)
        assert isinstance(
            result.success, bool
        ), "El resultado debe tener un estado de éxito booleano"
        assert (
            result.article_id == command.article_id
        ), "El article_id del resultado debe coincidir con el del comando"

    @settings(max_examples=100)
    @given(command=valid_calculate_quality_command_strategy())
    @pytest.mark.asyncio
    async def test_article_processing_preserves_article_id(self, command):
        """Para cualquier comando, el article_id debe preservarse en el resultado."""
        # Arrange
        mock_article = await self._create_mock_article_with_content(command.article_id)

        mock_query = AsyncMock()
        mock_query.get_by_id = AsyncMock(return_value=mock_article)

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        mock_quality_service = Mock()
        mock_quality_service.calculate_content_quality_score = Mock(return_value=0.75)

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        handler = CalculateArticleQualityHandler(
            article_repository=mock_repository,
            article_read_repository=mock_query,
            quality_service=mock_quality_service,
            logger=mock_logger,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert (
            result.article_id == command.article_id
        ), "El article_id debe preservarse en el resultado"

    @settings(max_examples=100)
    @given(command=valid_calculate_quality_command_strategy())
    @pytest.mark.asyncio
    async def test_article_processing_with_content_succeeds(self, command):
        """Para cualquier artículo con contenido, el procesamiento debe ser exitoso."""
        # Arrange - Artículo con contenido markdown
        mock_article = await self._create_mock_article_with_content(command.article_id)

        mock_query = AsyncMock()
        mock_query.get_by_id = AsyncMock(return_value=mock_article)

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        mock_quality_service = Mock()
        mock_quality_service.calculate_content_quality_score = Mock(return_value=0.75)

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        handler = CalculateArticleQualityHandler(
            article_repository=mock_repository,
            article_read_repository=mock_query,
            quality_service=mock_quality_service,
            logger=mock_logger,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert (
            result.success is True
        ), f"El procesamiento de artículo con contenido debe ser exitoso. Error: {result.error_message if not result.success else 'N/A'}"
        assert (
            result.quality_score is not None
        ), "El resultado debe incluir un quality_score"
        assert (
            0.0 <= result.quality_score <= 1.0
        ), "El quality_score debe estar entre 0.0 y 1.0"
        assert (
            result.quality_level is not None
        ), "El resultado debe incluir un quality_level"

    @settings(max_examples=100)
    @given(command=valid_calculate_quality_command_strategy())
    @pytest.mark.asyncio
    async def test_article_processing_without_content_fails_gracefully(self, command):
        """Para cualquier artículo sin contenido, el procesamiento debe fallar apropiadamente."""
        # Arrange - Artículo sin contenido markdown
        mock_article = await self._create_mock_article_without_content(
            command.article_id
        )

        mock_query = AsyncMock()
        mock_query.get_by_id = AsyncMock(return_value=mock_article)

        mock_repository = AsyncMock()
        mock_quality_service = Mock()

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        handler = CalculateArticleQualityHandler(
            article_repository=mock_repository,
            article_read_repository=mock_query,
            quality_service=mock_quality_service,
            logger=mock_logger,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert (
            result.success is False
        ), "El procesamiento de artículo sin contenido debe fallar"
        assert (
            result.error_code == "NO_CONTENT_MARKDOWN"
        ), "El código de error debe indicar falta de contenido"

    @settings(max_examples=100)
    @given(article_id=valid_article_id_strategy())
    @pytest.mark.asyncio
    async def test_article_processing_for_nonexistent_article_fails(self, article_id):
        """Para cualquier article_id inexistente, el procesamiento debe fallar apropiadamente."""
        # Arrange - Mock query que retorna None
        mock_query = AsyncMock()
        mock_query.get_by_id = AsyncMock(return_value=None)

        mock_repository = AsyncMock()
        mock_quality_service = Mock()

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        handler = CalculateArticleQualityHandler(
            article_repository=mock_repository,
            article_read_repository=mock_query,
            quality_service=mock_quality_service,
            logger=mock_logger,
        )

        # Crear comando
        command = CalculateArticleQualityCommand(
            article_id=article_id,
            force_recalculate=False,
            update_article=True,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert (
            result.success is False
        ), "El procesamiento debe fallar cuando el artículo no existe"
        assert (
            result.error_code == "ARTICLE_NOT_FOUND"
        ), "El código de error debe indicar que el artículo no fue encontrado"

    @settings(max_examples=100)
    @given(command=valid_calculate_quality_command_strategy())
    @pytest.mark.asyncio
    async def test_article_processing_calls_quality_service(self, command):
        """Para cualquier comando exitoso, debe llamar al servicio de calidad."""
        # Arrange
        mock_article = await self._create_mock_article_with_content(command.article_id)

        mock_query = AsyncMock()
        mock_query.get_by_id = AsyncMock(return_value=mock_article)

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        mock_quality_service = Mock()
        mock_quality_service.calculate_content_quality_score = Mock(return_value=0.75)

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        handler = CalculateArticleQualityHandler(
            article_repository=mock_repository,
            article_read_repository=mock_query,
            quality_service=mock_quality_service,
            logger=mock_logger,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        if result.success:
            # Si el artículo no tenía quality_score o force_recalculate=True
            if mock_article.quality.quality_score is None or command.force_recalculate:
                assert (
                    mock_quality_service.calculate_content_quality_score.called
                ), "El servicio de calidad debe ser llamado para calcular el score"

    @settings(max_examples=100)
    @given(command=valid_calculate_quality_command_strategy())
    @pytest.mark.asyncio
    async def test_article_processing_updates_repository_when_requested(self, command):
        """Para cualquier comando con update_article=True, debe actualizar el repositorio."""
        # Arrange
        mock_article = await self._create_mock_article_with_content(command.article_id)

        mock_query = AsyncMock()
        mock_query.get_by_id = AsyncMock(return_value=mock_article)

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        mock_quality_service = Mock()
        mock_quality_service.calculate_content_quality_score = Mock(return_value=0.75)

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        handler = CalculateArticleQualityHandler(
            article_repository=mock_repository,
            article_read_repository=mock_query,
            quality_service=mock_quality_service,
            logger=mock_logger,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        if result.success and command.update_article:
            # Si el artículo no tenía quality_score o force_recalculate=True
            if mock_article.quality.quality_score is None or command.force_recalculate:
                assert (
                    mock_repository.save.called
                ), "El repositorio debe ser llamado para guardar el artículo actualizado"

    @settings(max_examples=50)
    @given(
        command=valid_calculate_quality_command_strategy(),
        execution_count=st.integers(min_value=2, max_value=5),
    )
    @pytest.mark.asyncio
    async def test_article_processing_is_idempotent(self, command, execution_count):
        """Para cualquier comando, ejecutarlo múltiples veces debe ser idempotente."""
        # Arrange
        mock_article = await self._create_mock_article_with_content(command.article_id)

        mock_query = AsyncMock()
        mock_query.get_by_id = AsyncMock(return_value=mock_article)

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        mock_quality_service = Mock()
        mock_quality_service.calculate_content_quality_score = Mock(return_value=0.75)

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        handler = CalculateArticleQualityHandler(
            article_repository=mock_repository,
            article_read_repository=mock_query,
            quality_service=mock_quality_service,
            logger=mock_logger,
        )

        # Act - Ejecutar el comando múltiples veces
        results = []
        for _ in range(execution_count):
            result = await handler.handle(command)
            results.append(result)

        # Assert - Todos los resultados deben ser consistentes
        assert all(
            r.article_id == command.article_id for r in results
        ), "Todas las ejecuciones deben tener el mismo article_id"

        # Si la primera fue exitosa, todas deben serlo
        if results[0].success:
            assert all(
                r.success for r in results
            ), "Todas las ejecuciones deben ser exitosas si la primera lo fue"

    @settings(max_examples=100)
    @given(command=valid_calculate_quality_command_strategy())
    @pytest.mark.asyncio
    async def test_article_processing_returns_valid_quality_score(self, command):
        """Para cualquier procesamiento exitoso, el quality_score debe estar en rango válido."""
        # Arrange
        mock_article = await self._create_mock_article_with_content(command.article_id)

        mock_query = AsyncMock()
        mock_query.get_by_id = AsyncMock(return_value=mock_article)

        mock_repository = AsyncMock()
        mock_repository.save = AsyncMock()

        # Generar un score aleatorio válido
        import random

        random_score = random.uniform(0.0, 1.0)

        mock_quality_service = Mock()
        mock_quality_service.calculate_content_quality_score = Mock(
            return_value=random_score
        )

        mock_logger = Mock()
        mock_logger.bind = Mock(return_value=mock_logger)
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()

        handler = CalculateArticleQualityHandler(
            article_repository=mock_repository,
            article_read_repository=mock_query,
            quality_service=mock_quality_service,
            logger=mock_logger,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        if result.success and result.quality_score is not None:
            assert (
                0.0 <= result.quality_score <= 1.0
            ), f"El quality_score debe estar entre 0.0 y 1.0, pero fue {result.quality_score}"

    # Helper methods
    async def _create_mock_article_with_content(
        self, article_id_str: str
    ) -> RssArticle:
        """Crea un Article mock con contenido para testing."""
        from src.rss.article.domain.value_objects import RssArticleUrl
        from src.rss.article.domain.value_objects.metadata import RssArticleTitle

        article_id = RssArticleId(article_id_str)
        source_id = RssFeedId(str(uuid4()))
        title = RssArticleTitle("Test RssArticle")
        url = RssArticleUrl(f"https://example.com/article/{uuid4()}")

        article = RssArticle(
            title=title,
            url=url,
            source_id=source_id,
            article_id=article_id,
        )

        # Establecer contenido markdown después de la creación usando método público
        article.update_content_fields(
            markdown="This is test content for the article. It has enough text to be analyzed."
        )
        article.mark_events_as_committed()  # Limpiar eventos de test

        return article

    async def _create_mock_article_without_content(
        self, article_id_str: str
    ) -> RssArticle:
        """Crea un Article mock sin contenido para testing."""
        from src.rss.article.domain.value_objects import RssArticleUrl
        from src.rss.article.domain.value_objects.metadata import RssArticleTitle

        article_id = RssArticleId(article_id_str)
        source_id = RssFeedId(str(uuid4()))
        title = RssArticleTitle("Test RssArticle Without Content")
        url = RssArticleUrl(f"https://example.com/article/{uuid4()}")

        article = RssArticle(
            title=title,
            url=url,
            source_id=source_id,
            article_id=article_id,
        )

        # No establecer contenido markdown (None por defecto)

        return article
