"""Tests para el método update_quality_assessment() de RssArticle aggregate.

Tests para Fase 2 del refactor: Consolidación de Setters Adicionales.
"""

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.exceptions import InvalidScoreException
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId
from src.shared.domain.value_objects import Level


class TestRssArticleUpdateQualityAssessment:
    """Tests para el método update_quality_assessment() del Article aggregate."""

    @pytest.fixture
    def article_factory(self):
        """Factory para crear artículos de prueba."""
        return RssArticleFactory()

    @pytest.fixture
    def sample_rss_article(self, article_factory):
        """Artículo de prueba."""
        return article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

    # Tests de actualización de campos individuales

    def test_update_quality_assessment_updates_quality_level_only(self, sample_article):
        """Debería actualizar solo el campo quality_level."""
        # Arrange
        initial_readability = sample_article.quality.readability_score
        initial_hash = sample_article.quality.content_hash

        # Act
        sample_article.update_quality_assessment(quality_level=Level.high())

        # Assert
        assert sample_article.quality.quality_level == Level.high()
        assert sample_article.quality.readability_score == initial_readability
        assert sample_article.quality.content_hash == initial_hash

    def test_update_quality_assessment_updates_readability_score_only(
        self, sample_article
    ):
        """Debería actualizar solo el campo readability_score."""
        # Arrange
        initial_quality_level = sample_article.quality.quality_level
        initial_hash = sample_article.quality.content_hash

        # Act
        sample_article.update_readability_score(0.85)

        # Assert
        assert sample_article.quality.readability_score.value == 0.85
        assert sample_article.quality.quality_level == initial_quality_level
        assert sample_article.quality.content_hash == initial_hash

    def test_update_quality_assessment_updates_content_hash_only(self, sample_article):
        """Debería actualizar solo el campo content_hash."""
        # Arrange
        initial_quality_level = sample_article.quality.quality_level
        initial_readability = sample_article.quality.readability_score

        # Act
        sample_article.update_quality_assessment(content_hash="abc123def456")

        # Assert
        assert sample_article.quality.content_hash == "abc123def456"
        assert sample_article.quality.quality_level == initial_quality_level
        assert sample_article.quality.readability_score == initial_readability

    # Tests de actualización batch de múltiples campos

    def test_update_quality_assessment_updates_all_fields(self, sample_article):
        """Debería actualizar múltiples campos en batch."""
        # Act
        sample_article.update_quality_assessment(
            quality_level=Level.high(), readability_score=0.75, content_hash="hash123"
        )

        # Assert
        assert sample_article.quality.quality_level == Level.high()
        assert sample_article.quality.readability_score.value == 0.75
        assert sample_article.quality.content_hash == "hash123"

    def test_update_quality_assessment_updates_quality_and_hash(self, sample_article):
        """Debería actualizar quality_level y content_hash juntos."""
        # Act
        sample_article.update_quality_assessment(
            quality_level=Level.very_high(), content_hash="premium_hash"
        )

        # Assert
        assert sample_article.quality.quality_level == Level.very_high()
        assert sample_article.quality.content_hash == "premium_hash"

    def test_update_quality_assessment_updates_readability_and_hash(
        self, sample_article
    ):
        """Debería actualizar readability_score y content_hash juntos."""
        # Act
        sample_article.update_quality_assessment(
            readability_score=0.90, content_hash="readable_hash"
        )

        # Assert
        assert sample_article.quality.readability_score.value == 0.90
        assert sample_article.quality.content_hash == "readable_hash"

    # Tests que solo campos proporcionados cambian

    def test_update_quality_assessment_preserves_unprovided_fields(
        self, sample_article
    ):
        """Debería preservar campos no proporcionados."""
        # Arrange - Establecer valores iniciales
        sample_article.update_quality_assessment(
            quality_level=Level.medium(),
            readability_score=0.60,
            content_hash="initial_hash",
        )

        # Act - Actualizar solo quality_level
        sample_article.update_quality_assessment(quality_level=Level.high())

        # Assert - Otros campos deben permanecer sin cambios
        assert sample_article.quality.quality_level == Level.high()
        assert sample_article.quality.readability_score.value == 0.60
        assert sample_article.quality.content_hash == "initial_hash"

    def test_update_quality_assessment_with_no_parameters_does_nothing(
        self, sample_article
    ):
        """Debería no hacer nada si no se proporcionan parámetros."""
        # Arrange
        initial_quality_level = sample_article.quality.quality_level
        initial_readability = sample_article.quality.readability_score
        initial_hash = sample_article.quality.content_hash

        # Act
        sample_article.update_quality_assessment()

        # Assert
        assert sample_article.quality.quality_level == initial_quality_level
        assert sample_article.quality.readability_score == initial_readability
        assert sample_article.quality.content_hash == initial_hash

    # Tests de validación de content_hash vacío

    def test_update_quality_assessment_rejects_empty_content_hash(self, sample_article):
        """Debería rechazar content_hash vacío."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_article.update_quality_assessment(content_hash="")

        assert "content_hash no puede estar vacío" in str(exc_info.value)

    def test_update_quality_assessment_rejects_whitespace_content_hash(
        self, sample_article
    ):
        """Debería rechazar content_hash con solo espacios."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_article.update_quality_assessment(content_hash="   ")

        assert "content_hash no puede estar vacío" in str(exc_info.value)

    def test_update_quality_assessment_rejects_non_string_content_hash(
        self, sample_article
    ):
        """Debería rechazar content_hash que no es string."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_article.update_quality_assessment(content_hash=123)  # type: ignore

        assert "content_hash debe ser string" in str(exc_info.value)

    def test_update_quality_assessment_strips_content_hash_whitespace(
        self, sample_article
    ):
        """Debería remover espacios del content_hash."""
        # Act
        sample_article.update_quality_assessment(content_hash="  hash123  ")

        # Assert
        assert sample_article.quality.content_hash == "hash123"

    # Tests de validación de readability_score

    def test_update_quality_assessment_rejects_readability_score_below_zero(
        self, sample_article
    ):
        """Debería rechazar readability_score menor a 0.0."""
        # Act & Assert
        with pytest.raises(InvalidScoreException):
            sample_article.update_readability_score(-0.1)

    def test_update_quality_assessment_rejects_readability_score_above_one(
        self, sample_article
    ):
        """Debería rechazar readability_score mayor a 1.0."""
        # Act & Assert
        with pytest.raises(InvalidScoreException):
            sample_article.update_readability_score(1.1)

    def test_update_quality_assessment_accepts_readability_score_zero(
        self, sample_article
    ):
        """Debería aceptar readability_score de 0.0."""
        # Act
        sample_article.update_readability_score(0.0)

        # Assert
        assert sample_article.quality.readability_score.value == 0.0

    def test_update_quality_assessment_accepts_readability_score_one(
        self, sample_article
    ):
        """Debería aceptar readability_score de 1.0."""
        # Act
        sample_article.update_readability_score(1.0)

        # Assert
        assert sample_article.quality.readability_score.value == 1.0

    # Tests de manejo de valores None

    def test_update_quality_assessment_sets_quality_level_to_none(self, sample_article):
        """Debería establecer quality_level a None cuando se pasa None."""
        # Arrange
        sample_article.update_quality_assessment(quality_level=Level.high())
        assert sample_article.quality.quality_level is not None

        # Act
        sample_article.update_quality_assessment(quality_level=None)

        # Assert
        assert sample_article.quality.quality_level is None

    def test_update_quality_assessment_sets_readability_score_to_none(
        self, sample_article
    ):
        """Debería establecer readability_score a None cuando se pasa None."""
        # Arrange
        sample_article.update_readability_score(0.75)
        assert sample_article.quality.readability_score is not None

        # Act
        sample_article.update_readability_score(None)

        # Assert
        assert sample_article.quality.readability_score is None

    def test_update_quality_assessment_sets_content_hash_to_none(self, sample_article):
        """Debería establecer content_hash a None cuando se pasa None."""
        # Arrange
        sample_article.update_quality_assessment(content_hash="hash123")
        assert sample_article.quality.content_hash is not None

        # Act
        sample_article.update_quality_assessment(content_hash=None)

        # Assert
        assert sample_article.quality.content_hash is None

    # Tests de actualización de timestamp

    def test_update_quality_assessment_updates_timestamp(self, sample_article):
        """Debería actualizar el timestamp updated_at."""
        # Arrange
        initial_updated_at = sample_article.updated_at

        # Act
        sample_article.update_quality_assessment(quality_level=Level.high())

        # Assert
        assert sample_article.updated_at > initial_updated_at


class TestRssArticleQualitySettersAsWrappers:
    """Tests para verificar que los setters son wrappers de update_quality_assessment()."""

    @pytest.fixture
    def article_factory(self):
        """Factory para crear artículos de prueba."""
        return RssArticleFactory()

    @pytest.fixture
    def sample_rss_article(self, article_factory):
        """Artículo de prueba."""
        return article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

    def test_set_content_hash_is_equivalent_to_update_quality_assessment(
        self, sample_article
    ):
        """set_content_hash() debería ser equivalente a update_quality_assessment(content_hash=...)."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_quality_assessment(content_hash="test_hash_123")
        article2.update_quality_assessment(content_hash="test_hash_123")

        # Assert
        assert article1.quality.content_hash == article2.quality.content_hash

    def test_set_quality_level_is_equivalent_to_update_quality_assessment(
        self, sample_article
    ):
        """set_quality_level() debería ser equivalente a update_quality_assessment(quality_level=...)."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_quality_assessment(quality_level=Level.high())
        article2.update_quality_assessment(quality_level=Level.high())

        # Assert
        assert article1.quality.quality_level == article2.quality.quality_level

    def test_set_content_hash_preserves_other_fields(self, sample_article):
        """set_content_hash() debería preservar otros campos de quality."""
        # Arrange
        sample_article.update_quality_assessment(
            quality_level=Level.high(), readability_score=0.85
        )
        initial_quality_level = sample_article.quality.quality_level
        initial_readability = sample_article.quality.readability_score

        # Act
        sample_article.update_quality_assessment(content_hash="new_hash")

        # Assert
        assert sample_article.quality.content_hash == "new_hash"
        assert sample_article.quality.quality_level == initial_quality_level
        assert sample_article.quality.readability_score == initial_readability

    def test_set_quality_level_preserves_other_fields(self, sample_article):
        """set_quality_level() debería preservar otros campos de quality."""
        # Arrange
        sample_article.update_quality_assessment(
            readability_score=0.75, content_hash="existing_hash"
        )
        initial_readability = sample_article.quality.readability_score
        initial_hash = sample_article.quality.content_hash

        # Act
        sample_article.update_quality_assessment(quality_level=Level.very_high())

        # Assert
        assert sample_article.quality.quality_level == Level.very_high()
        assert sample_article.quality.readability_score == initial_readability
        assert sample_article.quality.content_hash == initial_hash

    def test_set_readability_score_uses_update_quality_assessment(self, sample_article):
        """set_readability_score() debería usar update_quality_assessment() internamente."""
        # Arrange
        sample_article.update_quality_assessment(
            quality_level=Level.medium(), content_hash="hash123"
        )
        initial_quality_level = sample_article.quality.quality_level
        initial_hash = sample_article.quality.content_hash

        # Act
        sample_article.update_readability_score(0.88)

        # Assert
        assert sample_article.quality.readability_score.value == 0.88
        assert sample_article.quality.quality_level == initial_quality_level
        assert sample_article.quality.content_hash == initial_hash
