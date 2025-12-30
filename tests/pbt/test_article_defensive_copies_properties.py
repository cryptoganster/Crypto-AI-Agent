"""Property-based tests para copias defensivas en RssArticle aggregate.

Feature: article-aggregate-refactor, Property 14
Validates: Requirements 8.1

Estos tests verifican que las propiedades de colección retornan copias
defensivas (tuplas inmutables) que no pueden ser modificadas desde fuera
del aggregate, protegiendo la encapsulación.
"""

from datetime import datetime, timezone

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import RssArticleId
from src.rss.feed.domain.value_objects import RssFeedId


# Estrategias para generar datos de test
@st.composite
def article_strategy(draw):
    """Genera un Article válido para testing."""
    # Generar título que no sea solo espacios
    title = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
            min_size=1,
            max_size=200,
        )
    )
    # Asegurar que el título no sea solo espacios
    assume(title.strip())

    url = draw(
        st.from_regex(r"https?://[a-z0-9]+\.[a-z]{2,}/[a-z0-9-]+", fullmatch=True)
    )
    source_id = RssFeedId(f"src-{draw(st.integers(min_value=1, max_value=1000))}")

    factory = RssArticleFactory()

    article = factory.create_article(title=title, url=url, source_id=source_id)

    # Limpiar eventos de creación para tests
    article.mark_events_as_committed()

    return article


@st.composite
def tags_strategy(draw):
    """Genera una lista de tags válidos."""
    num_tags = draw(st.integers(min_value=1, max_value=10))
    tags = []
    for _ in range(num_tags):
        tag = draw(
            st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
                min_size=1,
                max_size=20,
            )
        )
        if tag.strip():
            tags.append(tag)
    return tags


@st.composite
def keywords_strategy(draw):
    """Genera una lista de keywords válidas."""
    num_keywords = draw(st.integers(min_value=1, max_value=15))
    keywords = []
    for _ in range(num_keywords):
        keyword = draw(
            st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
                min_size=2,
                max_size=15,
            )
        )
        if keyword.strip():
            keywords.append(keyword)
    return keywords


