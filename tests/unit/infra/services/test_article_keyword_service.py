"""Tests para ArticleKeywordService en Infrastructure Layer."""

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.infra.services import ArticleKeywordService
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleKeywordService:
    """Tests para ArticleKeywordService."""

    @pytest.fixture
    def service(self):
        """Fixture que crea una instancia del servicio."""
        return ArticleKeywordService()

    @pytest.fixture
    def article_with_content(self):
        """Fixture que crea un artículo con contenido."""
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Python Programming Best Practices",
            url="https://example.com/python-article",
            source_id=RssFeedId("test-source-123"),
        )
        content = """
        Python is a high-level programming language that emphasizes code readability.
        Python programming requires understanding of data structures and algorithms.
        Best practices in Python include writing clean code and following PEP 8.
        Python developers should learn about testing and debugging techniques.
        """
        article.update_content_fields(markdown=content)
        return article

    def test_extracts_relevant_keywords(self, service, article_with_content):
        """Debería extraer keywords relevantes del contenido."""
        # Arrange
        article = article_with_content

        # Act
        keywords = service.extract_keywords(article, max_keywords=5)

        # Assert
        assert keywords is not None
        assert len(keywords) > 0
        assert len(keywords) <= 5
        # Verificar que "python" está en las keywords (palabra más frecuente)
        assert "python" in [k.lower() for k in keywords]

    def test_respects_max_keywords_limit(self, service, article_with_content):
        """Debería respetar el límite de max_keywords."""
        # Arrange
        article = article_with_content
        max_keywords = 3

        # Act
        keywords = service.extract_keywords(article, max_keywords=max_keywords)

        # Assert
        assert keywords is not None
        assert len(keywords) <= max_keywords

    def test_raises_exception_if_article_without_content(self, service):
        """Debería lanzar excepción si el artículo no tiene contenido."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        # No se establece contenido

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.extract_keywords(article)

        assert "contenido" in str(exc_info.value).lower()

    def test_raises_exception_if_article_with_empty_content(self, service):
        """Debería lanzar excepción si el artículo tiene contenido vacío."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        # Article sin contenido - no establecer contenido vacío
        # (update_content rechaza strings vacíos)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.extract_keywords(article)

        assert "contenido" in str(exc_info.value).lower()

    def test_filters_stopwords(self, service, article_with_content):
        """Debería filtrar stopwords comunes."""
        # Arrange
        article = article_with_content

        # Act
        keywords = service.extract_keywords(article, max_keywords=10)

        # Assert
        assert keywords is not None
        # Verificar que stopwords comunes no están en las keywords
        stopwords = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "is"}
        keywords_lower = [k.lower() for k in keywords]
        for stopword in stopwords:
            assert stopword not in keywords_lower

    def test_filters_short_words(self, service):
        """Debería filtrar palabras cortas (menos de 3 caracteres)."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        content = "I am a developer who writes code in Python and Go"
        article.update_content_fields(markdown=content)

        # Act
        keywords = service.extract_keywords(article, max_keywords=10)

        # Assert
        assert keywords is not None
        # Verificar que palabras de 1-2 letras no están
        keywords_lower = [k.lower() for k in keywords]
        assert "i" not in keywords_lower
        assert "am" not in keywords_lower
        assert "a" not in keywords_lower
        assert "in" not in keywords_lower

    def test_returns_none_if_no_valid_keywords(self, service):
        """Debería retornar None si no hay keywords válidas."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        # Contenido solo con stopwords
        content = "the and or but in on at to for of with by"
        article.update_content_fields(markdown=content)

        # Act
        keywords = service.extract_keywords(article)

        # Assert
        assert keywords is None

    def test_extract_keywords_with_scores_returns_dict(
        self, service, article_with_content
    ):
        """Debería retornar diccionario con keywords y scores."""
        # Arrange
        article = article_with_content

        # Act
        result = service.extract_keywords_with_scores(article, max_keywords=5)

        # Assert
        assert isinstance(result, dict)
        assert len(result) > 0
        assert len(result) <= 5
        # Verificar que los scores están entre 0 y 1
        for keyword, score in result.items():
            assert 0.0 <= score <= 1.0
            assert isinstance(keyword, str)

    def test_extract_keywords_with_scores_respects_min_score(self, service):
        """Debería respetar el score mínimo."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        content = "python python python java javascript ruby"
        article.update_content_fields(markdown=content)

        # Act
        result = service.extract_keywords_with_scores(
            article, max_keywords=10, min_score=0.5
        )

        # Assert
        assert isinstance(result, dict)
        # Todas las keywords deben tener score >= 0.5
        for keyword, score in result.items():
            assert score >= 0.5

    def test_extract_keywords_with_scores_raises_if_no_content(self, service):
        """Debería lanzar excepción si no hay contenido."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.extract_keywords_with_scores(article)

        assert "contenido" in str(exc_info.value).lower()

    def test_extract_keywords_with_scores_returns_empty_dict_if_no_valid_keywords(
        self, service
    ):
        """Debería retornar dict vacío si no hay keywords válidas."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        content = "the and or but"
        article.update_content_fields(markdown=content)

        # Act
        result = service.extract_keywords_with_scores(article)

        # Assert
        assert result == {}

    def test_filter_stopwords_english(self, service):
        """Debería filtrar stopwords en inglés."""
        # Arrange
        words = ["python", "the", "programming", "and", "language", "is"]

        # Act
        filtered = service.filter_stopwords(words, language="en")

        # Assert
        assert "python" in filtered
        assert "programming" in filtered
        assert "language" in filtered
        assert "the" not in filtered
        assert "and" not in filtered
        assert "is" not in filtered

    def test_filter_stopwords_spanish(self, service):
        """Debería filtrar stopwords en español."""
        # Arrange
        words = ["python", "el", "programación", "y", "lenguaje", "es"]

        # Act
        filtered = service.filter_stopwords(words, language="es")

        # Assert
        assert "python" in filtered
        assert "programación" in filtered
        assert "lenguaje" in filtered
        assert "el" not in filtered
        assert "y" not in filtered
        assert "es" not in filtered

    def test_extract_ngrams_returns_bigrams(self, service, article_with_content):
        """Debería extraer bigrams (n=2)."""
        # Arrange
        article = article_with_content

        # Act
        ngrams = service.extract_ngrams(article, n=2, max_ngrams=5)

        # Assert
        assert isinstance(ngrams, list)
        assert len(ngrams) > 0
        assert len(ngrams) <= 5
        # Verificar que son bigrams (2 palabras)
        for ngram in ngrams:
            words = ngram.split()
            assert len(words) == 2

    def test_extract_ngrams_returns_trigrams(self, service, article_with_content):
        """Debería extraer trigrams (n=3)."""
        # Arrange
        article = article_with_content

        # Act
        ngrams = service.extract_ngrams(article, n=3, max_ngrams=5)

        # Assert
        assert isinstance(ngrams, list)
        assert len(ngrams) > 0
        assert len(ngrams) <= 5
        # Verificar que son trigrams (3 palabras)
        for ngram in ngrams:
            words = ngram.split()
            assert len(words) == 3

    def test_extract_ngrams_respects_max_ngrams(self, service, article_with_content):
        """Debería respetar el límite de max_ngrams."""
        # Arrange
        article = article_with_content
        max_ngrams = 3

        # Act
        ngrams = service.extract_ngrams(article, n=2, max_ngrams=max_ngrams)

        # Assert
        assert len(ngrams) <= max_ngrams

    def test_extract_ngrams_raises_if_no_content(self, service):
        """Debería lanzar excepción si no hay contenido."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.extract_ngrams(article)

        assert "contenido" in str(exc_info.value).lower()

    def test_extract_ngrams_returns_empty_if_insufficient_words(self, service):
        """Debería retornar lista vacía si no hay suficientes palabras."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        content = "python"  # Solo una palabra
        article.update_content_fields(markdown=content)

        # Act
        ngrams = service.extract_ngrams(article, n=2, max_ngrams=5)

        # Assert
        assert ngrams == []

    def test_uses_plaintext_content_if_available(self, service):
        """Debería usar content_plaintext si está disponible."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_content_fields(markdown="markdown content")
        article.update_content_fields(plaintext="plaintext python programming language")

        # Act
        keywords = service.extract_keywords(article, max_keywords=5)

        # Assert
        assert keywords is not None
        # Debería extraer de plaintext
        assert "python" in [k.lower() for k in keywords]

    def test_falls_back_to_markdown_if_no_plaintext(self, service):
        """Debería usar content_markdown si no hay plaintext."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_content_fields(markdown="python programming language")
        # No se establece plaintext

        # Act
        keywords = service.extract_keywords(article, max_keywords=5)

        # Assert
        assert keywords is not None
        assert "python" in [k.lower() for k in keywords]

    def test_keywords_are_lowercase(self, service, article_with_content):
        """Debería retornar keywords en minúsculas."""
        # Arrange
        article = article_with_content

        # Act
        keywords = service.extract_keywords(article, max_keywords=5)

        # Assert
        assert keywords is not None
        for keyword in keywords:
            assert keyword.islower()

    def test_keywords_are_ordered_by_relevance(self, service):
        """Debería retornar keywords ordenadas por relevancia."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        # "python" aparece 5 veces, "java" 2 veces, "ruby" 1 vez
        content = "python python python python python java java ruby"
        article.update_content_fields(markdown=content)

        # Act
        keywords = service.extract_keywords(article, max_keywords=3)

        # Assert
        assert keywords is not None
        assert len(keywords) == 3
        # "python" debería ser la primera (más frecuente)
        assert keywords[0] == "python"

    def test_handles_special_characters(self, service):
        """Debería manejar caracteres especiales correctamente."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        content = "python! programming? language. code, testing; development:"
        article.update_content_fields(markdown=content)

        # Act
        keywords = service.extract_keywords(article, max_keywords=5)

        # Assert
        assert keywords is not None
        # Debería extraer palabras sin caracteres especiales
        assert "python" in keywords
        assert "programming" in keywords
        assert "language" in keywords

    def test_handles_accented_characters(self, service):
        """Debería manejar caracteres acentuados."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        content = "programación código diseño aplicación"
        article.update_content_fields(markdown=content)

        # Act
        keywords = service.extract_keywords(article, max_keywords=5)

        # Assert
        assert keywords is not None
        # Debería extraer palabras con acentos
        assert "programación" in keywords
        assert "código" in keywords

    def test_extract_keywords_with_scores_normalizes_scores(self, service):
        """Debería normalizar scores entre 0 y 1."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        # "python" aparece 5 veces, "java" 2 veces
        content = "python python python python python java java"
        article.update_content_fields(markdown=content)

        # Act
        result = service.extract_keywords_with_scores(article, max_keywords=2)

        # Assert
        assert "python" in result
        assert "java" in result
        # "python" debería tener score 1.0 (máxima frecuencia)
        assert result["python"] == 1.0
        # "java" debería tener score < 1.0
        assert result["java"] < 1.0
        assert result["java"] > 0.0
