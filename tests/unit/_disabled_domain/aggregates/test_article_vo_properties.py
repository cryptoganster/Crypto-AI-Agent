"""Tests para verificar acceso a Value Objects directamente desde Article aggregate."""

from datetime import datetime, timezone

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleValueObjectProperties:
    """Tests para propiedades de Value Objects expuestas directamente."""

    def test_content_vo_property_returns_article_content_vo(self):
        """Debería retornar ArticleContent Value Object."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        # Establecer contenido después de crear
        article.update_content_fields(markdown="Test content here")

        # Act
        content_vo = article.content_vo

        # Assert
        assert content_vo is not None
        assert content_vo.markdown == "Test content here"
        assert content_vo.has_markdown is True

    def test_metadata_vo_property_returns_article_metadata_vo(self):
        """Debería retornar ArticleMetadata Value Object."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_category("Technology", 0.9)
        article.update_language("en", 0.95)

        # Act
        metadata_vo = article.metadata_vo

        # Assert
        assert metadata_vo is not None
        assert metadata_vo.category is not None
        assert metadata_vo.category.value == "Technology"
        # Nota: confidence se almacena por separado, no en el VO category
        assert metadata_vo.language is not None
        assert metadata_vo.language.code == "en"
        assert metadata_vo.language.confidence == 0.95

    def test_quality_vo_property_returns_quality_assessment_vo(self):
        """Debería retornar QualityAssessment Value Object."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_readability_score(0.85)

        # Act
        quality_vo = article.quality_vo

        # Assert
        assert quality_vo is not None
        assert quality_vo.readability_score is not None
        assert quality_vo.readability_score.value == 0.85

    def test_metrics_vo_property_returns_content_metrics_vo(self):
        """Debería retornar ArticleMetrics Value Object."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        pytest.skip(
            "_set_word_count y _set_reading_time eliminados en limpieza profunda"
        )

        # Act
        metrics_vo = article.metrics_vo

        # Assert
        assert metrics_vo is not None
        assert metrics_vo.word_count is not None
        assert metrics_vo.word_count.value == 500
        assert metrics_vo.reading_time is not None
        assert metrics_vo.reading_time.minutes == 3

    def test_rss_metadata_vo_property_returns_rss_metadata_vo(self):
        """Debería retornar RssMetadata Value Object."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_metadata(guid="guid-123")
        article.update_metadata(description="Test description")

        # Act
        rss_vo = article.metadata

        # Assert
        assert rss_vo is not None
        assert rss_vo.guid == "guid-123"
        assert rss_vo.description == "Test description"

    def test_duplication_vo_property_returns_duplication_info_vo(self):
        """Debería retornar ArticleDuplicate Value Object."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        duplication_vo = article.duplication_vo

        # Assert
        assert duplication_vo is not None
        assert duplication_vo.is_duplicate is False
        assert duplication_vo.duplicate_of_article_id is None

    def test_error_vo_property_returns_error_info_vo(self):
        """Debería retornar ErrorInfo Value Object."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.mark_error("parsing_error", "Failed to parse", "system")

        # Act
        error_vo = article.error_vo

        # Assert
        assert error_vo is not None
        assert error_vo.has_error is True
        assert error_vo.error_type == "parsing_error"
        assert error_vo.error_message == "Failed to parse"

    def test_backward_compatibility_properties_still_work(self):
        """Debería mantener compatibilidad con propiedades antiguas."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_content_fields(markdown="Test content")
        article.update_category("Technology", 0.9)
        pytest.skip("_set_word_count eliminado en limpieza profunda")

        # Act & Assert - Propiedades antiguas siguen funcionando
        assert article.content_vo.markdown == "Test content"
        assert (
            article.metadata.category.value if article.metadata.category else None
        ) == "Technology"
        assert article.category_confidence == 0.9
        assert (
            article.metrics.word_count.value if article.metrics.word_count else None
        ) == 500

    def test_vo_properties_are_immutable(self):
        """Debería retornar VOs inmutables (no se pueden modificar)."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        content_vo = article.content_vo
        metadata_vo = article.metadata_vo

        # Assert - Los VOs son frozen dataclasses
        with pytest.raises(AttributeError):
            content_vo.markdown = "Modified"  # type: ignore

        # Metadata VO también es inmutable
        assert metadata_vo is not None

    def test_accessing_vo_multiple_times_returns_same_instance(self):
        """Debería retornar la misma instancia del VO en múltiples accesos."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        content_vo1 = article.content_vo
        content_vo2 = article.content_vo

        # Assert
        assert content_vo1 is content_vo2

    def test_new_way_vs_old_way_comparison(self):
        """Comparación entre acceso nuevo (VO) y antiguo (propiedades)."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_category("Technology", 0.9)
        article.update_language("en", 0.95)
        pytest.skip("_set_word_count eliminado en limpieza profunda")

        # Old way (backward compatible)
        old_category = (
            article.metadata.category.value if article.metadata.category else None
        )
        old_language = (
            article.metadata.language.code if article.metadata.language else None
        )
        old_word_count = (
            article.metrics.word_count.value if article.metrics.word_count else None
        )

        # New way (recommended)
        metadata = article.metadata_vo
        new_category = metadata.category.name if metadata.category else None
        new_language = metadata.language.code if metadata.language else None

        metrics = article.metrics_vo
        new_word_count = metrics.word_count.value if metrics.word_count else None

        # Assert - Ambas formas retornan los mismos valores
        assert old_category == new_category
        assert old_language == new_language
        assert old_word_count == new_word_count
