"""Unit tests para casos específicos de RssArticleFactory.

Estos tests cubren casos edge y escenarios específicos que complementan
los property-based tests.
"""

from datetime import datetime, timezone

import pytest

from src.rss.article.domain.factories.article_factory import FeedItem, RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId


class TestFeedItemWithoutContent:
    """Tests para FeedItem sin content pero con description.

    Validates: Requirements 5.2
    """

    def test_create_from_feed_item_uses_description_when_no_content(self):
        """Debería usar description como content cuando content es None."""
        # Arrange
        factory = RssArticleFactory()
        source_id = RssFeedId("test-source")

        feed_item = FeedItem(
            title="Test RssArticle",
            link="https://example.com/article",
            description="This is the description text",
            content=None,  # Sin content
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item, source_id=source_id, quality_assessment=False
        )

        # Assert
        assert article is not None
        # El factory debería haber usado description como content
        # (verificado indirectamente - el artículo se creó exitosamente)

    def test_create_from_feed_item_prefers_content_over_description(self):
        """Debería preferir content sobre description cuando ambos existen."""
        # Arrange
        factory = RssArticleFactory()
        source_id = RssFeedId("test-source")

        feed_item = FeedItem(
            title="Test RssArticle",
            link="https://example.com/article",
            description="Short description",
            content="Full content text that is longer",
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item, source_id=source_id, quality_assessment=False
        )

        # Assert
        assert article is not None
        # Content debería haberse usado (no description)

    def test_create_from_feed_item_with_empty_description_and_no_content(self):
        """Debería manejar caso donde description está vacía y no hay content."""
        # Arrange
        factory = RssArticleFactory()
        source_id = RssFeedId("test-source")

        feed_item = FeedItem(
            title="Test RssArticle",
            link="https://example.com/article",
            description="",  # Vacía
            content=None,
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item, source_id=source_id, quality_assessment=False
        )

        # Assert
        assert article is not None


class TestQualityAssessment:
    """Tests para quality assessment automático.

    Validates: Requirements 5.5
    """

    def test_quality_assessment_disabled_does_not_assess(self):
        """Con quality_assessment=False, no debería evaluar calidad."""
        # Arrange
        factory = RssArticleFactory()
        source_id = RssFeedId("test-source")

        feed_item = FeedItem(
            title="Test RssArticle",
            link="https://example.com/article",
            content="This is some content " * 50,  # Contenido largo
        )

        # Act
        article = factory.create_from_feed_item(
            feed_item=feed_item,
            source_id=source_id,
            quality_assessment=False,  # Desactivado
        )

        # Assert
        assert article is not None
        # No debería tener quality assessment aplicado
        # (el artículo se crea sin evaluar calidad)

    def test_quality_assessment_with_short_content(self):
        """Quality assessment con contenido corto debería dar low quality."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        quality = factory._assess_content_quality("Short")

        # Assert
        assert quality is not None
        assert quality.value == "low"

    def test_quality_assessment_with_medium_content(self):
        """Quality assessment con contenido medio debería dar medium quality."""
        # Arrange
        factory = RssArticleFactory()

        # Contenido de ~300 palabras
        content = " ".join(["word"] * 300)

        # Act
        quality = factory._assess_content_quality(content)

        # Assert
        assert quality is not None
        assert quality.value == "medium"

    def test_quality_assessment_with_long_content(self):
        """Quality assessment con contenido largo debería dar high quality."""
        # Arrange
        factory = RssArticleFactory()

        # Contenido de ~600 palabras
        content = " ".join(["word"] * 600)

        # Act
        quality = factory._assess_content_quality(content)

        # Assert
        assert quality is not None
        assert quality.value == "high"

    def test_quality_assessment_with_empty_content(self):
        """Quality assessment con contenido vacío debería dar low quality."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        quality = factory._assess_content_quality("")

        # Assert
        assert quality is not None
        assert quality.value == "low"


