"""Tests para verificar encapsulación de Value Objects en RssArticle aggregate.

Tests para Optimización 9: Eliminar Dependencias Granulares.

Estos tests verifican que el RssArticle aggregate respeta los principios DDD
de encapsulación, delegando la creación de VOs granulares a los VOs compuestos.
"""

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleMetadataEncapsulation:
    """Tests para verificar que update_metadata() usa métodos helper de ArticleMetadata."""

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

    def test_update_metadata_delegates_author_creation_to_vo(self, sample_article):
        """Debería delegar creación de ArticleAuthor a ArticleMetadata.with_author()."""
        # Act
        sample_article.update_metadata_fields(author="John Doe")

        # Assert - Verificar que ArticleMetadata contiene ArticleAuthor VO
        assert sample_article.metadata.author is not None
        assert sample_article.metadata.author.value == "John Doe"
        # Verificar que es un VO válido (tiene los métodos esperados)
        assert hasattr(sample_article.metadata.author, "value")

    def test_update_metadata_delegates_language_creation_to_vo(self, sample_article):
        """Debería delegar creación de ContentLanguage a ArticleMetadata.with_language()."""
        # Act
        sample_article.update_language("en", 0.95)

        # Assert - Verificar que ArticleMetadata contiene ContentLanguage VO
        assert sample_article.metadata.language is not None
        assert sample_article.metadata.language.code == "en"
        assert sample_article.metadata.language.confidence == 0.95
        # Verificar que es un VO válido (tiene los atributos esperados)
        assert hasattr(sample_article.metadata.language, "code")
        assert hasattr(sample_article.metadata.language, "confidence")

    def test_update_metadata_delegates_category_creation_to_vo(self, sample_article):
        """Debería delegar creación de ArticleCategory a ArticleMetadata.with_category()."""
        # Act
        sample_article.update_category("Technology", 0.90)

        # Assert - Verificar que ArticleMetadata contiene ArticleCategory VO
        assert sample_article.metadata.category is not None
        assert sample_article.metadata.category.value == "Technology"
        # Verificar que es un VO válido (tiene los atributos esperados)
        assert hasattr(sample_article.metadata.category, "value")

    def test_update_metadata_preserves_vo_immutability(self, sample_article):
        """Debería preservar inmutabilidad de VOs al actualizar metadata."""
        # Arrange - Establecer metadata inicial
        sample_article.update_metadata_fields(
            author="Initial Author", language="en", category="Tech"
        )
        initial_metadata = sample_article.metadata_vo

        # Act - Actualizar solo author
        sample_article.update_metadata_fields(author="Updated Author")

        # Assert - El VO anterior no debe cambiar (inmutabilidad)
        assert initial_metadata.author.value == "Initial Author"
        assert sample_article.metadata.author.value == "Updated Author"
        # Verificar que es una nueva instancia
        assert sample_article.metadata_vo is not initial_metadata

    def test_update_metadata_creates_new_vo_instance(self, sample_article):
        """Debería crear nueva instancia de ArticleMetadata al actualizar."""
        # Arrange
        initial_metadata = sample_article.metadata_vo

        # Act
        sample_article.update_metadata_fields(author="New Author")

        # Assert - Debe ser una nueva instancia (inmutabilidad)
        assert sample_article.metadata_vo is not initial_metadata
        assert id(sample_article.metadata_vo) != id(initial_metadata)


class TestRssArticleQualityAssessmentEncapsulation:
    """Tests para verificar que update_quality_assessment() respeta encapsulación."""

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

    def test_update_quality_assessment_delegates_readability_score_creation(
        self, sample_article
    ):
        """Debería delegar creación de ReadabilityScore a QualityAssessment."""
        # Act
        sample_article.update_readability_score(0.85)

        # Assert - Verificar que QualityAssessment contiene ReadabilityScore VO
        assert sample_article.quality.readability_score is not None
        assert sample_article.quality.readability_score.value == 0.85
        # Verificar que es un VO válido
        assert hasattr(sample_article.quality.readability_score, "value")
        assert hasattr(sample_article.quality.readability_score, "is_easy_to_read")

    def test_update_quality_assessment_uses_vo_helper_methods(self, sample_article):
        """Debería usar métodos helper de QualityAssessment para actualizar."""
        # Arrange
        from src.shared.domain.value_objects import Level

        # Act
        sample_article.update_quality_assessment(
            quality_level=Level.high(), readability_score=0.90
        )

        # Assert - Verificar que ambos campos se actualizaron correctamente
        assert sample_article.quality.quality_level is not None
        assert sample_article.quality.quality_level.is_high()
        assert sample_article.quality.readability_score is not None
        assert sample_article.quality.readability_score.value == 0.90

    def test_update_quality_assessment_preserves_vo_immutability(self, sample_article):
        """Debería preservar inmutabilidad de QualityAssessment al actualizar."""
        # Arrange
        sample_article.update_readability_score(0.75)
        initial_quality = sample_article.quality_vo

        # Act
        sample_article.update_readability_score(0.85)

        # Assert - El VO anterior no debe cambiar
        assert initial_quality.readability_score.value == 0.75
        assert sample_article.quality.readability_score.value == 0.85
        # Verificar que es una nueva instancia
        assert sample_article.quality_vo is not initial_quality


