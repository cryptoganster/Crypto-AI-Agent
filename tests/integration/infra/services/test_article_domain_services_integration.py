"""Integration tests for RssArticle Domain Services.

Tests the integration between Domain Services and RssArticle aggregate:
- ArticleHashingService calcula y RssArticle almacena hash
- ArticleKeywordService extrae y RssArticle almacena keywords
- ArticleQualityService evalúa y RssArticle almacena quality
- ArticleReadabilityService calcula y RssArticle almacena score
- ArticleDeduplicationService detecta duplicados
"""

from datetime import datetime, timezone

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.article.infra.services import (
    ArticleDeduplicationService,
    ArticleHashingService,
    ArticleKeywordService,
    ArticleQualityService,
    ArticleReadabilityService,
)
from src.rss.feed.domain.value_objects import RssFeedId
from src.shared.domain.value_objects import Level


@pytest.fixture
def article_factory():
    """Fixture para RssArticleFactory."""
    return RssArticleFactory()


@pytest.mark.integration
class TestRssArticleHashingServiceIntegration:
    """Integration tests for ArticleHashingService with Article aggregate."""

    def test_hashing_service_calculates_and_article_stores_hash(self, article_factory):
        """
        Debería calcular hash usando ArticleHashingService y RssArticle almacenarlo.

        Verifica que:
        1. El servicio puede calcular hash del artículo
        2. El artículo almacena el hash correctamente
        3. El hash es consistente para el mismo contenido
        """
        # Arrange
        article = article_factory.create_article(
            title="Test RssArticle for Hashing",
            url="https://example.com/test-hashing",
            source_id=RssFeedId("test-source-1"),
        )
        article.update_content_fields(
            markdown="This is test content for hashing integration."
        )

        hashing_service = ArticleHashingService()

        # Act - Generar y asignar hash
        content_hash = hashing_service.generate_and_assign_content_hash(article)

        # Assert - Verificar que el hash fue calculado y almacenado
        assert article.content_vo.markdown_hash is not None
        assert len(article.content_vo.markdown_hash) > 0
        assert article.content_vo.markdown_hash == content_hash.hash_value

        # Verificar consistencia - mismo contenido = mismo hash
        article2 = article_factory.create_article(
            title="Test RssArticle for Hashing",
            url="https://example.com/test-hashing",
            source_id=RssFeedId("test-source-1"),
        )
        article2.update_content_fields(
            markdown="This is test content for hashing integration."
        )

        content_hash2 = hashing_service.generate_and_assign_content_hash(article2)

        assert article.content_vo.markdown_hash == article2.content_hash
        assert content_hash.hash_value == content_hash2.hash_value

    def test_hashing_service_generates_different_hashes_for_different_content(
        self, article_factory
    ):
        """Debería generar hashes diferentes para contenido diferente."""
        # Arrange
        article1 = article_factory.create_article(
            title="RssArticle One",
            url="https://example.com/article-1",
            source_id=RssFeedId("test-source-1"),
        )
        article1.update_content_fields(markdown="Content for article one.")

        article2 = article_factory.create_article(
            title="RssArticle Two",
            url="https://example.com/article-2",
            source_id=RssFeedId("test-source-1"),
        )
        article2.update_content_fields(markdown="Content for article two.")

        hashing_service = ArticleHashingService()

        # Act
        hash1 = hashing_service.generate_and_assign_content_hash(article1)
        hash2 = hashing_service.generate_and_assign_content_hash(article2)

        # Assert
        assert article1.content_hash != article2.content_hash
        assert hash1.hash_value != hash2.hash_value

    def test_hashing_service_raises_error_for_article_without_content(
        self, article_factory
    ):
        """Debería lanzar excepción si el artículo no tiene contenido."""
        # Arrange
        article = article_factory.create_article(
            title="RssArticle Without Content",
            url="https://example.com/no-content",
            source_id=RssFeedId("test-source-1"),
        )
        # No asignar contenido

        hashing_service = ArticleHashingService()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            hashing_service.generate_and_assign_content_hash(article)

        assert "contenido" in str(exc_info.value).lower()


