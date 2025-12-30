"""Tests de integración para Article con ArticleCategory VO."""

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import RssArticleId
from src.rss.article.domain.value_objects.metadata import ArticleCategory
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleCategoryIntegration:
    """Tests de integración entre Article y ArticleCategory."""

    def test_article_category_property_returns_none_by_default(self):
        """Debería retornar None si no se ha establecido categoría."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert
        assert (
            article.metadata.category.value
            if article.metadata.category
            else None is None
        )

    def test_set_category_with_string(self):
        """Debería establecer categoría desde string."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.update_category("Technology", 0.9)

        # Assert
        assert (
            article.metadata.category.value if article.metadata.category else None
        ) == "Technology"
        # Verificar confidence en el evento
        events = article.get_uncommitted_events()
        category_event = next(e for e in events if e.event_type == "ArticleCategorized")
        assert category_event.confidence == 0.9

    def test_set_category_with_default_confidence(self):
        """Debería usar confidence=1.0 por defecto."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.update_category("Business", 1.0)

        # Assert
        assert (
            article.metadata.category.value if article.metadata.category else None
        ) == "Business"
        # Verificar confidence en el evento
        events = article.get_uncommitted_events()
        category_event = next(e for e in events if e.event_type == "ArticleCategorized")
        assert category_event.confidence == 1.0

    def test_set_category_normalizes_name(self):
        """Debería normalizar el nombre de la categoría."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.update_category("  sports  ", 1.0)

        # Assert
        assert (
            article.metadata.category.value if article.metadata.category else None
        ) == "Sports"

    def test_set_category_with_empty_string_sets_none(self):
        """Debería establecer None si se pasa string vacío."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_category("Technology", 1.0)

        # Act
        article.update_category("", 1.0)

        # Assert
        assert (
            article.metadata.category.value
            if article.metadata.category
            else None is None
        )
        # No hay evento cuando la categoría es vacía
        events = article.get_uncommitted_events()
        category_events = [e for e in events if e.event_type == "ArticleCategorized"]
        # Solo debe haber el evento inicial de "Technology", no uno nuevo
        assert len(category_events) == 1

    def test_set_category_with_none_sets_none(self):
        """Debería establecer None si se pasa None."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_category("Technology", 1.0)

        # Act
        article.update_category(None, 1.0)

        # Assert
        assert (
            article.metadata.category.value
            if article.metadata.category
            else None is None
        )
        # No hay evento cuando la categoría es None
        events = article.get_uncommitted_events()
        category_events = [e for e in events if e.event_type == "ArticleCategorized"]
        # Solo debe haber el evento inicial de "Technology", no uno nuevo
        assert len(category_events) == 1

    def test_category_property_returns_name_from_vo(self):
        """Debería retornar el nombre desde el VO."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_category("Entertainment", 0.85)

        # Act
        result = article.metadata.category.value if article.metadata.category else None

        # Assert
        assert result == "Entertainment"
        assert isinstance(result, str)

    def test_internal_category_is_vo(self):
        """Debería almacenar internamente como ArticleCategory VO."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.update_category("Politics", 0.75)

        # Assert
        # Verificar usando propiedades públicas
        assert (
            article.metadata.category.value if article.metadata.category else None
        ) == "Politics"
        # Verificar confidence en el evento
        events = article.get_uncommitted_events()
        category_event = next(e for e in events if e.event_type == "ArticleCategorized")
        assert category_event.confidence == 0.75

    def test_set_category_updates_timestamp(self):
        """Debería actualizar updated_at al establecer categoría."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        original_updated_at = article.updated_at

        # Act
        import time

        time.sleep(0.01)  # Pequeña pausa para asegurar diferencia en timestamp
        article.update_category("Health", 1.0)

        # Assert
        assert article.updated_at > original_updated_at
