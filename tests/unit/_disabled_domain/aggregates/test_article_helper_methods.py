"""Tests para métodos helper consolidados del RssArticle aggregate.

Tests para Optimización 3: Consolidación de Helpers
- _validate() método genérico
- _emit_metadata_event() método genérico
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.exceptions import (
    EmptyStringException,
    InvalidScoreException,
)
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleValidateHelper:
    """Tests para método genérico _validate()."""

    @pytest.fixture
    def rss_article(self):
        """Crea Article para tests."""
        factory = RssArticleFactory()
        return factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

    def test_validate_score_accepts_valid_scores(self, article):
        """_validate() con 'score' debería aceptar valores válidos [0.0, 1.0]."""
        # Arrange & Act & Assert - No debería lanzar excepción
        article._validate(0.0, "test_score", "score")
        article._validate(0.5, "test_score", "score")
        article._validate(1.0, "test_score", "score")

    def test_validate_score_rejects_negative_scores(self, article):
        """_validate() con 'score' debería rechazar valores negativos."""
        # Arrange & Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            article._validate(-0.1, "test_score", "score")

        assert "test_score" in str(exc_info.value)

    def test_validate_score_rejects_scores_above_one(self, article):
        """_validate() con 'score' debería rechazar valores > 1.0."""
        # Arrange & Act & Assert
        with pytest.raises(InvalidScoreException) as exc_info:
            article._validate(1.1, "test_score", "score")

        assert "test_score" in str(exc_info.value)

    def test_validate_string_accepts_non_empty_strings(self, article):
        """_validate() con 'string' debería aceptar strings no vacíos."""
        # Arrange & Act & Assert - No debería lanzar excepción
        article._validate("valid", "test_string", "string")
        article._validate("a", "test_string", "string")
        article._validate("  text  ", "test_string", "string")

    def test_validate_string_rejects_empty_string(self, article):
        """_validate() con 'string' debería rechazar string vacío."""
        # Arrange & Act & Assert
        with pytest.raises(EmptyStringException) as exc_info:
            article._validate("", "test_string", "string")

        assert "test_string" in str(exc_info.value)

    def test_validate_string_rejects_whitespace_only(self, article):
        """_validate() con 'string' debería rechazar strings solo con espacios."""
        # Arrange & Act & Assert
        with pytest.raises(EmptyStringException) as exc_info:
            article._validate("   ", "test_string", "string")

        assert "test_string" in str(exc_info.value)

    def test_validate_score_is_equivalent_to_old_validate_confidence(self, article):
        """_validate(value, name, 'score') debería ser equivalente a _validate_confidence()."""
        # Este test verifica que el comportamiento es idéntico al método antiguo

        # Test 1: Valores válidos no lanzan excepción
        article._validate(0.5, "confidence", "score")
        article._validate(0.0, "confidence", "score")
        article._validate(1.0, "confidence", "score")

        # Test 2: Valores inválidos lanzan InvalidScoreException
        with pytest.raises(InvalidScoreException):
            article._validate(-0.1, "confidence", "score")

        with pytest.raises(InvalidScoreException):
            article._validate(1.5, "confidence", "score")

    def test_validate_string_is_equivalent_to_old_validate_non_empty_string(
        self, article
    ):
        """_validate(value, name, 'string') debería ser equivalente a _validate_non_empty_string()."""
        # Este test verifica que el comportamiento es idéntico al método antiguo

        # Test 1: Strings válidos no lanzan excepción
        article._validate("valid", "param", "string")
        article._validate("a", "param", "string")

        # Test 2: Strings vacíos lanzan EmptyStringException
        with pytest.raises(EmptyStringException):
            article._validate("", "param", "string")

        with pytest.raises(EmptyStringException):
            article._validate("   ", "param", "string")


class TestRssArticleEmitMetadataEventHelper:
    """Tests para método genérico _emit_metadata_event()."""

    @pytest.fixture
    def rss_article(self):
        """Crea Article para tests."""
        factory = RssArticleFactory()
        return factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

    def test_emit_metadata_event_category_emits_article_categorized(self, article):
        """_emit_metadata_event('category', ...) debería emitir ArticleCategorized."""
        # Arrange
        initial_event_count = len(article.get_uncommitted_events())

        # Act
        article._emit_metadata_event("category", "Technology", 0.95)

        # Assert
        events = article.get_uncommitted_events()
        assert len(events) == initial_event_count + 1

        new_event = events[-1]
        assert new_event.__class__.__name__ == "ArticleCategorized"
        assert new_event.category == "Technology"
        assert new_event.confidence == 0.95
        assert new_event.article_id == str(article.id)
        assert new_event.source_id == str(article.identity_vo.source_id)

    def test_emit_metadata_event_language_emits_article_language_detected(
        self, article
    ):
        """_emit_metadata_event('language', ...) debería emitir ArticleLanguageDetected."""
        # Arrange
        initial_event_count = len(article.get_uncommitted_events())

        # Act
        article._emit_metadata_event("language", "en", 0.98)

        # Assert
        events = article.get_uncommitted_events()
        assert len(events) == initial_event_count + 1

        new_event = events[-1]
        assert new_event.__class__.__name__ == "ArticleLanguageDetected"
        assert new_event.language_code == "en"
        assert new_event.confidence == 0.98
        assert new_event.article_id == str(article.id)
        assert new_event.source_id == str(article.identity_vo.source_id)

    def test_emit_metadata_event_category_strips_whitespace(self, article):
        """_emit_metadata_event('category', ...) debería limpiar espacios del valor."""
        # Arrange & Act
        article._emit_metadata_event("category", "  Technology  ", 0.95)

        # Assert
        events = article.get_uncommitted_events()
        new_event = events[-1]
        assert new_event.category == "Technology"  # Sin espacios

    def test_emit_metadata_event_category_is_equivalent_to_old_emit_categorized_event(
        self, article
    ):
        """_emit_metadata_event('category', ...) debería ser equivalente a _emit_categorized_event()."""
        # Este test verifica que el comportamiento es idéntico al método antiguo

        # Act
        article._emit_metadata_event("category", "Technology", 0.95)

        # Assert
        events = article.get_uncommitted_events()
        event = events[-1]

        # Verificar estructura del evento (igual que el antiguo)
        assert event.__class__.__name__ == "ArticleCategorized"
        assert hasattr(event, "aggregate_id")
        assert hasattr(event, "article_id")
        assert hasattr(event, "source_id")
        assert hasattr(event, "category")
        assert hasattr(event, "confidence")
        assert hasattr(event, "categorized_at")

        # Verificar valores
        assert event.category == "Technology"
        assert event.confidence == 0.95
        assert event.article_id == str(article.id)

    def test_emit_metadata_event_language_is_equivalent_to_old_emit_language_detected_event(
        self, article
    ):
        """_emit_metadata_event('language', ...) debería ser equivalente a _emit_language_detected_event()."""
        # Este test verifica que el comportamiento es idéntico al método antiguo

        # Act
        article._emit_metadata_event("language", "es", 0.92)

        # Assert
        events = article.get_uncommitted_events()
        event = events[-1]

        # Verificar estructura del evento (igual que el antiguo)
        assert event.__class__.__name__ == "ArticleLanguageDetected"
        assert hasattr(event, "aggregate_id")
        assert hasattr(event, "article_id")
        assert hasattr(event, "source_id")
        assert hasattr(event, "language_code")
        assert hasattr(event, "confidence")
        assert hasattr(event, "detected_at")

        # Verificar valores
        assert event.language_code == "es"
        assert event.confidence == 0.92
        assert event.article_id == str(article.id)

    def test_emit_metadata_event_events_are_identical_to_old_methods(self, article):
        """Eventos emitidos por _emit_metadata_event() deben ser idénticos a los antiguos."""
        # Este test verifica equivalencia completa

        # Test Category Event
        article._emit_metadata_event("category", "Tech", 0.9)
        category_event = article.get_uncommitted_events()[-1]

        assert category_event.aggregate_id == str(article.id)
        assert category_event.article_id == str(article.id)
        assert category_event.source_id == str(article.identity_vo.source_id)
        assert category_event.category == "Tech"
        assert category_event.confidence == 0.9
        assert isinstance(category_event.categorized_at, datetime)

        # Test Language Event
        article._emit_metadata_event("language", "fr", 0.85)
        language_event = article.get_uncommitted_events()[-1]

        assert language_event.aggregate_id == str(article.id)
        assert language_event.article_id == str(article.id)
        assert language_event.source_id == str(article.identity_vo.source_id)
        assert language_event.language_code == "fr"
        assert language_event.confidence == 0.85
        assert isinstance(language_event.detected_at, datetime)
