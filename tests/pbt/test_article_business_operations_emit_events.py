"""Property-based tests para emisión de eventos en operaciones de negocio.

**Feature: article-aggregate-refactor, Property 9: Business operations emit domain events**

**Validates: Requirements 7.1, 15.5**

Para cualquier operación de negocio en el RssArticle aggregate, la operación debe
emitir al menos un evento de dominio que capture el cambio realizado.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# Importar componentes del sistema
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.events.article_content_updated import (
    RssArticleContentUpdated,
)
from src.rss.article.domain.events.article_created import RssArticleCreated
from src.rss.article.domain.events.article_error_marked import ArticleErrorMarked
from src.rss.article.domain.events.article_validated import ArticleValidated
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.article.domain.value_objects.validation_info import ValidationInfo
from src.rss.feed.domain.value_objects import RssFeedId
from src.shared.domain.value_objects import Level

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
def valid_title_strategy(draw):
    """Genera títulos válidos para artículos."""
    title = draw(
        st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        )
    )
    # Asegurar que no sea solo espacios en blanco
    if not title.strip():
        title = "Test RssArticle"
    return title


@st.composite
def valid_url_strategy(draw):
    """Genera URLs válidas."""
    domain = draw(
        st.text(
            min_size=3,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Ll",)),
        )
    )
    path = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
        )
    )
    return f"https://{domain}.com/{path}"


@st.composite
def valid_content_strategy(draw):
    """Genera contenido válido para artículos."""
    content = draw(
        st.text(
            min_size=10,
            max_size=1000,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        )
    )
    # Asegurar que no sea solo espacios en blanco
    if not content.strip():
        content = "This is test content for the article with sufficient length."
    return content


@st.composite
def valid_article_strategy(draw):
    """Genera Article válidos para testing."""
    title = draw(valid_title_strategy())
    url = draw(valid_url_strategy())
    source_id = draw(valid_source_id_strategy())
    article_id = RssArticleId(str(draw(valid_uuid_strategy())))

    # Crear artículo usando factory method
    factory = RssArticleFactory()

    article = factory.create_article(
        title=title,
        url=url,
        source_id=source_id,
        article_id=article_id,
    )

    # Limpiar eventos de creación para tests de operaciones posteriores
    article.mark_events_as_committed()

    return article


# ============================================================================
# PROPERTY TEST: BUSINESS OPERATIONS EMIT EVENTS
# ============================================================================


class TestBusinessOperationsEmitEvents:
    """**Feature: article-aggregate-refactor, Property 9: Business operations emit domain events**

    **Validates: Requirements 7.1, 15.5**

    Para cualquier operación de negocio en el RssArticle aggregate, la operación
    debe emitir al menos un evento de dominio.
    """

    @settings(max_examples=100)
    @given(
        title=valid_title_strategy(),
        url=valid_url_strategy(),
        source_id=valid_source_id_strategy(),
    )
    def test_create_operation_emits_article_created_event(self, title, url, source_id):
        """Para cualquier creación de Article, debe emitirse ArticleCreated."""
        # Act
        factory = RssArticleFactory()

        article = factory.create_article(title=title, url=url, source_id=source_id)

        # Assert - Debe haber al menos un evento
        uncommitted_events = article.get_uncommitted_events()
        assert (
            len(uncommitted_events) >= 1
        ), "create() debe emitir al menos un evento de dominio"

        # Assert - El primer evento debe ser ArticleCreated
        first_event = uncommitted_events[0]
        assert isinstance(
            first_event, RssArticleCreated
        ), f"El primer evento debe ser RssArticleCreated, pero fue {type(first_event)}"

        # Assert - El evento debe contener los datos correctos
        assert first_event.article_id == str(
            article.id
        ), "El evento debe contener el article_id correcto"
        assert first_event.source_id == str(
            source_id
        ), "El evento debe contener el source_id correcto"
        # Comparar con el título normalizado del artículo (ArticleTitle normaliza el input)
        assert (
            first_event.title == article.title
        ), "El evento debe contener el título correcto (normalizado)"
        assert first_event.url == url, "El evento debe contener la URL correcta"

    @settings(max_examples=100)
    @given(article=valid_article_strategy(), new_content=valid_content_strategy())
    def test_update_content_emits_content_updated_event(self, article, new_content):
        """Para cualquier actualización de contenido, debe emitirse ArticleContentUpdated."""
        # Arrange - Asegurar que no hay eventos previos
        assert (
            len(article.get_uncommitted_events()) == 0
        ), "El artículo debe empezar sin eventos no confirmados"

        # Act
        article.update_content_fields(markdown=new_content)

        # Assert - Debe haber al menos un evento
        uncommitted_events = article.get_uncommitted_events()
        assert (
            len(uncommitted_events) >= 1
        ), "update_content() debe emitir al menos un evento de dominio"

        # Assert - El evento debe ser ArticleContentUpdated
        event = uncommitted_events[0]
        assert isinstance(
            event, RssArticleContentUpdated
        ), f"El evento debe ser RssArticleContentUpdated, pero fue {type(event)}"

        # Assert - El evento debe contener los datos correctos
        assert event.article_id == str(
            article.id
        ), "El evento debe contener el article_id correcto"
        assert (
            event.updated_fields["content"] == new_content
        ), "El evento debe contener el nuevo contenido"

    @settings(max_examples=100)
    @given(
        article=valid_article_strategy(),
        validation_score=st.floats(min_value=0.0, max_value=1.0),
        validated_by=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        ),
    )
    def test_validate_article_emits_validated_event(
        self, article, validation_score, validated_by
    ):
        """Para cualquier validación de artículo, debe emitirse ArticleValidated."""
        # Arrange
        assume(validated_by.strip())  # Asegurar que no es solo espacios

        # Arrange - Asegurar que no hay eventos previos
        assert (
            len(article.get_uncommitted_events()) == 0
        ), "El artículo debe empezar sin eventos no confirmados"

        # Act
        article.validate_article(validation_score, validated_by)

        # Assert - Debe haber al menos un evento
        uncommitted_events = article.get_uncommitted_events()
        assert (
            len(uncommitted_events) >= 1
        ), "validate_article() debe emitir al menos un evento de dominio"

        # Assert - El evento debe ser ArticleValidated
        event = uncommitted_events[0]
        assert isinstance(
            event, ArticleValidated
        ), f"El evento debe ser ArticleValidated, pero fue {type(event)}"

        # Assert - El evento debe contener los datos correctos
        assert event.article_id == str(
            article.id
        ), "El evento debe contener el article_id correcto"
        assert (
            event.validation_score == validation_score
        ), "El evento debe contener el validation_score correcto"

    @settings(max_examples=100)
    @given(
        article=valid_article_strategy(),
        error_type=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        ),
        error_message=st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        ),
        marked_by=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        ),
    )
    def test_mark_error_emits_error_marked_event(
        self, article, error_type, error_message, marked_by
    ):
        """Para cualquier marcado de error, debe emitirse ArticleErrorMarked."""
        # Arrange
        assume(error_type.strip())  # Asegurar que no es solo espacios
        assume(error_message.strip())  # Asegurar que no es solo espacios
        assume(marked_by.strip())  # Asegurar que no es solo espacios

        # Arrange - Asegurar que no hay eventos previos
        assert (
            len(article.get_uncommitted_events()) == 0
        ), "El artículo debe empezar sin eventos no confirmados"

        # Act
        article.mark_error(error_type, error_message, marked_by)

        # Assert - Debe haber al menos un evento
        uncommitted_events = article.get_uncommitted_events()
        assert (
            len(uncommitted_events) >= 1
        ), "mark_error() debe emitir al menos un evento de dominio"

        # Assert - El evento debe ser ArticleErrorMarked
        event = uncommitted_events[0]
        assert isinstance(
            event, ArticleErrorMarked
        ), f"El evento debe ser ArticleErrorMarked, pero fue {type(event)}"

        # Assert - El evento debe contener los datos correctos
        assert event.article_id == str(
            article.id
        ), "El evento debe contener el article_id correcto"
        assert (
            event.error_type == error_type
        ), "El evento debe contener el error_type correcto"
        assert (
            event.error_message == error_message
        ), "El evento debe contener el error_message correcto"

    @settings(max_examples=100)
    @given(article=valid_article_strategy())
    def test_all_business_operations_emit_at_least_one_event(self, article):
        """Para cualquier operación de negocio, debe emitirse al menos un evento."""
        # Test 1: update_content
        article.mark_events_as_committed()
        article.update_content_fields(markdown="New content for testing")
        assert (
            len(article.get_uncommitted_events()) >= 1
        ), "update_content() debe emitir al menos un evento"

        # Test 2: validate_article
        article.mark_events_as_committed()
        article.validate_article(0.8, "test_validator")
        assert (
            len(article.get_uncommitted_events()) >= 1
        ), "validate_article() debe emitir al menos un evento"

        # Test 3: mark_error
        article.mark_events_as_committed()
        article.mark_error("test_error", "Test error message", "test_marker")
        assert (
            len(article.get_uncommitted_events()) >= 1
        ), "mark_error() debe emitir al menos un evento"

    @settings(max_examples=50)
    @given(
        article=valid_article_strategy(),
        content1=valid_content_strategy(),
        content2=valid_content_strategy(),
    )
    def test_multiple_operations_accumulate_events(self, article, content1, content2):
        """Para múltiples operaciones de negocio, los eventos deben acumularse."""
        # Arrange - Asegurar que no hay eventos previos
        assert len(article.get_uncommitted_events()) == 0

        # Act - Realizar múltiples operaciones
        article.update_content_fields(markdown=content1)
        first_event_count = len(article.get_uncommitted_events())

        article.update_content_fields(markdown=content2)
        second_event_count = len(article.get_uncommitted_events())

        article.validate_article(0.7, "validator")
        third_event_count = len(article.get_uncommitted_events())

        # Assert - Los eventos deben acumularse
        assert first_event_count >= 1, "Primera operación debe emitir evento"
        assert (
            second_event_count > first_event_count
        ), "Segunda operación debe agregar más eventos"
        assert (
            third_event_count > second_event_count
        ), "Tercera operación debe agregar más eventos"

        # Assert - Debe haber al menos 3 eventos (uno por operación)
        assert (
            third_event_count >= 3
        ), "Debe haber al menos 3 eventos después de 3 operaciones"

    @settings(max_examples=100)
    @given(article=valid_article_strategy(), new_content=valid_content_strategy())
    def test_events_contain_aggregate_id(self, article, new_content):
        """Para cualquier evento emitido, debe contener el aggregate_id correcto."""
        # Act
        article.update_content_fields(markdown=new_content)

        # Assert
        events = article.get_uncommitted_events()
        for event in events:
            assert hasattr(
                event, "aggregate_id"
            ), "Todos los eventos deben tener aggregate_id"
            assert event.aggregate_id == str(
                article.id
            ), "El aggregate_id del evento debe coincidir con el ID del artículo"

    @settings(max_examples=100)
    @given(article=valid_article_strategy(), new_content=valid_content_strategy())
    def test_events_are_immutable_after_emission(self, article, new_content):
        """Para cualquier evento emitido, debe ser inmutable."""
        # Act
        article.update_content_fields(markdown=new_content)

        # Assert
        events = article.get_uncommitted_events()
        assert len(events) > 0, "Debe haber al menos un evento"

        # Intentar modificar el evento (debe fallar o no tener efecto)
        first_event = events[0]
        original_article_id = first_event.article_id

        # Los eventos son dataclasses frozen, intentar modificar debe fallar
        try:
            first_event.article_id = "modified-id"
            # Si no falla, verificar que no se modificó
            assert (
                first_event.article_id == original_article_id
            ), "Los eventos deben ser inmutables"
        except (AttributeError, TypeError):
            # Esperado: los eventos frozen no permiten modificación
            pass

    @settings(max_examples=50)
    @given(
        title=valid_title_strategy(),
        url=valid_url_strategy(),
        source_id=valid_source_id_strategy(),
        content=valid_content_strategy(),
    )
    def test_create_and_update_emit_different_event_types(
        self, title, url, source_id, content
    ):
        """Para diferentes operaciones, deben emitirse diferentes tipos de eventos."""
        # Act - Crear artículo
        factory = RssArticleFactory()

        article = factory.create_article(title=title, url=url, source_id=source_id)
        create_events = list(article.get_uncommitted_events())

        # Act - Actualizar contenido
        article.mark_events_as_committed()
        article.update_content_fields(markdown=content)
        update_events = list(article.get_uncommitted_events())

        # Assert - Los tipos de eventos deben ser diferentes
        assert len(create_events) > 0, "create() debe emitir eventos"
        assert len(update_events) > 0, "update_content() debe emitir eventos"

        assert type(create_events[0]) != type(
            update_events[0]
        ), "create() y update_content() deben emitir tipos de eventos diferentes"

        assert isinstance(
            create_events[0], RssArticleCreated
        ), "create() debe emitir RssArticleCreated"
        assert isinstance(
            update_events[0], RssArticleContentUpdated
        ), "update_content() debe emitir RssArticleContentUpdated"
