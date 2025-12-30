"""Tests para el método update_metadata() de RssArticle aggregate.

Tests para Fase 1 del refactor: Consolidación de Metadata.
"""

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.exceptions import (
    EmptyStringException,
    InvalidScoreException,
)
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleUpdateMetadata:
    """Tests para el método update_metadata() del Article aggregate."""

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

    def test_update_metadata_updates_author_only(self, sample_article):
        """Debería actualizar solo el campo author."""
        # Arrange
        initial_language = sample_article.metadata.language
        initial_category = sample_article.metadata.category

        # Act
        sample_article.update_metadata_fields(author="John Doe")

        # Assert
        assert sample_article.metadata.author is not None
        assert sample_article.metadata.author.value == "John Doe"
        assert sample_article.metadata.language == initial_language
        assert sample_article.metadata.category == initial_category

    def test_update_metadata_updates_language_only(self, sample_article):
        """Debería actualizar solo el campo language."""
        # Arrange
        initial_author = sample_article.metadata.author
        initial_category = sample_article.metadata.category

        # Act
        sample_article.update_language("en", 0.95)

        # Assert
        assert sample_article.metadata.language is not None
        assert sample_article.metadata.language.code == "en"
        assert sample_article.metadata.language.confidence == 0.95
        assert sample_article.metadata.author == initial_author
        assert sample_article.metadata.category == initial_category

    def test_update_metadata_updates_category_only(self, sample_article):
        """Debería actualizar solo el campo category."""
        # Arrange
        initial_author = sample_article.metadata.author
        initial_language = sample_article.metadata.language

        # Act
        sample_article.update_category("Technology", 0.90)

        # Assert
        assert sample_article.metadata.category is not None
        assert sample_article.metadata.category.value == "Technology"
        assert sample_article.metadata.author == initial_author
        assert sample_article.metadata.language == initial_language

    # Tests de actualización batch de múltiples campos

    def test_update_metadata_updates_all_fields(self, sample_article):
        """Debería actualizar múltiples campos en batch."""
        # Act
        sample_article.update_metadata_fields(
            author="Jane Smith",
            language="es",
            category="Science",
            language_confidence=0.98,
            category_confidence=0.92,
        )

        # Assert
        assert sample_article.metadata.author is not None
        assert sample_article.metadata.author.value == "Jane Smith"
        assert sample_article.metadata.language is not None
        assert sample_article.metadata.language.code == "es"
        assert sample_article.metadata.language.confidence == 0.98
        assert sample_article.metadata.category is not None
        assert sample_article.metadata.category.value == "Science"

    def test_update_metadata_updates_author_and_language(self, sample_article):
        """Debería actualizar author y language juntos."""
        # Act
        sample_article.update_metadata_fields(
            author="Bob Johnson", language="fr", language_confidence=0.85
        )

        # Assert
        assert sample_article.metadata.author is not None
        assert sample_article.metadata.author.value == "Bob Johnson"
        assert sample_article.metadata.language is not None
        assert sample_article.metadata.language.code == "fr"
        assert sample_article.metadata.language.confidence == 0.85

    def test_update_metadata_updates_language_and_category(self, sample_article):
        """Debería actualizar language y category juntos."""
        # Act
        sample_article.update_metadata_fields(
            language="de",
            category="Politics",
            language_confidence=0.88,
            category_confidence=0.75,
        )

        # Assert
        assert sample_article.metadata.language is not None
        assert sample_article.metadata.language.code == "de"
        assert sample_article.metadata.category is not None
        assert sample_article.metadata.category.value == "Politics"

    # Tests que solo campos proporcionados cambian

    def test_update_metadata_preserves_unprovided_fields(self, sample_article):
        """Debería preservar campos no proporcionados."""
        # Arrange - Establecer valores iniciales
        sample_article.update_metadata_fields(
            author="Initial Author", language="en", category="Tech"
        )

        # Act - Actualizar solo author
        sample_article.update_metadata_fields(author="Updated Author")

        # Assert - language y category deben permanecer sin cambios
        assert sample_article.metadata.author.value == "Updated Author"
        assert sample_article.metadata.language.code == "en"
        assert sample_article.metadata.category.value == "Tech"

    def test_update_metadata_with_no_parameters_does_nothing(self, sample_article):
        """Debería no hacer nada si no se proporcionan parámetros."""
        # Arrange
        initial_author = sample_article.metadata.author
        initial_language = sample_article.metadata.language
        initial_category = sample_article.metadata.category

        # Act
        sample_article.update_metadata_fields()

        # Assert
        assert sample_article.metadata.author == initial_author
        assert sample_article.metadata.language == initial_language
        assert sample_article.metadata.category == initial_category

    # Tests de validación de parámetros inválidos

    def test_update_metadata_with_empty_language_raises_exception(self, sample_article):
        """Debería lanzar EmptyStringException con language vacío."""
        # Act & Assert
        with pytest.raises(EmptyStringException) as exc_info:
            sample_article.update_language("")

        assert exc_info.value.param_name == "language"

    def test_update_metadata_with_whitespace_language_raises_exception(
        self, sample_article
    ):
        """Debería lanzar EmptyStringException con language de solo espacios."""
        # Act & Assert
        with pytest.raises(EmptyStringException):
            sample_article.update_language("   ")

    def test_update_metadata_with_empty_category_sets_none(self, sample_article):
        """Debería establecer category a None con categoría vacía."""
        # Arrange - Establecer categoría inicial
        sample_article.update_metadata_fields(category="Tech")
        assert sample_article.metadata.category is not None

        # Act - Limpiar categoría
        sample_article.update_metadata_fields(category="")

        # Assert
        assert sample_article.metadata.category is None

    def test_update_metadata_with_invalid_language_confidence_raises_exception(
        self, sample_article
    ):
        """Debería lanzar InvalidScoreException con language_confidence inválido."""
        # Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            sample_article.update_language("en", 1.5)

        assert "language_confidence" in str(exc_info.value)
        assert exc_info.value.score == 1.5

    def test_update_metadata_with_negative_language_confidence_raises_exception(
        self, sample_article
    ):
        """Debería lanzar InvalidScoreException con language_confidence negativo."""
        # Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            sample_article.update_language("en", -0.1)

        assert exc_info.value.score == -0.1

    def test_update_metadata_with_invalid_category_confidence_raises_exception(
        self, sample_article
    ):
        """Debería lanzar InvalidScoreException con category_confidence inválido."""
        # Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            sample_article.update_category("Tech", 2.0)

        assert "category_confidence" in str(exc_info.value)
        assert exc_info.value.score == 2.0

    # Tests de emisión de eventos correctos

    def test_update_metadata_emits_language_detected_event(self, sample_article):
        """Debería emitir ArticleLanguageDetected event cuando se actualiza language."""
        # Arrange
        initial_event_count = len(sample_article.get_uncommitted_events())

        # Act
        sample_article.update_language("en", 0.95)

        # Assert
        events = sample_article.get_uncommitted_events()
        assert len(events) > initial_event_count
        assert any(e.event_type == "ArticleLanguageDetected" for e in events)

        # Verificar datos del evento
        language_event = next(
            e for e in events if e.event_type == "ArticleLanguageDetected"
        )
        assert language_event.language_code == "en"
        assert language_event.confidence == 0.95

    def test_update_metadata_emits_categorized_event(self, sample_article):
        """Debería emitir ArticleCategorized event cuando se actualiza category."""
        # Arrange
        initial_event_count = len(sample_article.get_uncommitted_events())

        # Act
        sample_article.update_category("Technology", 0.90)

        # Assert
        events = sample_article.get_uncommitted_events()
        assert len(events) > initial_event_count
        assert any(e.event_type == "ArticleCategorized" for e in events)

        # Verificar datos del evento
        category_event = next(e for e in events if e.event_type == "ArticleCategorized")
        assert category_event.category == "Technology"
        assert category_event.confidence == 0.90

    def test_update_metadata_emits_both_events_when_updating_both(self, sample_article):
        """Debería emitir ambos eventos cuando se actualizan language y category."""
        # Arrange
        initial_event_count = len(sample_article.get_uncommitted_events())

        # Act
        sample_article.update_metadata_fields(
            language="es",
            category="Science",
            language_confidence=0.98,
            category_confidence=0.85,
        )

        # Assert
        events = sample_article.get_uncommitted_events()
        assert len(events) > initial_event_count

        event_types = [e.event_type for e in events]
        assert "ArticleLanguageDetected" in event_types
        assert "ArticleCategorized" in event_types

    def test_update_metadata_does_not_emit_event_when_only_author_updated(
        self, sample_article
    ):
        """No debería emitir eventos cuando solo se actualiza author."""
        # Arrange
        initial_event_count = len(sample_article.get_uncommitted_events())

        # Act
        sample_article.update_metadata_fields(author="John Doe")

        # Assert
        final_event_count = len(sample_article.get_uncommitted_events())
        assert final_event_count == initial_event_count

    def test_update_metadata_does_not_emit_event_for_empty_category(
        self, sample_article
    ):
        """No debería emitir evento cuando category está vacía."""
        # Arrange
        initial_event_count = len(sample_article.get_uncommitted_events())

        # Act
        sample_article.update_metadata_fields(category="")

        # Assert
        final_event_count = len(sample_article.get_uncommitted_events())
        assert final_event_count == initial_event_count

    # Tests de actualización de timestamp

    def test_update_metadata_updates_timestamp(self, sample_article):
        """Debería actualizar el timestamp updated_at."""
        # Arrange
        initial_updated_at = sample_article.updated_at

        # Act
        sample_article.update_metadata_fields(author="New Author")

        # Assert
        assert sample_article.updated_at > initial_updated_at

    # Tests de normalización de datos

    def test_update_metadata_normalizes_language_to_lowercase(self, sample_article):
        """Debería normalizar código de idioma a minúsculas."""
        # Act
        sample_article.update_language("EN")

        # Assert
        assert sample_article.metadata.language.code == "en"

    def test_update_metadata_strips_whitespace_from_language(self, sample_article):
        """Debería remover espacios del código de idioma."""
        # Act
        sample_article.update_language("  es  ")

        # Assert
        assert sample_article.metadata.language.code == "es"

    # Tests de confidence por defecto

    def test_update_metadata_uses_default_language_confidence(self, sample_article):
        """Debería usar confidence por defecto (1.0) para language."""
        # Act
        sample_article.update_language("en")

        # Assert
        assert sample_article.metadata.language.confidence == 1.0

    def test_update_metadata_uses_default_category_confidence(self, sample_article):
        """Debería usar confidence por defecto (1.0) para category."""
        # Act
        sample_article.update_metadata_fields(category="Tech")

        # Assert - Verificar que el evento tiene confidence 1.0
        events = sample_article.get_uncommitted_events()
        category_event = next(e for e in events if e.event_type == "ArticleCategorized")
        assert category_event.confidence == 1.0


