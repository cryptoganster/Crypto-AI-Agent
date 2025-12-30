"""Tests para RssArticleFactory con Value Objects compuestos.

Tests específicos para validar que RssArticleFactory crea correctamente
RssArticleMetadata y RssArticleMetadata con todos sus campos.

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 9.4
"""

from datetime import datetime, timezone

import pytest

from src.rss.article.domain.factories.article_factory import FeedItem, RssArticleFactory
from src.rss.article.domain.value_objects.metadata import RssArticleMetadata
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleIdentityCreation:
    """Tests para creación de RssArticleMetadata.

    Validates: Requirements 6.1
    """

    @pytest.fixture
    def factory(self):
        """Factory instance para tests."""
        return RssArticleFactory()

    @pytest.fixture
    def valid_source_id(self):
        """Source ID válido para tests."""
        return RssFeedId("test-source-123")

    def test_create_article_creates_article_identity_correctly(
        self, factory, valid_source_id
    ):
        """Debería crear ArticleMetadata con id, source_id, title y url."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id
        )

        # Assert
        assert hasattr(article, "metadata")
        assert isinstance(article.metadata, RssArticleMetadata)
        assert article.metadata.id is not None
        assert article.metadata.source_id == valid_source_id
        assert str(article.metadata.title) == title
        assert str(article.metadata.url) == url

    def test_create_article_generates_deterministic_article_id(
        self, factory, valid_source_id
    ):
        """ArticleMetadata debería tener article_id determinístico basado en source y URL."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"

        # Act
        article1 = factory.create_article(
            title=title, url=url, source_id=valid_source_id
        )
        article2 = factory.create_article(
            title=title, url=url, source_id=valid_source_id
        )

        # Assert
        assert str(article1.identity.id) == str(article2.identity.id)

    def test_create_article_identity_is_immutable(self, factory, valid_source_id):
        """ArticleMetadata debería ser inmutable (frozen)."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id
        )

        # Assert
        with pytest.raises(AttributeError):
            article.identity.id = "new-id"  # type: ignore

    def test_create_article_with_custom_article_id(self, factory, valid_source_id):
        """Debería aceptar article_id personalizado en ArticleMetadata."""
        # Arrange
        import uuid

        from src.rss.article.domain.value_objects import RssArticleId

        title = "Test RssArticle"
        url = "https://example.com/article"
        custom_id = RssArticleId(str(uuid.uuid4()))

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id, article_id=custom_id
        )

        # Assert
        assert article.identity.id == custom_id


class TestRssArticleMetadataCreation:
    """Tests para creación de RssArticleMetadata con title.

    Validates: Requirements 6.2
    """

    @pytest.fixture
    def factory(self):
        """Factory instance para tests."""
        return RssArticleFactory()

    @pytest.fixture
    def valid_source_id(self):
        """Source ID válido para tests."""
        return RssFeedId("test-source-123")

    def test_create_article_creates_article_metadata_with_title(
        self, factory, valid_source_id
    ):
        """Debería crear ArticleMetadata con title correctamente."""
        # Arrange
        title = "Test RssArticle Title"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id
        )

        # Assert
        assert hasattr(article, "metadata_vo")
        assert isinstance(article.metadata, RssArticleMetadata)
        assert article.metadata.title is not None
        assert str(article.metadata.title) == title

    def test_create_article_metadata_with_summary(self, factory, valid_source_id):
        """Debería crear ArticleMetadata con summary cuando se proporciona description."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"
        description = "This is a test summary"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id, description=description
        )

        # Assert
        assert article.metadata.summary is not None
        assert str(article.metadata.summary) == description

    def test_create_article_metadata_with_thumbnail_url(self, factory, valid_source_id):
        """Debería crear ArticleMetadata con thumbnail_url cuando se proporciona."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"
        thumbnail_url = "https://example.com/thumb.jpg"

        # Act
        article = factory.create_article(
            title=title,
            url=url,
            source_id=valid_source_id,
            thumbnail_url=thumbnail_url,
        )

        # Assert
        assert article.metadata.thumbnail_url is not None
        assert str(article.metadata.thumbnail_url) == thumbnail_url

    def test_create_article_metadata_is_immutable(self, factory, valid_source_id):
        """ArticleMetadata debería ser inmutable (frozen)."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id
        )

        # Assert
        with pytest.raises(AttributeError):
            article.metadata.title = "new title"  # type: ignore