@pytest.mark.integration
class TestRssArticleKeywordServiceIntegration:
    """Integration tests for ArticleKeywordService with Article aggregate."""

    def test_keyword_service_extracts_and_article_stores_keywords(
        self, article_factory
    ):
        """
        Debería extraer keywords usando ArticleKeywordService y RssArticle almacenarlos.

        Verifica que:
        1. El servicio puede extraer keywords del artículo
        2. El artículo almacena los keywords correctamente
        3. Los keywords son relevantes al contenido
        """
        # Arrange
        article = article_factory.create_article(
            title="Python Programming Best Practices",
            url="https://example.com/python-practices",
            source_id=RssFeedId("test-source-1"),
        )
        article.update_content_fields(
            markdown="Python is a powerful programming language. "
            "Python developers use best practices for clean code. "
            "Programming in Python requires understanding of syntax and patterns. "
            "Python programming is popular for data science and web development."
        )

        keyword_service = ArticleKeywordService()

        # Act - Extraer keywords
        keywords = keyword_service.extract_keywords(article, max_keywords=5)

        # Asignar keywords al artículo
        if keywords:
            article.set_keywords(keywords)

        # Assert - Verificar que los keywords fueron extraídos y almacenados
        assert tuple(article.metadata.keywords.keywords) is not None
        assert len(tuple(article.metadata.keywords.keywords)) > 0
        assert "python" in [
            k.lower() for k in tuple(article.metadata.keywords.keywords)
        ]
        assert "programming" in [
            k.lower() for k in tuple(article.metadata.keywords.keywords)
        ]

    def test_keyword_service_respects_max_keywords_limit(self, article_factory):
        """Debería respetar el límite de max_keywords."""
        # Arrange
        article = article_factory.create_article(
            title="Technology RssArticle",
            url="https://example.com/tech",
            source_id=RssFeedId("test-source-1"),
        )
        article.update_content_fields(
            markdown="Technology innovation software development programming "
            "artificial intelligence machine learning data science "
            "cloud computing cybersecurity blockchain cryptocurrency "
            "internet networking database systems architecture design"
        )

        keyword_service = ArticleKeywordService()

        # Act
        keywords = keyword_service.extract_keywords(article, max_keywords=3)

        # Assert
        assert keywords is not None
        assert len(keywords) <= 3

    def test_keyword_service_raises_error_for_article_without_content(
        self, article_factory
    ):
        """Debería lanzar excepción si el artículo no tiene contenido."""
        # Arrange
        article = article_factory.create_article(
            title="RssArticle Without Content",
            url="https://example.com/no-content",
            source_id=RssFeedId("test-source-1"),
        )

        keyword_service = ArticleKeywordService()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            keyword_service.extract_keywords(article)

        assert "contenido" in str(exc_info.value).lower()


@pytest.mark.integration
class TestRssArticleQualityServiceIntegration:
    """Integration tests for ArticleQualityService with Article aggregate."""

    def test_quality_service_assesses_and_article_stores_quality(self, article_factory):
        """
        Debería evaluar calidad usando ArticleQualityService y RssArticle almacenarla.

        Verifica que:
        1. El servicio puede evaluar calidad del artículo
        2. El artículo almacena el nivel de calidad correctamente
        3. El nivel de calidad es válido
        """
        # Arrange
        article = article_factory.create_article(
            title="High Quality RssArticle with Good Content",
            url="https://example.com/quality-article",
            source_id=RssFeedId("test-source-1"),
        )
        # Contenido de calidad media-alta
        article.update_content_fields(
            markdown="This is a well-written article with substantial content. "
            "It provides valuable information and insights. "
            "The content is clear, concise, and easy to understand. "
            "It covers the topic comprehensively with good examples. "
            "The article maintains a professional tone throughout. "
            * 10  # Repetir para tener suficiente longitud
        )

        # Agregar metadatos para mejorar calidad
        article.set_summary("A comprehensive article about quality content.")
        article.add_tag("quality")
        article.add_tag("content")

        quality_service = ArticleQualityService()

        # Act - Evaluar calidad
        quality_level = quality_service.assess_quality(article)

        # Asignar calidad al artículo
        article.update_quality_assessment(quality_level=quality_level)

        # Assert - Verificar que la calidad fue evaluada y almacenada
        assert article.quality.quality_level is not None
        assert isinstance(article.quality.quality_level, Level)
        assert 0.0 <= article.quality.quality_level.score <= 1.0

    def test_quality_service_considers_multiple_factors(self, article_factory):
        """Debería considerar múltiples factores al evaluar calidad."""
        # Arrange - Artículo con buenos metadatos
        article_with_metadata = article_factory.create_article(
            title="Complete RssArticle with Metadata",
            url="https://example.com/complete",
            source_id=RssFeedId("test-source-1"),
        )
        article_with_metadata.update_content_fields(
            markdown="This article has complete metadata and good content. " * 50
        )
        article_with_metadata.set_summary("Complete article summary")
        article_with_metadata.add_tag("complete")
        article_with_metadata.add_tag("metadata")

        # Artículo sin metadatos
        article_without_metadata = article_factory.create_article(
            title="Incomplete RssArticle",
            url="https://example.com/incomplete",
            source_id=RssFeedId("test-source-1"),
        )
        article_without_metadata.update_content_fields(
            markdown="This article has minimal content and no metadata. " * 50
        )

        quality_service = ArticleQualityService()

        # Act
        quality_with_metadata = quality_service.assess_quality(article_with_metadata)
        quality_without_metadata = quality_service.assess_quality(
            article_without_metadata
        )

        # Assert - Artículo con metadatos debería tener mejor calidad
        assert quality_with_metadata.score > quality_without_metadata.score

    def test_quality_service_raises_error_for_insufficient_information(
        self, article_factory
    ):
        """Debería lanzar excepción si no hay suficiente información."""
        # Arrange - Artículo con título pero sin contenido
        article = article_factory.create_article(
            title="RssArticle Without Content",
            url="https://example.com/empty",
            source_id=RssFeedId("test-source-1"),
        )
        # No asignar contenido

        quality_service = ArticleQualityService()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            quality_service.assess_quality(article)

        # Verificar que el mensaje menciona contenido o título
        error_message = str(exc_info.value).lower()
        assert "contenido" in error_message or "título" in error_message