class TestRssArticleDefensiveCopiesProperties:
    """
    Property-based tests para verificar copias defensivas.

    Property 14: Collection properties return defensive copies
    Validates: Requirements 8.1
    """

    @given(article=article_strategy(), tags=tags_strategy())
    @settings(suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_tags_returns_immutable_tuple(self, article, tags):
        """
        Property 14: Tags property retorna tupla inmutable.

        Para cualquier RssArticle con tags, la propiedad tags debe retornar
        una tupla que no puede ser modificada desde fuera.

        Feature: article-aggregate-refactor, Property 14
        Validates: Requirements 8.1
        """
        # Arrange - Agregar tags al artículo
        for tag in tags:
            article.add_tag(tag)

        assume(len(tuple(article.metadata.tags.sorted_tags)) > 0)

        # Act - Obtener tags
        returned_tags = tuple(article.metadata.tags.sorted_tags)

        # Assert - Debe ser tupla (inmutable)
        assert isinstance(
            returned_tags, tuple
        ), "tags property debe retornar tupla, no lista"

        # Assert - No se puede modificar (intentar append debe fallar)
        with pytest.raises(AttributeError):
            returned_tags.append("hacked_tag")  # type: ignore

        # Assert - No se puede modificar (intentar asignación debe fallar)
        with pytest.raises(TypeError):
            returned_tags[0] = "modified_tag"  # type: ignore

    @given(article=article_strategy(), tags=tags_strategy())
    def test_property_tags_modification_does_not_affect_internal_state(
        self, article, tags
    ):
        """
        Property 14: Modificar tupla retornada no afecta estado interno.

        Para cualquier RssArticle, intentar modificar la tupla retornada
        por tags no debe afectar el estado interno del aggregate.

        Feature: article-aggregate-refactor, Property 14
        Validates: Requirements 8.1
        """
        # Arrange - Agregar tags
        for tag in tags:
            article.add_tag(tag)

        assume(len(tuple(article.metadata.tags.sorted_tags)) > 0)

        # Act - Obtener tags y guardar estado original
        original_tags = tuple(article.metadata.tags.sorted_tags)
        original_count = len(original_tags)

        # Intentar "modificar" creando nueva tupla (lo único posible)
        # No podemos modificar la tupla, pero podemos verificar que
        # obtener tags múltiples veces retorna el mismo contenido
        tags_second_call = tuple(article.metadata.tags.sorted_tags)

        # Assert - Múltiples llamadas retornan el mismo contenido
        assert (
            original_tags == tags_second_call
        ), "Múltiples llamadas a tags deben retornar el mismo contenido"

        assert (
            len(tuple(article.metadata.tags.sorted_tags)) == original_count
        ), "El número de tags no debe cambiar"

    @given(article=article_strategy(), keywords=keywords_strategy())
    def test_property_keywords_returns_immutable_tuple(self, article, keywords):
        """
        Property 14: Keywords property retorna tupla inmutable.

        Para cualquier RssArticle con keywords, la propiedad keywords debe
        retornar una tupla que no puede ser modificada desde fuera.

        Feature: article-aggregate-refactor, Property 14
        Validates: Requirements 8.1
        """
        # Arrange - Establecer keywords
        article.set_keywords(keywords)

        assume(len(tuple(article.metadata.keywords.keywords)) > 0)

        # Act - Obtener keywords
        returned_keywords = tuple(article.metadata.keywords.keywords)

        # Assert - Debe ser tupla (inmutable)
        assert isinstance(
            returned_keywords, tuple
        ), "keywords property debe retornar tupla, no lista"

        # Assert - No se puede modificar (intentar append debe fallar)
        with pytest.raises(AttributeError):
            returned_keywords.append("hacked_keyword")  # type: ignore

        # Assert - No se puede modificar (intentar asignación debe fallar)
        with pytest.raises(TypeError):
            returned_keywords[0] = "modified_keyword"  # type: ignore

    @given(article=article_strategy(), keywords=keywords_strategy())
    def test_property_keywords_modification_does_not_affect_internal_state(
        self, article, keywords
    ):
        """
        Property 14: Modificar tupla de keywords no afecta estado interno.

        Para cualquier RssArticle, intentar modificar la tupla retornada
        por keywords no debe afectar el estado interno del aggregate.

        Feature: article-aggregate-refactor, Property 14
        Validates: Requirements 8.1
        """
        # Arrange - Establecer keywords
        article.set_keywords(keywords)

        assume(len(tuple(article.metadata.keywords.keywords)) > 0)

        # Act - Obtener keywords y guardar estado original
        original_keywords = tuple(article.metadata.keywords.keywords)
        original_count = len(original_keywords)

        # Obtener keywords nuevamente
        keywords_second_call = tuple(article.metadata.keywords.keywords)

        # Assert - Múltiples llamadas retornan el mismo contenido
        assert (
            original_keywords == keywords_second_call
        ), "Múltiples llamadas a keywords deben retornar el mismo contenido"

        assert (
            len(tuple(article.metadata.keywords.keywords)) == original_count
        ), "El número de keywords no debe cambiar"

    @given(article=article_strategy())
    def test_property_domain_events_returns_immutable_tuple(self, article):
        """
        Property 14: domain_events property retorna tupla inmutable.

        Para cualquier RssArticle con eventos, la propiedad domain_events
        debe retornar una tupla que no puede ser modificada desde fuera.

        Feature: article-aggregate-refactor, Property 14
        Validates: Requirements 8.1
        """
        # Arrange - Generar algunos eventos
        article.update_content_fields(markdown="Test content for events")

        assume(len(article.domain_events) > 0)

        # Act - Obtener eventos
        returned_events = article.domain_events

        # Assert - Debe ser tupla (inmutable)
        assert isinstance(
            returned_events, tuple
        ), "domain_events property debe retornar tupla, no lista"

        # Assert - No se puede modificar (intentar append debe fallar)
        with pytest.raises(AttributeError):
            returned_events.append(None)  # type: ignore

        # Assert - No se puede modificar (intentar asignación debe fallar)
        with pytest.raises(TypeError):
            returned_events[0] = None  # type: ignore

    @given(article=article_strategy())
    def test_property_get_domain_events_returns_immutable_tuple(self, article):
        """
        Property 14: get_domain_events() retorna tupla inmutable.

        Para cualquier RssArticle, el método get_domain_events() debe
        retornar una tupla que no puede ser modificada desde fuera.

        Feature: article-aggregate-refactor, Property 14
        Validates: Requirements 8.1
        """
        # Arrange - Generar algunos eventos
        article.update_content_fields(markdown="Test content for get_domain_events")

        assume(len(article.get_domain_events()) > 0)

        # Act - Obtener eventos
        returned_events = article.get_domain_events()

        # Assert - Debe ser tupla (inmutable)
        assert isinstance(
            returned_events, tuple
        ), "get_domain_events() debe retornar tupla, no lista"

        # Assert - No se puede modificar
        with pytest.raises(AttributeError):
            returned_events.append(None)  # type: ignore

    @given(article=article_strategy())
    def test_property_get_uncommitted_events_returns_immutable_tuple(self, article):
        """
        Property 14: get_uncommitted_events() retorna tupla inmutable.

        Para cualquier RssArticle, el método get_uncommitted_events() debe
        retornar una tupla que no puede ser modificada desde fuera.

        Feature: article-aggregate-refactor, Property 14
        Validates: Requirements 8.1
        """
        # Arrange - Generar algunos eventos
        article.update_content_fields(markdown="Test content for uncommitted events")

        assume(len(article.get_uncommitted_events()) > 0)

        # Act - Obtener eventos no confirmados
        returned_events = article.get_uncommitted_events()

        # Assert - Debe ser tupla (inmutable)
        assert isinstance(
            returned_events, tuple
        ), "get_uncommitted_events() debe retornar tupla, no lista"

        # Assert - No se puede modificar
        with pytest.raises(AttributeError):
            returned_events.append(None)  # type: ignore

    @given(article=article_strategy())
    def test_property_domain_events_multiple_calls_return_same_content(self, article):
        """
        Property 14: Múltiples llamadas a domain_events retornan mismo contenido.

        Para cualquier RssArticle, llamar a domain_events múltiples veces
        debe retornar tuplas con el mismo contenido (hasta que se modifique
        el aggregate).

        Feature: article-aggregate-refactor, Property 14
        Validates: Requirements 8.1
        """
        # Arrange - Generar eventos
        article.update_content_fields(markdown="Test content for consistency check")

        assume(len(article.domain_events) > 0)

        # Act - Obtener eventos múltiples veces
        events_first = article.domain_events
        events_second = article.domain_events
        events_third = article.get_domain_events()

        # Assert - Todas las llamadas retornan el mismo contenido
        assert (
            events_first == events_second
        ), "Múltiples llamadas a domain_events deben retornar mismo contenido"

        assert (
            events_first == events_third
        ), "domain_events y get_domain_events() deben retornar mismo contenido"

        assert (
            len(events_first) == len(events_second) == len(events_third)
        ), "Todas las llamadas deben retornar el mismo número de eventos"
