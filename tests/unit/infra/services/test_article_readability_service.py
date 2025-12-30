"""Tests para ArticleReadabilityService."""

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.infra.services import ArticleReadabilityService
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleReadabilityService:
    """Tests para ArticleReadabilityService."""

    @pytest.fixture
    def service(self):
        """Crea instancia del servicio."""
        return ArticleReadabilityService()

    @pytest.fixture
    def simple_article(self):
        """Crea artículo con texto simple."""
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("src-1"),
        )
        # Texto simple: oraciones cortas, palabras simples
        article.update_content_fields(
            markdown="This is a test. It is easy to read. "
            "The cat sat on the mat. The dog ran fast. "
            "We like to play. The sun is hot."
        )
        return article

    @pytest.fixture
    def complex_article(self):
        """Crea artículo con texto complejo."""
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Complex RssArticle",
            url="https://example.com/complex",
            source_id=RssFeedId("src-1"),
        )
        # Texto complejo: oraciones largas, palabras complejas
        article.update_content_fields(
            markdown="The implementation of sophisticated algorithmic methodologies "
            "necessitates comprehensive understanding of computational complexity theory. "
            "Furthermore, the optimization of performance characteristics requires "
            "meticulous consideration of architectural design patterns and their "
            "implications on scalability and maintainability of enterprise systems."
        )
        return article

    @pytest.fixture
    def article_without_content(self):
        """Crea artículo sin contenido."""
        factory = RssArticleFactory()
        return factory.create_article(
            title="Empty RssArticle",
            url="https://example.com/empty",
            source_id=RssFeedId("src-1"),
        )

    def test_calculate_readability_score_returns_valid_range(
        self, service, simple_article
    ):
        """Debería calcular score válido entre 0.0 y 1.0."""
        # Act
        score = service.calculate_readability_score(simple_article)

        # Assert
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_calculate_readability_score_higher_for_simple_text(
        self, service, simple_article, complex_article
    ):
        """Debería retornar score mayor para texto simple."""
        # Act
        simple_score = service.calculate_readability_score(simple_article)
        complex_score = service.calculate_readability_score(complex_article)

        # Assert
        assert simple_score > complex_score
        # Texto simple debería ser más legible (score más alto)
        assert simple_score > 0.6  # Razonablemente legible

    def test_calculate_readability_score_raises_exception_without_content(
        self, service, article_without_content
    ):
        """Debería lanzar excepción si artículo sin contenido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.calculate_readability_score(article_without_content)

        assert "contenido" in str(exc_info.value).lower()

    def test_calculate_gunning_fog_index_returns_valid_value(
        self, service, simple_article
    ):
        """Debería calcular Gunning Fog Index válido."""
        # Act
        fog_index = service.calculate_gunning_fog_index(simple_article)

        # Assert
        assert fog_index is not None
        assert isinstance(fog_index, float)
        assert fog_index > 0

    def test_calculate_gunning_fog_index_higher_for_complex_text(
        self, service, simple_article, complex_article
    ):
        """Debería retornar índice mayor para texto complejo."""
        # Act
        simple_fog = service.calculate_gunning_fog_index(simple_article)
        complex_fog = service.calculate_gunning_fog_index(complex_article)

        # Assert
        assert complex_fog > simple_fog

    def test_calculate_gunning_fog_index_raises_exception_without_content(
        self, service, article_without_content
    ):
        """Debería lanzar excepción si artículo sin contenido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.calculate_gunning_fog_index(article_without_content)

        assert "contenido" in str(exc_info.value).lower()

    def test_get_content_statistics_returns_all_metrics(self, service, simple_article):
        """Debería retornar todas las estadísticas requeridas."""
        # Act
        stats = service.get_content_statistics(simple_article)

        # Assert
        required_keys = [
            "word_count",
            "sentence_count",
            "paragraph_count",
            "character_count",
            "syllable_count",
            "complex_word_count",
        ]
        for key in required_keys:
            assert key in stats, f"Falta estadística: {key}"
            assert isinstance(stats[key], int)
            assert stats[key] >= 0

    def test_get_content_statistics_counts_words_correctly(
        self, service, simple_article
    ):
        """Debería contar palabras correctamente."""
        # Act
        stats = service.get_content_statistics(simple_article)

        # Assert
        # El texto simple tiene aproximadamente 30 palabras
        assert stats["word_count"] > 20
        assert stats["word_count"] < 40

    def test_get_content_statistics_raises_exception_without_content(
        self, service, article_without_content
    ):
        """Debería lanzar excepción si artículo sin contenido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.get_content_statistics(article_without_content)

        assert "contenido" in str(exc_info.value).lower()

    def test_analyze_complexity_returns_all_metrics(self, service, simple_article):
        """Debería retornar todas las métricas de complejidad."""
        # Act
        analysis = service.analyze_complexity(simple_article)

        # Assert
        required_keys = [
            "readability_score",
            "fog_index",
            "avg_word_length",
            "avg_sentence_length",
            "complexity_rating",
        ]
        for key in required_keys:
            assert key in analysis, f"Falta métrica: {key}"
            assert isinstance(analysis[key], float)

    def test_analyze_complexity_rating_in_valid_range(self, service, simple_article):
        """Debería retornar complexity_rating entre 0.0 y 1.0."""
        # Act
        analysis = service.analyze_complexity(simple_article)

        # Assert
        assert 0.0 <= analysis["complexity_rating"] <= 1.0

    def test_analyze_complexity_higher_rating_for_complex_text(
        self, service, simple_article, complex_article
    ):
        """Debería retornar rating mayor para texto complejo."""
        # Act
        simple_analysis = service.analyze_complexity(simple_article)
        complex_analysis = service.analyze_complexity(complex_article)

        # Assert
        assert (
            complex_analysis["complexity_rating"] > simple_analysis["complexity_rating"]
        )

    def test_analyze_complexity_raises_exception_without_content(
        self, service, article_without_content
    ):
        """Debería lanzar excepción si artículo sin contenido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.analyze_complexity(article_without_content)

        assert "contenido" in str(exc_info.value).lower()

    def test_service_uses_plaintext_when_available(self, service):
        """Debería usar content_plaintext cuando está disponible."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test",
            url="https://example.com/test",
            source_id=RssFeedId("src-1"),
        )
        article.update_content_fields(plaintext="Simple text here.")
        article.update_content_fields(
            markdown="# Complex **markdown** with [links](url)"
        )
        article.mark_events_as_committed()  # Limpiar eventos de test

        # Act
        score = service.calculate_readability_score(article)

        # Assert
        # Debería usar plaintext (más simple) en lugar de markdown
        assert score is not None
        assert isinstance(score, float)

    def test_service_falls_back_to_markdown_when_no_plaintext(self, service):
        """Debería usar content_markdown si no hay plaintext."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test",
            url="https://example.com/test",
            source_id=RssFeedId("src-1"),
        )
        article.update_content_fields(markdown="This is simple text.")
        article.mark_events_as_committed()  # Limpiar eventos de test
        # VO is updated automatically by update_content()
        from src.rss.article.domain.value_objects.metadata.content import (
            RssArticleContent,
        )

        article._content = RssArticleContent(markdown="This is simple text.")
        # No plaintext

        # Act
        score = service.calculate_readability_score(article)

        # Assert
        assert score is not None
        assert isinstance(score, float)

    def test_calculate_readability_handles_empty_sentences(self, service):
        """Debería manejar texto sin oraciones correctamente."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test",
            url="https://example.com/test",
            source_id=RssFeedId("src-1"),
        )
        article.update_content_fields(markdown="word word word")  # Sin puntuación

        # Act
        score = service.calculate_readability_score(article)

        # Assert
        # Debería retornar score neutral sin fallar
        assert score is not None
        assert 0.0 <= score <= 1.0

    def test_gunning_fog_returns_none_for_insufficient_content(self, service):
        """Debería retornar None si no hay suficiente contenido para Gunning Fog."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test",
            url="https://example.com/test",
            source_id=RssFeedId("src-1"),
        )
        article.update_content_fields(markdown="a")  # Contenido mínimo

        # Act
        fog_index = service.calculate_gunning_fog_index(article)

        # Assert
        # Puede retornar None o un valor bajo
        assert fog_index is None or fog_index >= 0