@pytest.mark.integration
class TestRssArticleReadabilityServiceIntegration:
    """Integration tests for ArticleReadabilityService with Article aggregate."""

    def test_readability_service_calculates_and_article_stores_score(
        self, article_factory
    ):
        """
        Debería calcular score usando ArticleReadabilityService y RssArticle almacenarlo.

        Verifica que:
        1. El servicio puede calcular readability score del artículo
        2. El artículo almacena el score correctamente
        3. El score está en el rango válido [0.0, 1.0]
        """
        # Arrange
        article = article_factory.create_article(
            title="Readable RssArticle",
            url="https://example.com/readable",
            source_id=RssFeedId("test-source-1"),
        )
        # Contenido simple y legible
        article.update_content_fields(
            markdown="This is a simple text. It is easy to read. "
            "The words are short. The sentences are clear. "
            "Anyone can understand this content easily."
        )

        readability_service = ArticleReadabilityService()

        # Act - Calcular readability
        readability_score = readability_service.calculate_readability_score(article)

        # Asignar score al artículo
        article.update_readability_score(readability_score)

        # Assert - Verificar que el score fue calculado y almacenado
        assert (
            article.quality.readability_score.value
            if article.quality.readability_score
            else None is not None
        )
        assert (
            0.0 <= article.quality.readability_score.value
            if article.quality.readability_score
            else None <= 1.0
        )
        assert (
            article.quality.readability_score.value
            if article.quality.readability_score
            else None
        ) == readability_score

    def test_readability_service_higher_score_for_simple_text(self, article_factory):
        """Debería dar score mayor para texto simple."""
        # Arrange - Texto simple
        simple_article = article_factory.create_article(
            title="Simple Text",
            url="https://example.com/simple",
            source_id=RssFeedId("test-source-1"),
        )
        simple_article.update_content_fields(
            markdown="This is easy. The cat sat. The dog ran. "
            "We can see. They will go. It is fun."
        )

        # Texto complejo
        complex_article = article_factory.create_article(
            title="Complex Text",
            url="https://example.com/complex",
            source_id=RssFeedId("test-source-1"),
        )
        complex_article.update_content_fields(
            markdown="The implementation of sophisticated algorithmic methodologies "
            "necessitates comprehensive understanding of computational complexity. "
            "Multidimensional optimization techniques facilitate enhancement "
            "of performance characteristics in distributed systems."
        )

        readability_service = ArticleReadabilityService()

        # Act
        simple_score = readability_service.calculate_readability_score(simple_article)
        complex_score = readability_service.calculate_readability_score(complex_article)

        # Assert - Texto simple debería tener score mayor
        assert simple_score > complex_score

    def test_readability_service_raises_error_for_article_without_content(
        self, article_factory
    ):
        """Debería lanzar excepción si el artículo no tiene contenido."""
        # Arrange
        article = article_factory.create_article(
            title="RssArticle Without Content",
            url="https://example.com/no-content",
            source_id=RssFeedId("test-source-1"),
        )

        readability_service = ArticleReadabilityService()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            readability_service.calculate_readability_score(article)

        assert "contenido" in str(exc_info.value).lower()


