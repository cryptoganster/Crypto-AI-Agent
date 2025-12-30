"""Property-based tests para Event Publishing usando Hypothesis.

Estos tests verifican que los repositorios publican eventos de dominio
automáticamente al persistir agregados.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.infra.persistence.repositories.rss.article_write_repository import (
    ArticleWriteRepository,
)

# Importar componentes del sistema
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.events.article_content_updated import (
    RssArticleContentUpdated,
)
from src.rss.article.domain.events.article_created import RssArticleCreated
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.feed.domain.value_objects import RssFeedId

# ============================================================================
# ESTRATEGIAS DE GENERACIÓN DE DATOS
# ============================================================================


def valid_uuid_strategy():
    """Genera UUIDs válidos."""
    return st.uuids()


@st.composite
def valid_source_id_strategy(draw):
    """Genera SourceId válidos."""
    uuid_val = draw(valid_uuid_strategy())
    return RssFeedId(str(uuid_val))


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

    # Crear artículo usando factory method (emite ArticleCreated event)
    factory = RssArticleFactory()

    article = factory.create_article(
        title=title,
        url=url,
        source_id=source_id,
        article_id=article_id,
    )

    # Establecer contenido markdown usando el método público
    if content_markdown:
        article.update_content_fields(markdown=content_markdown)
        article.mark_events_as_committed()  # Limpiar eventos de test

    # Establecer coin_mentions como None (atributo comentado en Article pero requerido por mapper)
    article._coin_mentions = None
    article._is_coin_checked = False

    return article


@st.composite
def article_with_events_strategy(draw):
    """Genera Article con eventos de dominio."""
    article = draw(valid_article_strategy())

    # Generar número aleatorio de eventos adicionales (1-5)
    num_additional_events = draw(st.integers(min_value=0, max_value=4))

    for _ in range(num_additional_events):
        # Agregar evento de actualización de contenido
        new_content = draw(
            st.text(
                min_size=10,
                max_size=500,
                alphabet=st.characters(blacklist_categories=("Cs",)),
            )
        )
        if new_content.strip():
            article.update_content_fields(markdown=new_content)

    return article


# ============================================================================
# PROPERTY TEST: EVENT PUBLISHING ON SAVE
# ============================================================================


class TestEventPublishingOnSave:
    """**Feature: cqrs-separation, Property 1: Event Publishing on Save**

    **Validates: Requirements 1.3**

    Para cualquier agregado con eventos de dominio, cuando se guarda a través
    de un repositorio, todos los eventos de dominio deben ser publicados
    automáticamente.
    """

    @settings(max_examples=100)
    @given(article=article_with_events_strategy())
    @pytest.mark.asyncio
    async def test_repository_publishes_all_events_on_save(self, article):
        """Para cualquier agregado con eventos, save() debe publicar todos los eventos."""
        # Arrange
        mock_session = AsyncMock()

        # Mock execute to return a result with scalar_one_or_none that returns None (new article)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        repository = ArticleWriteRepository(
            session=mock_session,
            logger=None,
            event_publisher=mock_event_publisher,
        )

        # Capturar eventos antes de guardar
        expected_events = list(article.domain_events)
        expected_event_count = len(expected_events)

        # Act
        await repository.save(article)

        # Assert - Todos los eventos deben ser publicados
        assert (
            mock_event_publisher.publish.call_count == expected_event_count
        ), f"Se esperaban {expected_event_count} eventos publicados, pero se publicaron {mock_event_publisher.publish.call_count}"

        # Verificar que cada evento fue publicado
        published_events = [
            call.args[0] for call in mock_event_publisher.publish.call_args_list
        ]

        assert len(published_events) == len(
            expected_events
        ), "El número de eventos publicados debe coincidir con los eventos del agregado"

        # Verificar que los eventos publicados son los mismos que los del agregado
        for expected_event, published_event in zip(expected_events, published_events):
            assert type(published_event) == type(
                expected_event
            ), f"El tipo de evento publicado {type(published_event)} debe coincidir con el esperado {type(expected_event)}"
            assert (
                published_event.aggregate_id == expected_event.aggregate_id
            ), "El aggregate_id del evento publicado debe coincidir"

    @settings(max_examples=100)
    @given(article=article_with_events_strategy())
    @pytest.mark.asyncio
    async def test_events_published_in_correct_order(self, article):
        """Para cualquier agregado con eventos, los eventos deben publicarse en el orden correcto."""
        # Arrange
        mock_session = AsyncMock()

        # Mock execute to return a result with scalar_one_or_none that returns None (new article)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        repository = ArticleWriteRepository(
            session=mock_session,
            logger=None,
            event_publisher=mock_event_publisher,
        )

        # Capturar eventos en orden
        expected_events = list(article.domain_events)

        # Act
        await repository.save(article)

        # Assert - Los eventos deben publicarse en el mismo orden
        published_events = [
            call.args[0] for call in mock_event_publisher.publish.call_args_list
        ]

        for i, (expected_event, published_event) in enumerate(
            zip(expected_events, published_events)
        ):
            assert type(published_event) == type(
                expected_event
            ), f"El evento en posición {i} debe ser del tipo correcto"

    @settings(max_examples=100)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_repository_without_publisher_does_not_fail(self, article):
        """Para cualquier agregado, save() sin event_publisher no debe fallar."""
        # Arrange
        mock_session = AsyncMock()

        # Mock execute to return a result with scalar_one_or_none that returns None (new article)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        repository = ArticleWriteRepository(
            session=mock_session,
            logger=None,
            event_publisher=None,  # Sin event publisher
        )

        # Act & Assert - No debe lanzar excepción
        try:
            await repository.save(article)
            success = True
        except Exception:
            success = False

        assert success, "save() sin event_publisher no debe fallar"

    @settings(max_examples=100)
    @given(article=article_with_events_strategy())
    @pytest.mark.asyncio
    async def test_events_published_after_persistence(self, article):
        """Para cualquier agregado, los eventos deben publicarse después de persistir."""
        # Arrange
        call_order = []

        async def track_flush():
            call_order.append("flush")

        async def track_commit():
            call_order.append("commit")

        async def track_publish(event):
            call_order.append("publish")

        mock_session = AsyncMock()

        # Mock execute to return a result with scalar_one_or_none that returns None (new article)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock(side_effect=track_flush)
        mock_session.commit = AsyncMock(side_effect=track_commit)

        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock(side_effect=track_publish)

        repository = ArticleWriteRepository(
            session=mock_session,
            logger=None,
            event_publisher=mock_event_publisher,
        )

        # Act
        await repository.save(article)

        # Assert - Los eventos deben publicarse después de flush y commit
        if len(article.domain_events) > 0:
            assert "flush" in call_order, "flush debe ser llamado"
            assert "commit" in call_order, "commit debe ser llamado"
            assert "publish" in call_order, "publish debe ser llamado"

            # Verificar orden: flush -> commit -> publish
            flush_index = call_order.index("flush")
            commit_index = call_order.index("commit")
            publish_index = call_order.index("publish")

            assert flush_index < commit_index, "flush debe ocurrir antes de commit"
            assert commit_index < publish_index, "commit debe ocurrir antes de publish"

    @settings(max_examples=50)
    @given(article=article_with_events_strategy())
    @pytest.mark.asyncio
    async def test_all_event_types_are_published(self, article):
        """Para cualquier agregado, todos los tipos de eventos deben ser publicados."""
        # Arrange
        mock_session = AsyncMock()

        # Mock execute to return a result with scalar_one_or_none that returns None (new article)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        repository = ArticleWriteRepository(
            session=mock_session,
            logger=None,
            event_publisher=mock_event_publisher,
        )

        # Capturar tipos de eventos esperados
        expected_event_types = set(type(event) for event in article.domain_events)

        # Act
        await repository.save(article)

        # Assert - Todos los tipos de eventos deben estar presentes
        published_events = [
            call.args[0] for call in mock_event_publisher.publish.call_args_list
        ]
        published_event_types = set(type(event) for event in published_events)

        assert (
            published_event_types == expected_event_types
        ), f"Los tipos de eventos publicados {published_event_types} deben coincidir con los esperados {expected_event_types}"

    @settings(max_examples=100)
    @given(article=valid_article_strategy())
    @pytest.mark.asyncio
    async def test_article_with_no_events_does_not_publish(self, article):
        """Para cualquier agregado sin eventos, save() no debe intentar publicar."""
        # Arrange - Limpiar eventos del artículo
        article._domain_events = []
        article._uncommitted_events = []

        mock_session = AsyncMock()

        # Mock execute to return a result with scalar_one_or_none that returns None (new article)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        repository = ArticleWriteRepository(
            session=mock_session,
            logger=None,
            event_publisher=mock_event_publisher,
        )

        # Act
        await repository.save(article)

        # Assert - No debe publicar eventos
        assert (
            mock_event_publisher.publish.call_count == 0
        ), "No debe publicar eventos cuando el agregado no tiene eventos"

    @settings(max_examples=50)
    @given(article=article_with_events_strategy())
    @pytest.mark.asyncio
    async def test_event_publishing_preserves_event_data(self, article):
        """Para cualquier agregado, los eventos publicados deben preservar todos los datos."""
        # Arrange
        mock_session = AsyncMock()

        # Mock execute to return a result with scalar_one_or_none that returns None (new article)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_event_publisher = AsyncMock()
        mock_event_publisher.publish = AsyncMock()

        repository = ArticleWriteRepository(
            session=mock_session,
            logger=None,
            event_publisher=mock_event_publisher,
        )

        # Capturar eventos originales
        expected_events = list(article.domain_events)

        # Act
        await repository.save(article)

        # Assert - Los datos de los eventos deben preservarse
        published_events = [
            call.args[0] for call in mock_event_publisher.publish.call_args_list
        ]

        for expected_event, published_event in zip(expected_events, published_events):
            # Verificar que los atributos clave se preservan
            assert (
                published_event.aggregate_id == expected_event.aggregate_id
            ), "El aggregate_id debe preservarse"

            # Verificar atributos específicos según el tipo de evento
            if isinstance(expected_event, RssArticleCreated):
                assert (
                    published_event.article_id == expected_event.article_id
                ), "El article_id debe preservarse en RssArticleCreated"
                assert (
                    published_event.source_id == expected_event.source_id
                ), "El source_id debe preservarse en RssArticleCreated"
                assert (
                    published_event.title == expected_event.title
                ), "El title debe preservarse en RssArticleCreated"

            elif isinstance(expected_event, RssArticleContentUpdated):
                assert (
                    published_event.article_id == expected_event.article_id
                ), "El article_id debe preservarse en RssArticleContentUpdated"
