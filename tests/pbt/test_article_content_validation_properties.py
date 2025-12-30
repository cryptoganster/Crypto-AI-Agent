"""
Property-Based Tests para validaciones de contenido en RssArticle aggregate.

Feature: article-aggregate-refactor, Property 6
Validates: Requirements 6.2
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import RssArticleTitle, RssArticleUrl
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleContentValidationProperties:
    """Property-based tests para validación de contenido."""

    @given(
        empty_content=st.one_of(
            st.just(""),
            st.just("   "),
            st.just("\t"),
            st.just("\n"),
            st.just("  \t\n  "),
        )
    )
    @settings(max_examples=100)
    def test_property_update_content_rejects_empty_values(self, empty_content: str):
        """
        Property 6: Content updates reject empty values.

        Para cualquier RssArticle, llamar update_content() con un string vacío
        o que solo contiene espacios en blanco debe lanzar ValueError.

        Feature: article-aggregate-refactor, Property 6
        Validates: Requirements 6.2
        """
        # Arrange - Crear Article válido
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert - Intentar actualizar con contenido vacío debe fallar
        with pytest.raises(ValueError) as exc_info:
            article.update_content_fields(markdown=empty_content)

        # Verificar mensaje de error apropiado
        assert (
            "vacío" in str(exc_info.value).lower()
            or "empty" in str(exc_info.value).lower()
        )

    @given(valid_content=st.text(min_size=1, max_size=1000).filter(lambda x: x.strip()))
    @settings(max_examples=100)
    def test_property_update_content_accepts_valid_values(self, valid_content: str):
        """
        Property 6 (inverso): Content updates accept valid non-empty values.

        Para cualquier RssArticle, llamar update_content() con un string no vacío
        debe actualizar el contenido exitosamente.

        Feature: article-aggregate-refactor, Property 6
        Validates: Requirements 6.2
        """
        # Arrange - Crear Article válido
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act - Actualizar con contenido válido
        article.update_content_fields(markdown=valid_content)

        # Assert - El contenido debe haberse actualizado
        assert article.content_vo.markdown == valid_content
        assert article.content_vo.has_markdown is True

    @given(
        core_content=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(blacklist_categories=("Cs", "Cc")),
        ),
        leading_spaces=st.integers(min_value=0, max_value=5),
        trailing_spaces=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=100)
    def test_property_update_content_preserves_meaningful_whitespace(
        self, core_content: str, leading_spaces: int, trailing_spaces: int
    ):
        """
        Property 6 (edge case): Content with leading/trailing whitespace is accepted.

        Para cualquier RssArticle, llamar update_content() con contenido que tiene
        espacios al inicio o final pero contiene texto válido debe ser aceptado.

        Feature: article-aggregate-refactor, Property 6
        Validates: Requirements 6.2
        """
        # Arrange - Crear Article válido
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Construir contenido con whitespace
        content_with_whitespace = (
            (" " * leading_spaces) + core_content + (" " * trailing_spaces)
        )

        # Solo probar si el contenido tiene algo más que espacios
        if not content_with_whitespace.strip():
            return  # Skip este caso, ya está cubierto por otro test

        # Act - Actualizar con contenido que tiene whitespace pero es válido
        article.update_content_fields(markdown=content_with_whitespace)

        # Assert - El contenido debe haberse actualizado (preservando whitespace)
        assert article.content_vo.markdown == content_with_whitespace
        assert article.content_vo.has_markdown is True