@pytest.mark.integration
class TestRssArticleDeduplicationServiceIntegration:
    """Integration tests for ArticleDeduplicationService with Article aggregate."""

    def test_deduplication_service_detects_duplicates_with_high_similarity(
        self, article_factory
    ):
        """
        Debería detectar duplicados usando ArticleDeduplicationService.

        Verifica que:
        1. El servicio puede detectar artículos duplicados
        2. Artículos con alta similitud son detectados como duplicados
        3. El threshold de similitud funciona correctamente
        """
        # Arrange
        original_article = article_factory.create_article(
            title="Python Best Practices for Clean Code",
            url="https://example.com/python-practices",
            source_id=RssFeedId("test-source-1"),
        )
        original_article.update_content_fields(
            markdown="Python is a powerful programming language. "
            "Following best practices ensures clean and maintainable code. "
            "This article covers essential Python coding standards."
        )

        # Artículo muy similar (duplicado)
        duplicate_article = article_factory.create_article(
            title="Python Best Practices for Clean Code",
            url="https://example.com/python-practices-copy",
            source_id=RssFeedId("test-source-1"),
        )
        duplicate_article.update_content_fields(
            markdown="Python is a powerful programming language. "
            "Following best practices ensures clean and maintainable code. "
            "This article covers essential Python coding standards."
        )

        deduplication_service = ArticleDeduplicationService(similarity_threshold=0.85)

        # Act
        is_duplicate = deduplication_service.is_duplicate(
            duplicate_article, [original_article]
        )

        # Assert
        assert is_duplicate is True

    def test_deduplication_service_does_not_detect_different_articles(
        self, article_factory
    ):
        """No debería detectar como duplicados artículos con baja similitud."""
        # Arrange
        article1 = article_factory.create_article(
            title="Python Programming",
            url="https://example.com/python",
            source_id=RssFeedId("test-source-1"),
        )
        article1.update_content_fields(
            markdown="Python is a high-level programming language known for its simplicity."
        )

        article2 = article_factory.create_article(
            title="JavaScript Development",
            url="https://example.com/javascript",
            source_id=RssFeedId("test-source-1"),
        )
        article2.update_content_fields(
            markdown="JavaScript is a versatile language used for web development."
        )

        deduplication_service = ArticleDeduplicationService(similarity_threshold=0.85)

        # Act
        is_duplicate = deduplication_service.is_duplicate(article2, [article1])

        # Assert
        assert is_duplicate is False

    def test_deduplication_service_respects_similarity_threshold(self, article_factory):
        """Debería respetar el threshold de similitud configurado."""
        # Arrange
        article1 = article_factory.create_article(
            title="Similar RssArticle One",
            url="https://example.com/similar-1",
            source_id=RssFeedId("test-source-1"),
        )
        article1.update_content_fields(
            markdown="This article discusses programming concepts and best practices."
        )

        article2 = article_factory.create_article(
            title="Similar RssArticle Two",
            url="https://example.com/similar-2",
            source_id=RssFeedId("test-source-1"),
        )
        article2.update_content_fields(
            markdown="This article discusses programming concepts and good practices."
        )

        # Threshold alto (0.95) - no debería detectar como duplicado
        strict_service = ArticleDeduplicationService(similarity_threshold=0.95)
        is_duplicate_strict = strict_service.is_duplicate(article2, [article1])

        # Threshold bajo (0.50) - debería detectar como duplicado
        lenient_service = ArticleDeduplicationService(similarity_threshold=0.50)
        is_duplicate_lenient = lenient_service.is_duplicate(article2, [article1])

        # Assert
        assert is_duplicate_strict is False
        assert is_duplicate_lenient is True

    def test_deduplication_service_find_duplicate_returns_article_id(
        self, article_factory
    ):
        """Debería retornar el ArticleId del duplicado encontrado."""
        # Arrange
        original = article_factory.create_article(
            title="Original RssArticle",
            url="https://example.com/original",
            source_id=RssFeedId("test-source-1"),
        )
        original.update_content_fields(markdown="Original content for testing.")

        duplicate = article_factory.create_article(
            title="Original RssArticle",
            url="https://example.com/duplicate",
            source_id=RssFeedId("test-source-1"),
        )
        duplicate.update_content_fields(markdown="Original content for testing.")

        deduplication_service = ArticleDeduplicationService(similarity_threshold=0.85)

        # Act
        duplicate_id = deduplication_service.find_duplicate(duplicate, [original])

        # Assert
        assert duplicate_id is not None
        assert duplicate_id == original.id