class TestRssArticleSettersAsWrappers:
    """Tests para verificar que los setters son wrappers de update_metadata()."""

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

    def test_set_author_is_equivalent_to_update_metadata(self, sample_article):
        """set_author() debería ser equivalente a update_metadata(author=...)."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_metadata_fields(author="John Doe")
        article2.update_metadata_fields(author="John Doe")

        # Assert
        assert article1.metadata.author.value == article2.metadata.author.value

    def test_set_language_is_equivalent_to_update_metadata(self, sample_article):
        """set_language() debería ser equivalente a update_metadata(language=...)."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_language("en", 0.95)
        article2.update_language("en", 0.95)

        # Assert
        assert article1.metadata.language.code == article2.metadata.language.code
        assert (
            article1.metadata.language.confidence
            == article2.metadata.language.confidence
        )

    def test_set_category_is_equivalent_to_update_metadata(self, sample_article):
        """set_category() debería ser equivalente a update_metadata(category=...)."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_category("Technology", 0.90)
        article2.update_category("Technology", 0.90)

        # Assert
        assert article1.metadata.category.value == article2.metadata.category.value

    def test_set_language_emits_same_event_as_update_metadata(self, sample_article):
        """set_language() debería emitir el mismo evento que update_metadata()."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_language("en", 0.95)
        article2.update_language("en", 0.95)

        # Assert
        events1 = article1.get_uncommitted_events()
        events2 = article2.get_uncommitted_events()

        language_event1 = next(
            e for e in events1 if e.event_type == "ArticleLanguageDetected"
        )
        language_event2 = next(
            e for e in events2 if e.event_type == "ArticleLanguageDetected"
        )

        assert language_event1.language_code == language_event2.language_code
        assert language_event1.confidence == language_event2.confidence

    def test_set_category_emits_same_event_as_update_metadata(self, sample_article):
        """set_category() debería emitir el mismo evento que update_metadata()."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_category("Tech", 0.90)
        article2.update_category("Tech", 0.90)

        # Assert
        events1 = article1.get_uncommitted_events()
        events2 = article2.get_uncommitted_events()

        category_event1 = next(
            e for e in events1 if e.event_type == "ArticleCategorized"
        )
        category_event2 = next(
            e for e in events2 if e.event_type == "ArticleCategorized"
        )

        assert category_event1.category == category_event2.category
        assert category_event1.confidence == category_event2.confidence