class TestTitleValidation:
    """Tests para validación de title.

    Validates: Requirements 6.3
    """

    @pytest.fixture
    def factory(self):
        """Factory instance para tests."""
        return RssArticleFactory()

    @pytest.fixture
    def valid_source_id(self):
        """Source ID válido para tests."""
        return RssFeedId("test-source-123")

    def test_create_article_with_empty_title_raises_error(
        self, factory, valid_source_id
    ):
        """Debería rechazar título vacío."""
        # Arrange
        title = ""
        url = "https://example.com/article"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            factory.create_article(title=title, url=url, source_id=valid_source_id)

        assert "Validación de RssArticle fallida" in str(exc_info.value)

    def test_create_article_with_whitespace_only_title_raises_error(
        self, factory, valid_source_id
    ):
        """Debería rechazar título con solo espacios."""
        # Arrange
        title = "   "
        url = "https://example.com/article"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            factory.create_article(title=title, url=url, source_id=valid_source_id)

        assert "Validación de RssArticle fallida" in str(exc_info.value)

    def test_create_article_with_very_long_title_raises_error(
        self, factory, valid_source_id
    ):
        """Debería rechazar título muy largo (> 500 caracteres)."""
        # Arrange
        title = "A" * 501
        url = "https://example.com/article"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            factory.create_article(title=title, url=url, source_id=valid_source_id)

        assert "Validación de RssArticle fallida" in str(exc_info.value)

    def test_create_article_with_valid_title_succeeds(self, factory, valid_source_id):
        """Debería aceptar título válido."""
        # Arrange
        title = "Valid RssArticle Title"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id
        )

        # Assert
        assert article is not None
        assert str(article.metadata.title) == title


class TestTitleCleaning:
    """Tests para limpieza de title.

    Validates: Requirements 6.4
    """

    @pytest.fixture
    def factory(self):
        """Factory instance para tests."""
        return RssArticleFactory()

    @pytest.fixture
    def valid_source_id(self):
        """Source ID válido para tests."""
        return RssFeedId("test-source-123")

    def test_clean_title_removes_rss_prefix(self, factory, valid_source_id):
        """Debería remover prefijo 'RSS:' del título."""
        # Arrange
        dirty_title = "RSS: RssArticle Title"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=dirty_title, url=url, source_id=valid_source_id
        )

        # Assert
        assert "RSS:" not in str(article.metadata.title)
        assert str(article.metadata.title) == "RssArticle Title"

    def test_clean_title_removes_feed_prefix(self, factory, valid_source_id):
        """Debería remover prefijo 'FEED:' del título."""
        # Arrange
        dirty_title = "FEED: RssArticle Title"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=dirty_title, url=url, source_id=valid_source_id
        )

        # Assert
        assert "FEED:" not in str(article.metadata.title)
        assert str(article.metadata.title) == "RssArticle Title"

    def test_clean_title_removes_rss_suffix(self, factory, valid_source_id):
        """Debería remover sufijo ' - RSS' del título."""
        # Arrange
        dirty_title = "RssArticle Title - RSS"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=dirty_title, url=url, source_id=valid_source_id
        )

        # Assert
        assert " - RSS" not in str(article.metadata.title)
        assert str(article.metadata.title) == "RssArticle Title"

    def test_clean_title_removes_extra_spaces(self, factory, valid_source_id):
        """Debería remover espacios extra del título."""
        # Arrange
        dirty_title = "  RssArticle   Title   With   Spaces  "
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=dirty_title, url=url, source_id=valid_source_id
        )

        # Assert
        title_str = str(article.metadata.title)
        assert "   " not in title_str
        assert not title_str.startswith(" ")
        assert not title_str.endswith(" ")


