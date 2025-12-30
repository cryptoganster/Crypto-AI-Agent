"""
Property-Based Tests para validación de marcado de duplicados en RssArticle aggregate.

Feature: article-aggregate-refactor, Property 7
Validates: Requirements 6.3
"""

from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.feed.domain.value_objects import RssFeedId


# Strategy para generar UUIDs válidos
def uuid_strategy():
    """Genera UUIDs válidos como strings."""
    return st.builds(lambda: str(uuid4()))


class TestRssArticleDuplicateMarkingProperties:
    """Property-based tests para validación de marcado de duplicados."""

    @given(original_uuid=uuid_strategy())
    @settings(max_examples=100)
    def test_property_mark_as_duplicate_requires_valid_article_id(
        self, original_uuid: str
    ):
        """
        Property 7: Duplicate marking requires original article ID.

        Para cualquier RssArticle, llamar mark_as_duplicate() con un RssArticleId válido
        debe marcar el artículo como duplicado exitosamente.

        Feature: article-aggregate-refactor, Property 7
        Validates: Requirements 6.3
        """
        # Arrange - Crear Article válido
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Crear ArticleId válido del original
        original_article_id = RssArticleId(original_uuid)

        # Act - Marcar como duplicado con ID válido
        article.mark_as_duplicate(original_article_id)

        # Assert - El artículo debe estar marcado como duplicado
        assert article.duplication_vo.is_duplicate is True
        assert article.duplication_vo.duplicate_of_article_id == original_article_id
        assert article.archived_at is not None

    def test_property_mark_as_duplicate_rejects_none(self):
        """
        Property 7: Duplicate marking rejects None.

        Para cualquier RssArticle, llamar mark_as_duplicate() con None
        debe lanzar ValueError.

        Feature: article-aggregate-refactor, Property 7
        Validates: Requirements 6.3
        """
        # Arrange - Crear Article válido
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert - Intentar marcar como duplicado sin ID debe fallar
        with pytest.raises(ValueError) as exc_info:
            article.mark_as_duplicate(None)

        # Verificar mensaje de error apropiado
        assert (
            "requerido" in str(exc_info.value).lower()
            or "required" in str(exc_info.value).lower()
        )

    @given(
        invalid_value=st.one_of(
            st.just("not-a-uuid"),
            st.just("   "),
            st.integers(),
            st.floats(),
            st.booleans(),
            st.lists(st.text()),
            st.dictionaries(st.text(), st.text()),
        )
    )
    @settings(max_examples=100)
    def test_property_mark_as_duplicate_rejects_invalid_types(self, invalid_value):
        """
        Property 7: Duplicate marking rejects invalid types.

        Para cualquier RssArticle, llamar mark_as_duplicate() con un valor
        que no es RssArticleId debe lanzar error.

        Feature: article-aggregate-refactor, Property 7
        Validates: Requirements 6.3
        """
        # Arrange - Crear Article válido
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert - Intentar marcar como duplicado con tipo inválido debe fallar
        with pytest.raises((ValueError, TypeError, AttributeError)):
            article.mark_as_duplicate(invalid_value)

    @given(original_uuid_1=uuid_strategy(), original_uuid_2=uuid_strategy())
    @settings(max_examples=100)
    def test_property_mark_as_duplicate_can_be_called_multiple_times(
        self, original_uuid_1: str, original_uuid_2: str
    ):
        """
        Property 7 (edge case): Duplicate marking can be updated.

        Para cualquier RssArticle, llamar mark_as_duplicate() múltiples veces
        debe actualizar el ID del artículo original.

        Feature: article-aggregate-refactor, Property 7
        Validates: Requirements 6.3
        """
        # Arrange - Crear Article válido
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act - Marcar como duplicado dos veces
        original_1 = RssArticleId(original_uuid_1)
        original_2 = RssArticleId(original_uuid_2)

        article.mark_as_duplicate(original_1)
        first_archived_at = article.archived_at

        article.mark_as_duplicate(original_2)
        second_archived_at = article.archived_at

        # Assert - El último ID debe prevalecer
        assert article.duplication_vo.is_duplicate is True
        assert article.duplication_vo.duplicate_of_article_id == original_2
        assert article.archived_at is not None
        # El segundo archived_at debe ser igual o posterior al primero
        assert second_archived_at >= first_archived_at
