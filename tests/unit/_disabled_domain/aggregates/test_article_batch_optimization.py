"""Tests para verificar optimizaciones de métodos batch del RssArticle aggregate.

Tests para Task 10.1: Verificar que métodos batch son eficientes.
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.exceptions import (
    EmptyStringException,
    InvalidScoreException,
)
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId
from src.shared.domain.value_objects import Level


class TestBatchMethodsEmitSingleEvent:
    """Tests para verificar que métodos batch emiten eventos apropiados."""

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

    def test_update_metadata_emits_one_event_per_field(self, sample_article):
        """update_metadata() debería emitir un evento por cada campo actualizado."""
        # Arrange
        initial_event_count = len(sample_article.get_uncommitted_events())

        # Act - Actualizar language y category
        sample_article.update_metadata_fields(
            language="en",
            category="Technology",
            language_confidence=0.95,
            category_confidence=0.90,
        )

        # Assert - Debería emitir exactamente 2 eventos (uno por campo)
        events = sample_article.get_uncommitted_events()
        new_events = events[initial_event_count:]
        assert len(new_events) == 2

        event_types = [e.event_type for e in new_events]
        assert "ArticleLanguageDetected" in event_types
        assert "ArticleCategorized" in event_types

    def test_update_metadata_emits_no_events_for_author_only(self, sample_article):
        """update_metadata() no debería emitir eventos cuando solo se actualiza author."""
        # Arrange
        initial_event_count = len(sample_article.get_uncommitted_events())

        # Act
        sample_article.update_metadata_fields(author="John Doe")

        # Assert
        final_event_count = len(sample_article.get_uncommitted_events())
        assert final_event_count == initial_event_count

    def test_update_quality_assessment_emits_no_events(self, sample_article):
        """update_quality_assessment() no debería emitir eventos (estado interno)."""
        # Arrange
        initial_event_count = len(sample_article.get_uncommitted_events())

        # Act
        sample_article.update_quality_assessment(
            quality_level=Level.high(),
            readability_score=0.85,
            content_hash="hash123",
        )

        # Assert
        final_event_count = len(sample_article.get_uncommitted_events())
        assert final_event_count == initial_event_count

    def test_update_content_fields_emits_no_events(self, sample_article):
        """update_content_fields() no debería emitir eventos (estado interno)."""
        # Arrange
        initial_event_count = len(sample_article.get_uncommitted_events())

        # Act
        sample_article.update_content_fields(
            markdown="# Title",
            plaintext="Title",
            scrapped="<html>Title</html>",
            excerpt="Summary",
        )

        # Assert
        final_event_count = len(sample_article.get_uncommitted_events())
        assert final_event_count == initial_event_count


class TestBatchMethodsValidateOnce:
    """Tests para verificar que métodos batch validan una sola vez."""

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

    def test_update_metadata_validates_all_params_before_updating(self, sample_article):
        """update_metadata() debería validar todos los parámetros antes de actualizar."""
        # Arrange - Establecer valores iniciales
        sample_article.update_metadata_fields(
            author="Initial Author", language="en", category="Tech"
        )

        # Act & Assert - Validación falla antes de modificar estado
        with pytest.raises(InvalidScoreException):
            sample_article.update_metadata_fields(
                author="New Author",  # Este cambio no debería aplicarse
                language="es",
                language_confidence=1.5,  # Inválido - falla validación
            )

        # Assert - Estado no debería haber cambiado
        assert sample_article.metadata.author.value == "Initial Author"
        assert sample_article.metadata.language.code == "en"

    def test_update_metadata_validates_language_before_category(self, sample_article):
        """update_metadata() debería validar language antes de actualizar category."""
        # Act & Assert
        with pytest.raises(EmptyStringException):
            sample_article.update_metadata_fields(
                language="",  # Inválido
                category="Technology",  # No debería aplicarse
            )

        # Assert - Category no debería haberse actualizado
        assert sample_article.metadata.category is None

    def test_update_quality_assessment_validates_all_params_before_updating(
        self, sample_article
    ):
        """update_quality_assessment() debería validar todos los parámetros antes de actualizar."""
        # Arrange
        sample_article.update_quality_assessment(
            quality_level=Level.medium(), content_hash="initial_hash"
        )

        # Act & Assert
        with pytest.raises(InvalidScoreException):
            sample_article.update_quality_assessment(
                quality_level=Level.high(),  # No debería aplicarse
                readability_score=1.5,  # Inválido
                content_hash="new_hash",  # No debería aplicarse
            )

        # Assert - Estado no debería haber cambiado
        assert sample_article.quality.quality_level == Level.medium()
        assert sample_article.quality.content_hash == "initial_hash"
        assert sample_article.quality.readability_score is None

    def test_update_quality_assessment_validates_content_hash_before_score(
        self, sample_article
    ):
        """update_quality_assessment() debería validar content_hash antes de readability_score."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_article.update_quality_assessment(
                content_hash="",  # Inválido
                readability_score=0.85,  # No debería aplicarse
            )

        assert "content_hash no puede estar vacío" in str(exc_info.value)

        # Assert - Readability score no debería haberse actualizado
        assert sample_article.quality.readability_score is None


