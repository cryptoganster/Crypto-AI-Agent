"""
Property-Based Tests para creación de RssArticle aggregate.

Feature: article-aggregate-refactor, Property 5
Validates: Requirements 6.1
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleCreationProperties:
    """Property-based tests para validación de creación de Article."""

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_property_article_creation_with_valid_required_fields_succeeds(
        self, title: str, url: str, source_id: str
    ):
        """
        Property 5: RssArticle creation validates required fields.

        Para cualquier combinación de title, url y source_id válidos,
        crear un RssArticle debe tener éxito y validar que todos los campos
        requeridos están presentes y válidos a través de sus respectivos
        Value Objects.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 6.1
        """
        # Arrange - Crear SourceId VO
        source_id_vo = RssFeedId(source_id)

        # Act - Crear Article con campos requeridos válidos
        factory = RssArticleFactory()

        article = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
        )

        # Assert - Verificar que el artículo se creó correctamente
        assert article is not None
        assert article.id is not None
        assert isinstance(article.id, RssArticleId)

        # Verificar que los campos requeridos se almacenaron correctamente
        # Note: ArticleTitle normaliza el título (strip + elimina espacios extra)
        import re

        normalized_title = re.sub(r"\s+", " ", title.strip())
        assert article.title == normalized_title
        assert article.url == url
        assert article.source_id == source_id_vo

        # Verificar que se emitió evento de creación
        events = article.get_uncommitted_events()
        assert len(events) == 1
        assert events[0].event_type == "RssArticleCreated"

    @given(
        empty_title=st.one_of(
            st.just(""),
            st.just("   "),
            st.just("\t"),
            st.just("\n"),
            st.just("  \t\n  "),
        ),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_property_article_creation_rejects_empty_title(
        self, empty_title: str, url: str, source_id: str
    ):
        """
        Property 5: RssArticle creation validates required fields (empty title).

        Para cualquier title vacío o que solo contiene espacios en blanco,
        crear un RssArticle debe fallar con ValueError desde RssArticleTitle VO.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 6.1
        """
        # Arrange
        factory = RssArticleFactory()
        source_id_vo = RssFeedId(source_id)

        # Act & Assert - Intentar crear con título vacío debe fallar
        with pytest.raises(ValueError) as exc_info:
            factory.create_article(
                title=empty_title,
                url=url,
                source_id=source_id_vo,
            )

        # Verificar que el error viene de la validación del título
        error_msg = str(exc_info.value).lower()
        assert any(
            word in error_msg for word in ["title", "título", "empty", "vacío", "blank"]
        )

    @given(
        title=st.text(min_size=1, max_size=500).filter(
            lambda x: x.strip()
            and not x.strip().upper()
            in ["RSS:", "FEED:", "[RSS]", "[FEED]", "RSS -", "FEED:"]
        ),
        invalid_url=st.one_of(
            st.just(""),
            st.just("not-a-url"),
            st.just("ftp://invalid-protocol.com"),
            st.just("javascript:alert('xss')"),
            st.just("   "),
            st.text(min_size=1, max_size=50).filter(
                lambda x: not x.startswith(("http://", "https://"))
            ),
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_property_article_creation_rejects_invalid_url(
        self, title: str, invalid_url: str, source_id: str
    ):
        """
        Property 5: RssArticle creation validates required fields (invalid URL).

        Para cualquier URL inválida (vacía, sin protocolo http/https, o formato incorrecto),
        crear un RssArticle debe fallar con ValueError desde RssArticleUrl VO.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 6.1
        """
        # Arrange
        factory = RssArticleFactory()
        source_id_vo = RssFeedId(source_id)

        # Act & Assert - Intentar crear con URL inválida debe fallar
        with pytest.raises(ValueError) as exc_info:
            factory.create_article(
                title=title,
                url=invalid_url,
                source_id=source_id_vo,
            )

        # Verificar que el error viene de la validación (URL o título)
        # Nota: El factory limpia títulos (remueve prefijos RSS), por lo que
        # el error puede ser de título vacío O de URL inválida
        error_msg = str(exc_info.value).lower()
        assert any(
            word in error_msg
            for word in [
                "url",
                "http",
                "https",
                "protocol",
                "invalid",
                "inválid",
                "título",
                "title",
                "vacío",
                "empty",
            ]
        )

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
    )
    @settings(max_examples=100)
    def test_property_article_creation_requires_source_id(self, title: str, url: str):
        """
        Property 5: RssArticle creation validates required fields (missing source_id).

        Para cualquier combinación de title y url válidos, crear un RssArticle
        sin source_id debe fallar con ValueError.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 6.1
        """
        # Arrange
        factory = RssArticleFactory()

        # Act & Assert - Intentar crear sin source_id debe fallar
        with pytest.raises((ValueError, TypeError)) as exc_info:
            factory.create_article(
                title=title,
                url=url,
                source_id=None,  # type: ignore
            )

        # Verificar que el error indica que source_id es requerido
        error_msg = str(exc_info.value).lower()
        assert any(
            word in error_msg
            for word in ["source", "required", "requerido", "none", "null"]
        )

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_property_article_creation_without_optional_fields_succeeds(
        self, title: str, url: str, source_id: str
    ):
        """
        Property 5: RssArticle creation validates required fields (minimal creation).

        Para cualquier combinación de campos requeridos válidos, crear un RssArticle
        sin campos opcionales debe tener éxito. Solo title, url y source_id son
        requeridos en la creación.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 6.1
        """
        # Arrange
        source_id_vo = RssFeedId(source_id)

        # Act - Crear Article solo con campos requeridos
        factory = RssArticleFactory()

        article = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
        )

        # Assert - Verificar que el artículo se creó correctamente
        assert article is not None

        # Note: ArticleTitle normaliza el título (strip + elimina espacios extra)
        import re

        normalized_title = re.sub(r"\s+", " ", title.strip())
        assert article.title == normalized_title
        assert article.url == url
        assert article.source_id == source_id_vo

        # Verificar que campos opcionales están en su estado inicial
        assert article.content_vo.markdown is None
        assert article.content_vo.has_markdown is False
        assert article.metadata.summary is None
        assert article.metadata.author is None

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_property_article_creation_generates_deterministic_id(
        self, title: str, url: str, source_id: str
    ):
        """
        Property 5: RssArticle creation validates required fields (deterministic ID).

        Para cualquier combinación de source_id y url, crear dos Articles
        con los mismos valores debe generar el mismo ID determinístico.
        Esto previene duplicados basados en source + url.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 6.1
        """
        # Arrange
        factory = RssArticleFactory()
        source_id_vo = RssFeedId(source_id)

        # Act - Crear dos artículos con los mismos source_id y url
        article1 = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
        )

        article2 = factory.create_article(
            title=title + " (different title)",  # Título diferente
            url=url,  # Misma URL
            source_id=source_id_vo,  # Mismo source_id
        )

        # Assert - Los IDs deben ser iguales (determinísticos basados en source + url)
        assert (
            article1.id == article2.id
        ), "Articles con mismo source_id y url deben tener el mismo ID determinístico"

    @given(
        title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        url=st.from_regex(
            r"https?://[a-z0-9\-]+\.[a-z]{2,}(/[a-z0-9\-]*)*", fullmatch=True
        ),
        source_id=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_property_article_creation_accepts_custom_id(
        self, title: str, url: str, source_id: str
    ):
        """
        Property 5: RssArticle creation validates required fields (custom ID).

        Para cualquier combinación de campos requeridos válidos y un article_id
        personalizado (UUID válido), crear un RssArticle debe usar el ID proporcionado
        en lugar del ID determinístico.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 6.1
        """
        # Arrange
        import uuid

        source_id_vo = RssFeedId(source_id)
        # Generar UUID válido para el test
        custom_uuid = str(uuid.uuid4())
        custom_article_id = RssArticleId(custom_uuid)

        # Act - Crear Article con ID personalizado
        factory = RssArticleFactory()

        article = factory.create_article(
            title=title,
            url=url,
            source_id=source_id_vo,
            article_id=custom_article_id,
        )

        # Assert - Verificar que se usó el ID personalizado
        assert article.id == custom_article_id
        assert str(article.id) == custom_uuid
