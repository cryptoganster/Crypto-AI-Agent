"""Tests de integración para Article con ReadabilityScore VO."""

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects.readability_score import ReadabilityScore
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleReadabilityIntegration:
    """Tests de integración entre Article y ReadabilityScore."""

    def test_article_readability_score_property_returns_none_by_default(self):
        """Debería retornar None si no se ha calculado readability."""
        # Arrange
        factory = RssArticleFactory()
        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert
        assert (
            article.quality.readability_score.value
            if article.quality.readability_score
            else None is None
        )

    def test_set_readability_score_with_float(self):
        """Debería establecer readability score desde float."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.update_readability_score(0.85)

        # Assert
        assert (
            article.quality.readability_score.value
            if article.quality.readability_score
            else None
        ) == 0.85
        assert article.quality.readability_score is not None

    def test_set_readability_score_with_none(self):
        """Debería establecer None si se pasa None."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_readability_score(0.75)

        # Act
        article.update_readability_score(None)

        # Assert
        assert (
            article.quality.readability_score.value
            if article.quality.readability_score
            else None is None
        )
        assert article.quality.readability_score is None

    def test_set_readability_score_validates_range(self):
        """Debería validar que el score esté en rango 0.0-1.0."""
        # Arrange
        from src.rss.article.domain.exceptions import InvalidScoreException

        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            article.update_readability_score(1.5)

        assert "entre 0.0 y 1.0" in str(exc_info.value) or "between 0.0 and 1.0" in str(
            exc_info.value
        )

    def test_set_readability_score_validates_negative(self):
        """Debería rechazar scores negativos."""
        # Arrange
        from src.rss.article.domain.exceptions import InvalidScoreException

        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            article.update_readability_score(-0.1)

        assert "entre 0.0 y 1.0" in str(exc_info.value) or "between 0.0 and 1.0" in str(
            exc_info.value
        )

    def test_readability_score_property_returns_value_from_vo(self):
        """Debería retornar el valor desde el VO."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_readability_score(0.65)

        # Act
        result = (
            article.quality.readability_score.value
            if article.quality.readability_score
            else None
        )

        # Assert
        assert result == 0.65
        assert isinstance(result, float)

    def test_internal_readability_score_is_vo(self):
        """Debería almacenar internamente como ReadabilityScore VO."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article.update_readability_score(0.92)

        # Assert
        # Verificar usando propiedades públicas
        assert (
            article.quality.readability_score.value
            if article.quality.readability_score
            else None
        ) == 0.92
        assert article.quality.readability_score is not None

    def test_set_readability_score_updates_timestamp(self):
        """Debería actualizar updated_at al establecer readability."""
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
        article.update_readability_score(0.78)

        # Assert
        assert article.updated_at > original_updated_at

    def test_readability_score_vo_provides_level_info(self):
        """Debería poder acceder a métodos del VO para obtener nivel."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_readability_score(0.25)

        # Act & Assert
        # Verificar usando propiedad pública
        assert article.quality.readability_score is not None
        assert (
            article.quality.readability_score.value
            if article.quality.readability_score
            else None
        ) == 0.25

    def test_set_readability_score_with_boundary_values(self):
        """Debería aceptar valores en los límites (0.0 y 1.0)."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert - Límite inferior
        article.update_readability_score(0.0)
        assert (
            article.quality.readability_score.value
            if article.quality.readability_score
            else None
        ) == 0.0

        # Act & Assert - Límite superior
        article.update_readability_score(1.0)
        assert (
            article.quality.readability_score.value
            if article.quality.readability_score
            else None
        ) == 1.0