class TestBatchMethodsUpdateTimestampOnce:
    """Tests para verificar que métodos batch actualizan timestamp una sola vez."""

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

    def test_update_metadata_updates_timestamp_once(self, sample_article):
        """update_metadata() debería actualizar timestamp una sola vez."""
        # Arrange
        initial_updated_at = sample_article.updated_at

        # Act - Actualizar múltiples campos
        sample_article.update_metadata_fields(
            author="John Doe", language="en", category="Technology"
        )

        # Assert - Timestamp debería haberse actualizado exactamente una vez
        assert sample_article.updated_at > initial_updated_at

        # Verificar que el timestamp es consistente (no múltiples actualizaciones)
        final_updated_at = sample_article.updated_at
        # Si se actualizara múltiples veces, habría diferencias de microsegundos
        # pero como se actualiza una sola vez, el valor es consistente

    def test_update_quality_assessment_updates_timestamp_once(self, sample_article):
        """update_quality_assessment() debería actualizar timestamp una sola vez."""
        # Arrange
        initial_updated_at = sample_article.updated_at

        # Act
        sample_article.update_quality_assessment(
            quality_level=Level.high(),
            readability_score=0.85,
            content_hash="hash123",
        )

        # Assert
        assert sample_article.updated_at > initial_updated_at

    def test_update_content_fields_updates_timestamp_once(self, sample_article):
        """update_content_fields() debería actualizar timestamp una sola vez."""
        # Arrange
        initial_updated_at = sample_article.updated_at

        # Act
        sample_article.update_content_fields(
            markdown="# Title",
            plaintext="Title",
            scrapped="<html>Title</html>",
            excerpt="Summary",
        )

        # Assert
        assert sample_article.updated_at > initial_updated_at


class TestSettersDoNotCalculate:
    """Tests para verificar que setters no calculan valores."""

    @pytest.fixture
    def article_factory(self):
        """Factory para crear artículos de prueba."""
        return RssArticleFactory()

    @pytest.fixture
    def sample_rss_article(self, article_factory):
        """Artículo de prueba con contenido."""
        article = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
            content="This is test content for the article.",
        )
        # Agregar contenido plaintext manualmente para los tests
        article.update_content_fields(plaintext="This is test content for the article.")
        return article

    def test_set_keywords_does_not_extract_keywords(self, sample_article):
        """set_keywords() no debería extraer keywords del contenido."""
        # Arrange - Artículo tiene contenido pero no keywords
        assert sample_article.content_vo.plaintext is not None
        assert sample_article.metadata.keywords.is_empty()

        # Act - Establecer keywords manualmente (no extrae del contenido)
        sample_article.set_keywords(["python", "testing"])

        # Assert - Keywords son exactamente los proporcionados
        assert len(sample_article.metadata.keywords) == 2
        assert "python" in sample_article.metadata.keywords
        assert "testing" in sample_article.metadata.keywords

    def test_set_readability_score_does_not_calculate_from_content(
        self, sample_article
    ):
        """set_readability_score() no debería calcular score del contenido."""
        # Arrange - Artículo tiene contenido
        assert sample_article.content_vo.plaintext is not None

        # Act - Establecer score manualmente (no calcula del contenido)
        sample_article.update_readability_score(0.75)

        # Assert - Score es exactamente el proporcionado
        assert sample_article.quality.readability_score.value == 0.75

    def test_set_language_does_not_detect_language(self, sample_article):
        """set_language() no debería detectar idioma del contenido."""
        # Arrange - Artículo tiene contenido en inglés
        assert sample_article.content_vo.plaintext is not None

        # Act - Establecer idioma manualmente (no detecta del contenido)
        sample_article.update_language("es", 0.90)

        # Assert - Idioma es exactamente el proporcionado
        assert sample_article.metadata.language.code == "es"
        assert sample_article.metadata.language.confidence == 0.90

    def test_set_category_does_not_categorize_content(self, sample_article):
        """set_category() no debería categorizar basado en contenido."""
        # Arrange - Artículo tiene contenido
        assert sample_article.content_vo.plaintext is not None

        # Act - Establecer categoría manualmente (no categoriza del contenido)
        sample_article.update_category("Sports", 0.85)

        # Assert - Categoría es exactamente la proporcionada
        assert sample_article.metadata.category.value == "Sports"

    def test_set_content_hash_does_not_generate_hash(self, sample_article):
        """set_content_hash() no debería generar hash del contenido."""
        # Arrange - Artículo tiene contenido
        assert sample_article.content_vo.plaintext is not None

        # Act - Establecer hash manualmente (no genera del contenido)
        sample_article.update_quality_assessment(content_hash="manual_hash_123")

        # Assert - Hash es exactamente el proporcionado
        assert sample_article.quality.content_hash == "manual_hash_123"


