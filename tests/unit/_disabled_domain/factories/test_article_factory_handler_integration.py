"""Tests para verificar que handlers usan RssArticleFactory correctamente."""

from datetime import datetime

import pytest

from src.rss.article.domain.factories.article_factory import FeedItem, RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleFactoryHandlerIntegration:
    """Tests para verificar integración entre handlers y RssArticleFactory."""

    def test_factory_accepts_string_title_and_creates_article_title_vo(self):
        """Factory debe aceptar string para title y crear ArticleTitle VO internamente."""
        # Arrange
        factory = RssArticleFactory()
        title_string = "Test RssArticle Title"
        url_string = "https://example.com/article"
        source_id = RssFeedId("src-123")

        # Act
        article = factory.create_article(
            title=title_string,
            url=url_string,
            source_id=source_id,
        )

        # Assert
        assert article.metadata.title.value == title_string

    def test_factory_accepts_string_summary_and_creates_article_summary_vo(self):
        """Factory debe aceptar string para description y crear ArticleSummary VO internamente."""
        # Arrange
        factory = RssArticleFactory()
        title_string = "Test RssArticle"
        url_string = "https://example.com/article"
        source_id = RssFeedId("src-123")
        summary_string = "This is a test summary"

        # Act
        article = factory.create_article(
            title=title_string,
            url=url_string,
            source_id=source_id,
            description=summary_string,  # description se convierte en summary
        )

        # Assert
        assert article.metadata.summary is not None
        assert article.metadata.summary.value == summary_string

    def test_factory_accepts_string_thumbnail_url_and_creates_thumbnail_url_vo(self):
        """Factory debe aceptar string para thumbnail_url y crear ArticleThumbnailUrl VO internamente."""
        # Arrange
        factory = RssArticleFactory()
        title_string = "Test RssArticle"
        url_string = "https://example.com/article"
        source_id = RssFeedId("src-123")
        thumbnail_string = "https://example.com/image.jpg"

        # Act
        article = factory.create_article(
            title=title_string,
            url=url_string,
            source_id=source_id,
            thumbnail_url=thumbnail_string,
        )

        # Assert
        assert article.metadata.thumbnail_url is not None
        assert article.metadata.thumbnail_url.value == thumbnail_string

    def test_factory_create_from_feed_item_handles_all_string_parameters(self):
        """Factory debe manejar FeedItem con todos los parámetros como strings."""
        # Arrange
        factory = RssArticleFactory()
        source_id = RssFeedId("src-123")

        feed_item = FeedItem(
            title="RSS Feed RssArticle",
            link="https://example.com/rss-article",
            description="RSS article description",
            content="Full RSS article content",
            pub_date=datetime.now(),
            author="John Doe",
            categories=["Technology", "News"],
            guid="unique-guid-123",
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item,
            source_id=source_id,
            quality_assessment=False,
        )

        # Assert
        # Verificar que todos los strings se convirtieron a VOs correctamente
        assert article.metadata.title.value == "RSS Feed RssArticle"
        assert article.metadata.summary is not None
        assert article.metadata.summary.value == "RSS article description"
        assert article.identity_vo.url.value == "https://example.com/rss-article"
        assert article.identity_vo.source_id == source_id

    def test_handler_pattern_passes_strings_to_factory(self):
        """Simula el patrón que usan los handlers: pasar strings al factory."""
        # Arrange
        factory = RssArticleFactory()

        # Simular datos que vienen de un handler (todos strings)
        article_data = {
            "title": "Handler RssArticle",
            "url": "https://example.com/handler-article",
            "source_id": RssFeedId("src-456"),
            "content": "RssArticle content from handler",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "description": "RssArticle description from handler",
            "author": "Jane Smith",
            "tags": ["tag1", "tag2"],
        }

        # Act - Handler llama al factory con strings
        article = factory.create_article(**article_data)

        # Assert - Factory creó todos los VOs correctamente
        assert article.metadata.title.value == "Handler RssArticle"
        assert article.metadata.summary.value == "RssArticle description from handler"
        assert article.metadata.thumbnail_url.value == "https://example.com/thumb.jpg"
        assert article.identity_vo.url.value == "https://example.com/handler-article"
        assert article.identity_vo.source_id == RssFeedId("src-456")

    def test_factory_cleans_title_before_creating_vo(self):
        """Factory debe limpiar title antes de crear ArticleTitle VO."""
        # Arrange
        factory = RssArticleFactory()
        dirty_title = "RSS: Test RssArticle - RSS"
        url_string = "https://example.com/article"
        source_id = RssFeedId("src-123")

        # Act
        article = factory.create_article(
            title=dirty_title,
            url=url_string,
            source_id=source_id,
        )

        # Assert - Title debe estar limpio
        assert article.metadata.title.value == "Test RssArticle"
        assert "RSS:" not in article.metadata.title.value
        assert "- RSS" not in article.metadata.title.value

    def test_factory_cleans_summary_before_creating_vo(self):
        """Factory debe limpiar summary antes de crear ArticleSummary VO."""
        # Arrange
        factory = RssArticleFactory()
        title_string = "Test RssArticle"
        url_string = "https://example.com/article"
        source_id = RssFeedId("src-123")
        dirty_summary = "Summary:   This is a   test   summary   "

        # Act
        article = factory.create_article(
            title=title_string,
            url=url_string,
            source_id=source_id,
            description=dirty_summary,
        )

        # Assert - Summary debe estar limpio
        assert article.metadata.summary is not None
        assert article.metadata.summary.value == "This is a test summary"
        assert "Summary:" not in article.metadata.summary.value

    def test_factory_validates_title_and_raises_error_for_invalid_input(self):
        """Factory debe validar title y lanzar error si es inválido."""
        # Arrange
        factory = RssArticleFactory()
        empty_title = ""
        url_string = "https://example.com/article"
        source_id = RssFeedId("src-123")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            factory.create_article(
                title=empty_title,
                url=url_string,
                source_id=source_id,
            )

        assert "Validación de RssArticle fallida" in str(exc_info.value)

    def test_factory_creates_composite_value_objects_correctly(self):
        """Factory debe crear ArticleMetadata y ArticleMetadata correctamente."""
        # Arrange
        factory = RssArticleFactory()
        title_string = "Test RssArticle"
        url_string = "https://example.com/article"
        source_id = RssFeedId("src-123")
        summary_string = "Test summary"
        thumbnail_string = "https://example.com/thumb.jpg"

        # Act
        article = factory.create_article(
            title=title_string,
            url=url_string,
            source_id=source_id,
            description=summary_string,
            thumbnail_url=thumbnail_string,
        )

        # Assert - Verificar que los VOs compuestos se crearon correctamente
        # ArticleMetadata
        assert article.identity_vo is not None
        assert article.identity_vo.article_id is not None
        assert article.identity_vo.source_id == source_id
        assert article.identity_vo.url.value == url_string

        # ArticleMetadata
        assert article.metadata_vo is not None
        assert article.metadata.title.value == title_string
        assert article.metadata.summary.value == summary_string
        assert article.metadata.thumbnail_url.value == thumbnail_string
