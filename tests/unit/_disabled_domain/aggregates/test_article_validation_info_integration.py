"""Tests de integración para Article con ValidationInfo VO."""

from datetime import datetime, timedelta, timezone

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects.validation_info import ValidationInfo
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleValidationInfoIntegration:
    """Tests de integración entre Article y ValidationInfo."""

    def test_article_validation_properties_return_none_by_default(self):
        """Debería retornar None si no se ha validado el artículo."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert
        assert article.validation_info is None

    def test_validate_article_creates_validation_info(self):
        """Debería crear ValidationInfo al validar artículo."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.validate_article(validation_score=0.85, validated_by="admin")

        # Assert
        assert isinstance(article._validation_info, ValidationInfo)
        assert article.validation_info.score == 0.85
        assert article.validation_info.validated_by == "admin"
        assert article.validation_info.validated_at is not None

    def test_validation_score_property_returns_value_from_vo(self):
        """Debería retornar el score desde el VO."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.validate_article(validation_score=0.72, validated_by="system")

        # Act
        result = article.validation_info.score

        # Assert
        assert result == 0.72
        assert isinstance(result, float)

    def test_validated_by_property_returns_value_from_vo(self):
        """Debería retornar el validador desde el VO."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.validate_article(validation_score=0.65, validated_by="user123")

        # Act
        result = article.validation_info.validated_by

        # Assert
        assert result == "user123"
        assert isinstance(result, str)

    def test_validated_at_property_returns_value_from_vo(self):
        """Debería retornar el timestamp desde el VO."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.validate_article(validation_score=0.90, validated_by="admin")

        # Act
        result = article.validation_info.validated_at

        # Assert
        assert result is not None
        assert isinstance(result, datetime)
        assert result.tzinfo is not None  # Debe tener timezone

    def test_validate_article_updates_timestamp(self):
        """Debería actualizar updated_at al validar."""
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

        time.sleep(0.01)
        article.validate_article(validation_score=0.75, validated_by="system")

        # Assert
        assert article.updated_at > original_updated_at

    def test_validation_info_vo_quality_level_detection(self):
        """Debería detectar nivel de calidad desde el VO."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.validate_article(validation_score=0.85, validated_by="admin")

        # Act & Assert
        assert article._validation_info.is_high_quality()
        assert not article._validation_info.is_low_quality()
        assert not article._validation_info.is_medium_quality()

    def test_validation_info_vo_medium_quality_detection(self):
        """Debería detectar calidad media."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.validate_article(validation_score=0.55, validated_by="system")

        # Act & Assert
        assert article._validation_info.is_medium_quality()
        assert not article._validation_info.is_high_quality()
        assert not article._validation_info.is_low_quality()

    def test_validation_info_vo_low_quality_detection(self):
        """Debería detectar baja calidad."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.validate_article(validation_score=0.25, validated_by="system")

        # Act & Assert
        assert article._validation_info.is_low_quality()
        assert not article._validation_info.is_high_quality()
        assert not article._validation_info.is_medium_quality()

    def test_validation_info_vo_get_quality_level(self):
        """Debería obtener nivel de calidad como string."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.validate_article(validation_score=0.80, validated_by="admin")

        # Act
        level = article._validation_info.get_quality_level()

        # Assert
        assert level == "high"

    def test_validation_info_vo_is_recent(self):
        """Debería verificar si la validación es reciente."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.validate_article(validation_score=0.70, validated_by="system")

        # Act & Assert
        assert article._validation_info.is_recent(hours=24)
        assert article._validation_info.is_recent(hours=1)

    def test_validation_info_vo_was_validated_by(self):
        """Debería verificar quién validó."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.validate_article(validation_score=0.88, validated_by="admin")

        # Act & Assert
        assert article._validation_info.was_validated_by("admin")
        assert article._validation_info.was_validated_by("ADMIN")  # Case insensitive
        assert not article._validation_info.was_validated_by("user")

    def test_validate_article_with_invalid_score_raises_error(self):
        """Debería rechazar scores fuera de rango."""
        # Arrange
        from src.rss.article.domain.exceptions import InvalidScoreException

        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert
        # ValidationInfo ahora lanza ValueError en lugar de InvalidScoreException
        with pytest.raises(ValueError) as exc_info:
            article.validate_article(validation_score=1.5, validated_by="admin")

        assert "entre 0.0 y 1.0" in str(exc_info.value) or "between 0.0 and 1.0" in str(
            exc_info.value
        )

    def test_validate_article_with_empty_validator_raises_error(self):
        """Debería rechazar validador vacío."""
        # Arrange
        from src.rss.article.domain.exceptions import EmptyStringException

        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert
        # ValidationInfo ahora lanza ValueError en lugar de EmptyStringException
        with pytest.raises(ValueError) as exc_info:
            article.validate_article(validation_score=0.75, validated_by="")

        assert "no puede estar vacío" in str(
            exc_info.value
        ) or "cannot be empty" in str(exc_info.value)

    def test_validate_article_emits_event(self):
        """Debería emitir evento de validación."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.validate_article(validation_score=0.82, validated_by="admin")

        # Assert
        events = article.get_uncommitted_events()
        # Debería tener ArticleCreated + ArticleValidated
        assert len(events) == 2
        assert events[1].event_type == "ArticleValidated"

    def test_validation_info_consolidates_three_fields(self):
        """Debería consolidar score, validated_by y validated_at en un solo VO."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.validate_article(validation_score=0.77, validated_by="system")

        # Assert - Todos los valores vienen del mismo VO
        assert article._validation_info.score == 0.77
        assert article._validation_info.validated_by == "system"
        assert article._validation_info.validated_at is not None

        # Property validation_info accede al mismo VO
        assert article.validation_info.score == article._validation_info.score
        assert (
            article.validation_info.validated_by
            == article._validation_info.validated_by
        )
        assert (
            article.validation_info.validated_at
            == article._validation_info.validated_at
        )