class TestSummaryCleaning:
    """Tests para limpieza de summary.

    Validates: Requirements 6.4
    """

    @pytest.fixture
    def factory(self):
        """Factory instance para tests."""
        return RssArticleFactory()

    @pytest.fixture
    def valid_source_id(self):
        """Source ID válido para tests."""
        return RssFeedId("test-source-123")

    def test_clean_summary_removes_extra_spaces(self, factory, valid_source_id):
        """Debería remover espacios extra del summary."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"
        dirty_summary = "  Summary   with   extra   spaces  "

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id, description=dirty_summary
        )

        # Assert
        summary_str = str(article.metadata.summary)
        assert "   " not in summary_str
        assert not summary_str.startswith(" ")
        assert not summary_str.endswith(" ")

    def test_clean_summary_removes_summary_prefix(self, factory, valid_source_id):
        """Debería remover prefijo 'Summary:' del summary."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"
        dirty_summary = "Summary: This is the actual summary"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id, description=dirty_summary
        )

        # Assert
        summary_str = str(article.metadata.summary)
        assert "Summary:" not in summary_str
        assert summary_str == "This is the actual summary"

    def test_clean_summary_handles_none(self, factory, valid_source_id):
        """Debería manejar summary None correctamente."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id, description=None
        )

        # Assert
        assert article.metadata.summary is None


class TestFeedItemMapping:
    """Tests para mapeo de FeedItem a Value Objects compuestos.

    Validates: Requirements 6.5
    """

    @pytest.fixture
    def factory(self):
        """Factory instance para tests."""
        return RssArticleFactory()

    @pytest.fixture
    def valid_source_id(self):
        """Source ID válido para tests."""
        return RssFeedId("test-source-123")

    def test_create_from_feed_item_maps_title_correctly(self, factory, valid_source_id):
        """Debería mapear title de FeedItem a ArticleMetadata."""
        # Arrange
        feed_item = FeedItem(
            title="Feed RssArticle Title", link="https://example.com/feed"
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item, source_id=valid_source_id, quality_assessment=False
        )

        # Assert
        assert str(article.metadata.title) == "Feed RssArticle Title"

    def test_create_from_feed_item_maps_url_correctly(self, factory, valid_source_id):
        """Debería mapear link de FeedItem a ArticleMetadata.url."""
        # Arrange
        feed_item = FeedItem(
            title="Feed RssArticle", link="https://example.com/feed-article"
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item, source_id=valid_source_id, quality_assessment=False
        )

        # Assert
        assert "example.com" in str(article.identity.url)

    def test_create_from_feed_item_maps_description_to_summary(
        self, factory, valid_source_id
    ):
        """Debería mapear description de FeedItem a ArticleMetadata.summary."""
        # Arrange
        feed_item = FeedItem(
            title="Feed RssArticle",
            link="https://example.com/feed",
            description="This is the article description",
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item, source_id=valid_source_id, quality_assessment=False
        )

        # Assert
        assert article.metadata.summary is not None
        assert str(article.metadata.summary) == "This is the article description"

    def test_create_from_feed_item_creates_article_identity(
        self, factory, valid_source_id
    ):
        """Debería crear ArticleMetadata desde FeedItem."""
        # Arrange
        feed_item = FeedItem(
            title="Feed RssArticle", link="https://example.com/feed-article"
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item, source_id=valid_source_id, quality_assessment=False
        )

        # Assert
        assert isinstance(article.identity, RssArticleMetadata)
        assert article.identity.source_id == valid_source_id

    def test_create_from_feed_item_creates_article_metadata(
        self, factory, valid_source_id
    ):
        """Debería crear ArticleMetadata desde FeedItem."""
        # Arrange
        feed_item = FeedItem(
            title="Feed RssArticle",
            link="https://example.com/feed",
            description="RssArticle description",
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item, source_id=valid_source_id, quality_assessment=False
        )

        # Assert
        assert isinstance(article.metadata, RssArticleMetadata)
        assert article.metadata.title is not None
        assert article.metadata.summary is not None

    def test_create_from_feed_item_with_all_metadata(self, factory, valid_source_id):
        """Debería mapear todos los campos de FeedItem a Value Objects compuestos."""
        # Arrange
        pub_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        feed_item = FeedItem(
            title="Complete Feed RssArticle",
            link="https://example.com/complete",
            description="RssArticle description",
            content="Full article content",
            pub_date=pub_date,
            author="John Doe",
            categories=["tech", "python"],
            guid="feed-guid-123",
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item, source_id=valid_source_id, quality_assessment=False
        )

        # Assert
        # ArticleMetadata
        assert isinstance(article.identity, RssArticleMetadata)
        assert article.identity.source_id == valid_source_id

        # ArticleMetadata
        assert isinstance(article.metadata, RssArticleMetadata)
        assert str(article.metadata.title) == "Complete Feed RssArticle"
        assert article.metadata.summary is not None
        assert str(article.metadata.author) == "John Doe"


class TestBackwardCompatibility:
    """Tests para verificar backward compatibility con API legacy.

    Validates: Requirements 9.4
    """

    @pytest.fixture
    def factory(self):
        """Factory instance para tests."""
        return RssArticleFactory()

    @pytest.fixture
    def valid_source_id(self):
        """Source ID válido para tests."""
        return RssFeedId("test-source-123")

    def test_article_id_property_works(self, factory, valid_source_id):
        """Property article.id debería funcionar (backward compatibility)."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id
        )

        # Assert
        assert article.id is not None
        assert article.id == article.identity.id

    def test_article_title_property_works(self, factory, valid_source_id):
        """Property article.metadata.title debería funcionar."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id
        )

        # Assert
        assert article.metadata.title is not None
        assert str(article.metadata.title) == title

    def test_article_source_id_property_works(self, factory, valid_source_id):
        """Property article.identity.source_id debería funcionar."""
        # Arrange
        title = "Test RssArticle"
        url = "https://example.com/article"

        # Act
        article = factory.create_article(
            title=title, url=url, source_id=valid_source_id
        )

        # Assert
        assert article.identity.source_id is not None
        assert article.identity.source_id == valid_source_id
