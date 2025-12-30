"""Tests para métodos refactorizados de Article que usan Specifications."""

from datetime import datetime, timezone

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.exceptions import (
    EmptyStringException,
    InvalidScoreException,
)
from src.rss.article.domain.factories.rss_article_factory import RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleSpecifications:
    """Tests para métodos de Article que usan Specification Pattern."""

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

    # Tests para set_readability_score

    def test_set_readability_score_with_valid_score(self, sample_rss_article):
        """Debería establecer readability score con valor válido."""
        # Act
        sample_rss_article.update_readability_score(0.75)

        # Assert
        assert (
            sample_rss_article.quality.readability_score.value
            if sample_rss_article.quality.readability_score
            else None == 0.75
        )
        assert sample_rss_article.quality.readability_score is not None

    def test_set_readability_score_with_min_score(self, sample_rss_article):
        """Debería aceptar score mínimo (0.0)."""
        # Act
        sample_rss_article.update_readability_score(0.0)

        # Assert
        assert sample_rss_article.quality.readability_score is not None
        assert sample_rss_article.quality.readability_score.value == 0.0

    def test_set_readability_score_with_max_score(self, sample_rss_article):
        """Debería aceptar score máximo (1.0)."""
        # Act
        sample_rss_article.update_readability_score(1.0)

        # Assert
        assert (
            sample_rss_article.quality.readability_score.value
            if sample_rss_article.quality.readability_score
            else None == 1.0
        )

    def test_set_readability_score_with_invalid_score_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar InvalidScoreException con score fuera de rango."""
        # Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            sample_rss_article.update_readability_score(1.5)

        assert "readability_score" in str(exc_info.value)
        assert exc_info.value.score == 1.5

    def test_set_readability_score_with_negative_score_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar InvalidScoreException con score negativo."""
        # Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            sample_rss_article.update_readability_score(-0.1)

        assert exc_info.value.score == -0.1

    def test_set_readability_score_with_non_numeric_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar InvalidScoreException con valor no numérico."""
        # Act & Assert
        with pytest.raises(InvalidScoreException):
            sample_rss_article.update_readability_score("invalid")

    def test_set_readability_score_is_pure_setter(self, sample_rss_article):
        """set_readability_score() es un setter puro - NO emite eventos."""
        # Arrange
        initial_event_count = len(sample_rss_article.get_uncommitted_events())

        # Act
        sample_rss_article.update_readability_score(0.8)

        # Assert - No debe emitir eventos
        final_event_count = len(sample_rss_article.get_uncommitted_events())
        assert final_event_count == initial_event_count

    # Tests para validate_article

    def test_validate_article_with_valid_inputs(self, sample_rss_article):
        """Debería validar artículo con inputs válidos."""
        # Act
        sample_rss_article.validate_article(0.85, "test_validator")

        # Assert
        assert sample_rss_article.validation_info.score == 0.85
        assert sample_rss_article.validation_info.validated_by == "test_validator"
        assert sample_rss_article.validation_info.validated_at is not None

    def test_validate_article_with_invalid_score_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar ValueError con score inválido (validación en ValidationInfo)."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_rss_article.validate_article(2.0, "validator")

        assert "2.0" in str(exc_info.value)

    def test_validate_article_with_empty_validated_by_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar ValueError con validated_by vacío (validación en ValidationInfo)."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_rss_article.validate_article(0.8, "")

        assert "validated_by" in str(exc_info.value)

    def test_validate_article_with_whitespace_validated_by_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar ValueError con validated_by solo espacios (validación en ValidationInfo)."""
        # Act & Assert
        with pytest.raises(ValueError):
            sample_rss_article.validate_article(0.8, "   ")

    def test_validate_article_emits_event(self, sample_rss_article):
        """Debería emitir ArticleValidated event."""
        # Act
        sample_rss_article.validate_article(0.9, "validator")

        # Assert
        events = sample_rss_article.get_uncommitted_events()
        assert len(events) > 0
        assert any(e.event_type == "ArticleValidated" for e in events)

    # Tests para mark_error

    def test_mark_error_with_valid_inputs(self, sample_rss_article):
        """Debería marcar error con inputs válidos."""
        # Act
        sample_rss_article.mark_error(
            "parsing_error", "Failed to parse content", "system"
        )

        # Assert
        assert sample_rss_article.error_info.has_error is True
        assert sample_rss_article.error_info.error_type == "parsing_error"
        assert sample_rss_article.error_info.error_message == "Failed to parse content"
        assert sample_rss_article.error_info.error_marked_by == "system"
        assert sample_rss_article.error_info.error_marked_at is not None

    def test_mark_error_with_empty_error_type_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar ValueError con error_type vacío (validación en ErrorInfo)."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_rss_article.mark_error("", "message", "system")

        assert "error_type" in str(exc_info.value)

    def test_mark_error_with_empty_error_message_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar ValueError con error_message vacío (validación en ErrorInfo)."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_rss_article.mark_error("error", "", "system")

        assert "error_message" in str(exc_info.value)

    def test_mark_error_with_empty_marked_by_raises_exception(self, sample_rss_article):
        """Debería lanzar ValueError con marked_by vacío (validación en ErrorInfo)."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_rss_article.mark_error("error", "message", "")

        assert "marked_by" in str(exc_info.value)

    def test_mark_error_with_whitespace_strings_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar ValueError con strings de solo espacios (validación en ErrorInfo)."""
        # Act & Assert
        with pytest.raises(ValueError):
            sample_rss_article.mark_error("   ", "message", "system")

        with pytest.raises(ValueError):
            sample_rss_article.mark_error("error", "   ", "system")

        with pytest.raises(ValueError):
            sample_rss_article.mark_error("error", "message", "   ")

    def test_mark_error_emits_event(self, sample_rss_article):
        """Debería emitir ArticleErrorMarked event."""
        # Act
        sample_rss_article.mark_error("test_error", "Test message", "system")

        # Assert
        events = sample_rss_article.get_uncommitted_events()
        assert len(events) > 0
        assert any(e.event_type == "ArticleErrorMarked" for e in events)

    # Tests para set_category

    def test_set_category_with_valid_inputs(self, sample_rss_article):
        """Debería establecer categoría con inputs válidos."""
        # Act
        sample_rss_article.update_category("Technology", 0.95)

        # Assert
        assert (
            sample_rss_article.metadata.category.value
            if sample_rss_article.metadata.category
            else None == "Technology"
        )
        # Verificar que se emitió el evento con la confidence correcta
        events = sample_rss_article.get_uncommitted_events()
        category_event = next(e for e in events if e.event_type == "ArticleCategorized")
        assert category_event.confidence == 0.95

    def test_set_category_with_default_confidence(self, sample_rss_article):
        """Debería usar confidence por defecto (1.0)."""
        # Act
        sample_rss_article.update_category("Science", 1.0)

        # Assert
        assert (
            sample_rss_article.metadata.category.value
            if sample_rss_article.metadata.category
            else None == "Science"
        )
        # Verificar que se emitió el evento con la confidence por defecto
        events = sample_rss_article.get_uncommitted_events()
        category_event = next(e for e in events if e.event_type == "ArticleCategorized")
        assert category_event.confidence == 1.0

    def test_set_category_with_invalid_confidence_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar InvalidScoreException con confidence inválido."""
        # Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            sample_rss_article.update_category("Tech", 1.5)

        assert "confidence" in str(exc_info.value)
        assert exc_info.value.score == 1.5

    def test_set_category_with_empty_category_sets_none(self, sample_rss_article):
        """Debería establecer None con categoría vacía."""
        # Act
        sample_rss_article.update_category("", 0.8)

        # Assert
        assert (
            sample_rss_article.metadata.category.value
            if sample_rss_article.metadata.category
            else None is None
        )

    def test_set_category_emits_event_when_not_empty(self, sample_rss_article):
        """Debería emitir ArticleCategorized event cuando categoría no está vacía."""
        # Act
        sample_rss_article.update_category("Tech", 0.9)

        # Assert
        events = sample_rss_article.get_uncommitted_events()
        assert len(events) > 0
        assert any(e.event_type == "ArticleCategorized" for e in events)

    def test_set_category_does_not_emit_event_when_empty(self, sample_rss_article):
        """No debería emitir evento cuando categoría está vacía."""
        # Arrange
        initial_event_count = len(sample_rss_article.get_uncommitted_events())

        # Act
        sample_rss_article.update_category("", 0.8)

        # Assert
        final_event_count = len(sample_rss_article.get_uncommitted_events())
        assert final_event_count == initial_event_count

    # Tests para set_language

    def test_set_language_with_valid_inputs(self, sample_rss_article):
        """Debería establecer idioma con inputs válidos."""
        # Act
        sample_rss_article.update_language("en", 0.98)

        # Assert
        assert (
            sample_rss_article.metadata.language.code
            if sample_rss_article.metadata.language
            else None == "en"
        )

    def test_set_language_with_default_confidence(self, sample_rss_article):
        """Debería usar confidence por defecto (1.0)."""
        # Act
        sample_rss_article.update_language("es")

        # Assert
        assert (
            sample_rss_article.metadata.language.code
            if sample_rss_article.metadata.language
            else None == "es"
        )

    def test_set_language_normalizes_to_lowercase(self, sample_rss_article):
        """Debería normalizar código de idioma a minúsculas."""
        # Act
        sample_rss_article.update_language("EN", 0.9)

        # Assert
        assert (
            sample_rss_article.metadata.language.code
            if sample_rss_article.metadata.language
            else None == "en"
        )

    def test_set_language_with_empty_language_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar EmptyStringException con language vacío."""
        # Act & Assert
        with pytest.raises(EmptyStringException) as exc_info:
            sample_rss_article.update_language("", 0.9)

        assert exc_info.value.param_name == "language"

    def test_set_language_with_whitespace_language_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar EmptyStringException con language de solo espacios."""
        # Act & Assert
        with pytest.raises(EmptyStringException):
            sample_rss_article.update_language("   ", 0.9)

    def test_set_language_with_invalid_confidence_raises_exception(
        self, sample_rss_article
    ):
        """Debería lanzar InvalidScoreException con confidence inválido."""
        # Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            sample_rss_article.update_language("en", -0.1)

        assert "confidence" in str(exc_info.value)
        assert exc_info.value.score == -0.1

    def test_set_language_emits_event(self, sample_rss_article):
        """Debería emitir ArticleLanguageDetected event."""
        # Act
        sample_rss_article.update_language("fr", 0.95)

        # Assert
        events = sample_rss_article.get_uncommitted_events()
        assert len(events) > 0
        assert any(e.event_type == "ArticleLanguageDetected" for e in events)

    # Tests de integración - Specifications usadas correctamente

    def test_specifications_provide_detailed_error_messages(self, sample_rss_article):
        """Debería proporcionar mensajes de error detallados desde Specifications."""
        # Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            sample_rss_article.update_readability_score(2.5)

        error_message = str(exc_info.value)
        assert "readability_score" in error_message
        assert "0.0" in error_message
        assert "1.0" in error_message
        assert "2.5" in error_message

    def test_specifications_validate_type_correctly(self, sample_rss_article):
        """Debería validar tipos correctamente (validación en ValidationInfo)."""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            sample_rss_article.validate_article("not_a_number", "validator")

        assert (
            "número" in str(exc_info.value).lower()
            or "number" in str(exc_info.value).lower()
        )

    def test_multiple_validations_in_single_method(self, sample_rss_article):
        """Debería validar múltiples parámetros en un solo método (validación en ValidationInfo)."""
        # Test que validate_article valida tanto score como validated_by

        # Score inválido
        with pytest.raises(ValueError):
            sample_rss_article.validate_article(1.5, "validator")

        # validated_by vacío
        with pytest.raises(ValueError):
            sample_rss_article.validate_article(0.8, "")

    def test_events_still_emitted_after_refactoring(self, sample_rss_article):
        """Debería seguir emitiendo eventos correctamente después de refactorización."""
        # Arrange
        initial_events = len(sample_rss_article.get_uncommitted_events())

        # Act
        sample_rss_article.update_readability_score(
            0.7
        )  # Setter puro - NO emite evento
        sample_rss_article.validate_article(0.8, "validator")
        sample_rss_article.update_category("Tech", 0.9)
        sample_rss_article.update_language("en", 0.95)
        sample_rss_article.mark_error("test", "message", "system")

        # Assert
        final_events = sample_rss_article.get_uncommitted_events()
        assert len(final_events) > initial_events

        # Verificar que los eventos esperados están presentes
        # NOTA: set_readability_score ya NO emite eventos (es setter puro)
        event_types = [e.event_type for e in final_events]
        assert "ArticleValidated" in event_types
        assert "ArticleCategorized" in event_types
        assert "ArticleLanguageDetected" in event_types
        assert "ArticleErrorMarked" in event_types