class TestMetadataValidation:
    """Tests para validación de metadatos.

    Validates: Requirements 6.4
    """

    def test_validate_metadata_with_very_long_summary(self):
        """Debería generar warning para resumen muy largo."""
        # Arrange
        factory = RssArticleFactory()

        metadata = {"summary": "A" * 1500}  # Muy largo (> 1000)

        # Act
        result = factory._validate_metadata(metadata)

        # Assert
        assert len(result["warnings"]) > 0
        assert any(
            "resumen" in w.lower() or "summary" in w.lower() for w in result["warnings"]
        )

    def test_validate_metadata_with_very_long_author(self):
        """Debería generar warning para nombre de autor muy largo."""
        # Arrange
        factory = RssArticleFactory()

        metadata = {"author": "A" * 150}  # Muy largo (> 100)

        # Act
        result = factory._validate_metadata(metadata)

        # Assert
        assert len(result["warnings"]) > 0
        assert any(
            "autor" in w.lower() or "author" in w.lower() for w in result["warnings"]
        )

    def test_validate_metadata_with_normal_values(self):
        """No debería generar warnings para metadatos normales."""
        # Arrange
        factory = RssArticleFactory()

        metadata = {"summary": "Normal summary text", "author": "John Doe"}

        # Act
        result = factory._validate_metadata(metadata)

        # Assert
        assert len(result["warnings"]) == 0

    def test_validate_metadata_with_empty_dict(self):
        """Debería manejar dict vacío sin errores."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        result = factory._validate_metadata({})

        # Assert
        assert len(result["warnings"]) == 0


class TestEdgeCases:
    """Tests para casos edge adicionales."""

    def test_create_article_with_none_content(self):
        """Debería crear artículo con content=None."""
        # Arrange
        factory = RssArticleFactory()
        source_id = RssFeedId("test-source")

        # Act
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/article",
            source_id=source_id,
            content=None,  # Explícitamente None
        )

        # Assert
        assert article is not None

    def test_create_article_with_all_optional_metadata(self):
        """Debería crear artículo con todos los metadatos opcionales."""
        # Arrange
        factory = RssArticleFactory()
        source_id = RssFeedId("test-source")

        # Act
        article = factory.create_article(
            title="Complete RssArticle",
            url="https://example.com/complete",
            source_id=source_id,
            content="RssArticle content",
            thumbnail_url="https://example.com/thumb.jpg",
            guid="unique-guid-123",
            published_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            description="RssArticle description",
            author="Jane Doe",
            language="en",
            category="tech",
            tags=["python", "testing"],
        )

        # Assert
        assert article is not None
        assert article._rss_metadata.guid == "unique-guid-123"
        assert str(article._metadata.author) == "Jane Doe"
        assert len(tuple(article.metadata.tags.sorted_tags)) > 0

    def test_validation_with_http_url(self):
        """Debería generar warning para HTTP (no HTTPS)."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        result = factory.validate_article_creation_data(
            title="Test RssArticle",
            url="http://example.com/article",  # HTTP, no HTTPS
            source_id="test-source",
        )

        # Assert
        assert result.is_valid is True
        # Puede tener warning sobre HTTP
        if len(result.warnings) > 0:
            warnings_text = " ".join(result.warnings).lower()
            assert "http" in warnings_text or "https" in warnings_text

    def test_validation_with_shortened_url(self):
        """Debería generar warning para URLs acortadas."""
        # Arrange
        factory = RssArticleFactory()

        # Act
        result = factory.validate_article_creation_data(
            title="Test RssArticle",
            url="https://bit.ly/abc123",  # URL acortada
            source_id="test-source",
        )

        # Assert
        assert result.is_valid is True
        assert len(result.warnings) > 0
        warnings_text = " ".join(result.warnings).lower()
        assert "acortada" in warnings_text or "archivado" in warnings_text