class TestRssArticleEventEmission:
    """Tests para verificar que eventos se emiten correctamente después de refactor."""

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

    def test_update_metadata_emits_correct_language_event(self, sample_article):
        """Debería emitir ArticleLanguageDetected con datos correctos."""
        # Act
        sample_article.update_language("es", 0.98)

        # Assert
        events = sample_article.get_uncommitted_events()
        language_events = [
            e for e in events if e.event_type == "ArticleLanguageDetected"
        ]
        assert len(language_events) == 1

        event = language_events[0]
        assert event.language_code == "es"
        assert event.confidence == 0.98
        assert event.article_id == str(sample_article.id)

    def test_update_metadata_emits_correct_category_event(self, sample_article):
        """Debería emitir ArticleCategorized con datos correctos."""
        # Act
        sample_article.update_category("Science", 0.92)

        # Assert
        events = sample_article.get_uncommitted_events()
        category_events = [e for e in events if e.event_type == "ArticleCategorized"]
        assert len(category_events) == 1

        event = category_events[0]
        assert event.category == "Science"
        assert event.confidence == 0.92
        assert event.article_id == str(sample_article.id)

    def test_update_metadata_emits_both_events_correctly(self, sample_article):
        """Debería emitir ambos eventos con datos correctos al actualizar ambos campos."""
        # Act
        sample_article.update_metadata_fields(
            language="fr",
            category="Technology",
            language_confidence=0.95,
            category_confidence=0.88,
        )

        # Assert
        events = sample_article.get_uncommitted_events()

        language_events = [
            e for e in events if e.event_type == "ArticleLanguageDetected"
        ]
        category_events = [e for e in events if e.event_type == "ArticleCategorized"]

        assert len(language_events) == 1
        assert len(category_events) == 1

        assert language_events[0].language_code == "fr"
        assert language_events[0].confidence == 0.95
        assert category_events[0].category == "Technology"
        assert category_events[0].confidence == 0.88


class TestRssArticleBehaviorEquivalence:
    """Tests para verificar equivalencia de comportamiento antes/después del refactor."""

    @pytest.fixture
    def article_factory(self):
        """Factory para crear artículos de prueba."""
        return RssArticleFactory()

    def test_update_metadata_behavior_unchanged(self, article_factory):
        """Debería mantener el mismo comportamiento que antes del refactor."""
        # Arrange - Crear dos artículos idénticos
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

        # Act - Aplicar mismas operaciones
        article1.update_metadata_fields(
            author="John Doe",
            language="en",
            category="Tech",
            language_confidence=0.95,
            category_confidence=0.90,
        )
        article2.update_metadata_fields(
            author="John Doe",
            language="en",
            category="Tech",
            language_confidence=0.95,
            category_confidence=0.90,
        )

        # Assert - Deben tener el mismo estado
        assert article1.metadata.author.value == article2.metadata.author.value
        assert article1.metadata.language.code == article2.metadata.language.code
        assert (
            article1.metadata.language.confidence
            == article2.metadata.language.confidence
        )
        assert article1.metadata.category.value == article2.metadata.category.value

    def test_set_readability_score_behavior_unchanged(self, article_factory):
        """set_readability_score() es ahora un setter puro - NO emite eventos."""
        # Arrange
        article = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        initial_event_count = len(article.get_uncommitted_events())

        # Act
        article.update_readability_score(0.85)

        # Assert - Verificar que el score se estableció correctamente
        assert article.quality.readability_score is not None
        assert article.quality.readability_score.value == 0.85

        # Verificar que NO se emitió evento (es setter puro)
        final_event_count = len(article.get_uncommitted_events())
        assert final_event_count == initial_event_count

    def test_multiple_updates_maintain_consistency(self, article_factory):
        """Debería mantener consistencia a través de múltiples actualizaciones."""
        # Arrange
        article = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act - Múltiples actualizaciones
        article.update_metadata_fields(author="Author 1", language="en")
        article.update_metadata_fields(category="Tech")
        article.update_metadata_fields(author="Author 2")
        article.update_language("es", 0.98)

        # Assert - Estado final debe ser consistente
        assert article.metadata.author.value == "Author 2"
        assert article.metadata.language.code == "es"
        assert article.metadata.language.confidence == 0.98
        assert article.metadata.category.value == "Tech"