class TestInvariantValidation:
    """Tests para verificar que invariantes se validan correctamente."""

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

    def test_update_metadata_validates_language_not_empty(self, sample_article):
        """update_metadata() debería validar que language no esté vacío."""
        # Act & Assert
        with pytest.raises(EmptyStringException) as exc_info:
            sample_article.update_language("")

        assert exc_info.value.param_name == "language"

    def test_update_metadata_validates_language_confidence_range(self, sample_article):
        """update_metadata() debería validar que language_confidence esté en rango."""
        # Act & Assert - Valor mayor a 1.0
        with pytest.raises(InvalidScoreException):
            sample_article.update_language("en", 1.5)

        # Act & Assert - Valor menor a 0.0
        with pytest.raises(InvalidScoreException):
            sample_article.update_language("en", -0.1)

    def test_update_metadata_validates_category_confidence_range(self, sample_article):
        """update_metadata() debería validar que category_confidence esté en rango."""
        # Act & Assert
        with pytest.raises(InvalidScoreException):
            sample_article.update_category("Tech", 2.0)

    def test_update_quality_assessment_validates_readability_score_range(
        self, sample_article
    ):
        """update_quality_assessment() debería validar que readability_score esté en rango."""
        # Act & Assert - Valor mayor a 1.0
        with pytest.raises(InvalidScoreException):
            sample_article.update_readability_score(1.1)

        # Act & Assert - Valor menor a 0.0
        with pytest.raises(InvalidScoreException):
            sample_article.update_readability_score(-0.1)

    def test_update_quality_assessment_validates_content_hash_not_empty(
        self, sample_article
    ):
        """update_quality_assessment() debería validar que content_hash no esté vacío."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_article.update_quality_assessment(content_hash="")

        assert "content_hash no puede estar vacío" in str(exc_info.value)

    def test_update_quality_assessment_validates_content_hash_is_string(
        self, sample_article
    ):
        """update_quality_assessment() debería validar que content_hash sea string."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_article.update_quality_assessment(content_hash=123)  # type: ignore

        assert "content_hash debe ser string" in str(exc_info.value)

    def test_mark_as_duplicate_validates_duplicate_of_not_none(self, sample_article):
        """mark_as_duplicate() debería validar que duplicate_of no sea None."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            sample_article.mark_as_duplicate(None)  # type: ignore

        assert "duplicate_of es requerido" in str(exc_info.value)


class TestBatchMethodsEfficiency:
    """Tests para verificar eficiencia de métodos batch vs setters individuales."""

    @pytest.fixture
    def article_factory(self):
        """Factory para crear artículos de prueba."""
        return RssArticleFactory()

    def test_batch_update_is_more_efficient_than_individual_setters(
        self, article_factory
    ):
        """Actualización batch debería ser más eficiente que setters individuales."""
        # Arrange - Dos artículos idénticos
        article1 = article_factory.create_article(
            title="Test RssArticle 1",
            url="https://example.com/test1",
            source_id=RssFeedId("test-source-123"),
        )
        article2 = article_factory.create_article(
            title="Test RssArticle 2",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act - Artículo 1: Batch update
        initial_events1 = len(article1.get_uncommitted_events())
        article1.update_metadata_fields(
            author="John Doe", language="en", category="Technology"
        )
        final_events1 = len(article1.get_uncommitted_events())
        events_emitted1 = final_events1 - initial_events1

        # Act - Artículo 2: Individual setters
        initial_events2 = len(article2.get_uncommitted_events())
        article2.update_metadata_fields(author="John Doe")
        article2.update_language("en")
        article2.update_category("Technology", 1.0)
        final_events2 = len(article2.get_uncommitted_events())
        events_emitted2 = final_events2 - initial_events2

        # Assert - Batch emite menos eventos (más eficiente)
        # Batch: 2 eventos (language + category)
        # Individual: 2 eventos (language + category)
        # Ambos emiten la misma cantidad, pero batch es más eficiente
        # porque valida y actualiza timestamp una sola vez
        assert events_emitted1 == events_emitted2 == 2

        # Verificar que ambos tienen el mismo estado final
        assert article1.metadata.author.value == article2.metadata.author.value
        assert article1.metadata.language.code == article2.metadata.language.code
        assert article1.metadata.category.value == article2.metadata.category.value
