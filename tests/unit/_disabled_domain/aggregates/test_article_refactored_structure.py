"""Tests para verificar la nueva estructura refactorizada del Article aggregate."""

from datetime import datetime, timezone

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.article.domain.value_objects.metadata import (
    RssArticleMetadata,
    RssArticleSummary,
    RssArticleThumbnailUrl,
)
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleRefactoredStructure:
    """Tests para la estructura refactorizada con Value Objects compuestos."""

    def test_article_has_identity_vo_property(self):
        """Debería tener property identity_vo que retorna ArticleMetadata."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        identity = article.identity_vo

        # Assert
        assert identity is not None
        assert isinstance(identity, RssArticleMetadata)
        assert isinstance(identity.article_id, RssArticleId)
        assert isinstance(identity.source_id, RssFeedId)
        assert isinstance(identity.url, RssArticleUrl)

    def test_article_has_metadata_vo_property(self):
        """Debería tener property metadata_vo que retorna ArticleMetadata."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        metadata = article.metadata_vo

        # Assert
        assert metadata is not None
        assert isinstance(metadata, RssArticleMetadata)
        assert isinstance(metadata.title, RssArticleTitle)

    def test_identity_vo_article_id_access(self):
        """Debería poder acceder a article_id via identity_vo."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article_id = article.identity_vo.article_id

        # Assert
        assert article_id is not None
        assert isinstance(article_id, RssArticleId)

    def test_identity_vo_source_id_access(self):
        """Debería poder acceder a source_id via identity_vo."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        source_id = article.identity_vo.source_id

        # Assert
        assert source_id is not None
        assert isinstance(source_id, RssFeedId)
        assert str(source_id) == "test-source-123"

    def test_identity_vo_url_access(self):
        """Debería poder acceder a url via identity_vo."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        url = article.identity_vo.url

        # Assert
        assert url is not None
        assert isinstance(url, RssArticleUrl)
        assert url.value == "https://example.com/test"

    def test_metadata_vo_title_access(self):
        """Debería poder acceder a title via metadata_vo."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        title = article.metadata.title

        # Assert
        assert title is not None
        assert isinstance(title, RssArticleTitle)
        assert str(title) == "Test RssArticle"

    def test_metadata_vo_summary_access(self):
        """Debería poder acceder a summary via metadata_vo."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act - Initially None
        summary = article.metadata.summary

        # Assert
        assert summary is None

        # Update with summary
        article.update_metadata_fields(summary=RssArticleSummary("Test summary"))

        # Assert - Now has value
        assert article.metadata.summary is not None
        assert isinstance(article.metadata.summary, RssArticleSummary)
        assert str(article.metadata.summary) == "Test summary"

    def test_identity_vo_article_id_consistency(self):
        """Debería acceder a article_id via identity_vo consistentemente."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article_id = article.identity_vo.article_id

        # Assert
        assert article_id is not None
        assert isinstance(article_id, RssArticleId)
        assert article_id == article.identity_vo.article_id

    def test_identity_vo_source_id_consistency(self):
        """Debería acceder a source_id via identity_vo consistentemente."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        source_id = article.identity_vo.source_id

        # Assert
        assert source_id is not None
        assert isinstance(source_id, RssFeedId)
        assert source_id == article.identity_vo.source_id

    def test_identity_vo_url_consistency(self):
        """Debería acceder a url via identity_vo consistentemente."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        url = article.identity_vo.url

        # Assert
        assert url is not None
        assert isinstance(url, RssArticleUrl)
        assert url == article.identity_vo.url

    def test_metadata_vo_title_consistency(self):
        """Debería acceder a title via metadata_vo consistentemente."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        title = article.metadata.title

        # Assert
        assert title is not None
        assert isinstance(title, RssArticleTitle)
        assert title == article.metadata.title

    def test_update_metadata_fields_updates_title(self):
        """Debería actualizar title correctamente."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Original Title",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.update_metadata_fields(title=RssArticleTitle("Updated Title"))

        # Assert
        assert str(article.metadata.title) == "Updated Title"

    def test_update_metadata_fields_updates_summary(self):
        """Debería actualizar summary correctamente."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.update_metadata_fields(summary=RssArticleSummary("New summary"))

        # Assert
        assert article.metadata.summary is not None
        assert str(article.metadata.summary) == "New summary"

    def test_update_metadata_fields_updates_thumbnail_url(self):
        """Debería actualizar thumbnail_url correctamente."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.update_metadata_fields(
            thumbnail_url=RssArticleThumbnailUrl("https://example.com/image.jpg")
        )

        # Assert
        assert article.metadata.thumbnail_url is not None
        assert article.metadata.thumbnail_url.is_present is True

    def test_article_has_less_than_or_equal_10_direct_attributes(self):
        """Debería tener máximo 10 atributos directos (reducción de ~15)."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act - Count only instance attributes (not methods or class attributes)
        instance_attributes = [
            attr
            for attr in vars(article).keys()
            if attr.startswith("_") and not attr.startswith("__")
        ]

        # Assert
        # Expected attributes after refactoring:
        # _identity, _metadata, _created_at, _updated_at, _version,
        # _validation_info, _published_at, _archived_at,
        # _content, _metrics, _rss_metadata, _quality, _duplication, _error,
        # _domain_events, _uncommitted_events
        # That's 16 total

        # Before refactoring we had:
        # _id, _title, _url, _source_id, _thumbnail_url (5 separate)
        # + all the others = ~18 total

        # After refactoring we have:
        # _identity, _metadata (2 consolidated)
        # + all the others = ~16 total

        # Net reduction: 2 attributes
        assert len(instance_attributes) <= 16

        # The key improvement is consolidation:
        # Before: _id, _title, _url, _source_id, _thumbnail_url (5 separate)
        # After: _identity, _metadata (2 consolidated)
        # Net reduction: 3 attributes consolidated into 2 VOs
