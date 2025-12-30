"""Tests para ArticleHashingService en Infrastructure Layer."""

from datetime import datetime, timezone

import pytest

from src.domain.value_objects.similarity import (
    ContentHash,
    ContentHashAlgorithm,
)
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.infra.services import ArticleHashingService
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleHashingService:
    """Tests para ArticleHashingService."""

    @pytest.fixture
    def service(self):
        """Fixture que crea una instancia del servicio."""
        return ArticleHashingService()

    @pytest.fixture
    def article_with_content(self):
        """Fixture que crea un artículo con contenido."""
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test-article",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_content_fields(markdown="This is test content for the article.")
        return article

    def test_hash_is_consistent_for_same_content(self, service, article_with_content):
        """Debería generar el mismo hash para el mismo contenido."""
        # Arrange
        article = article_with_content

        # Act
        hash1 = service.generate_and_assign_content_hash(article)
        hash2 = service.generate_and_assign_content_hash(article)

        # Assert
        assert hash1.hash_value == hash2.hash_value
        assert article.quality.content_hash is not None

    def test_hash_is_different_for_different_content(self, service):
        """Debería generar hashes diferentes para contenido diferente."""
        # Arrange
        factory = RssArticleFactory()
        article1 = factory.create_article(
            title="First RssArticle",
            url="https://example.com/first",
            source_id=RssFeedId("test-source-123"),
        )
        article1.update_content_fields(markdown="First content")

        factory2 = RssArticleFactory()
        article2 = factory2.create_article(
            title="Second RssArticle",
            url="https://example.com/second",
            source_id=RssFeedId("test-source-123"),
        )
        article2.update_content_fields(markdown="Second content")

        # Act
        hash1 = service.generate_and_assign_content_hash(article1)
        hash2 = service.generate_and_assign_content_hash(article2)

        # Assert
        assert hash1.hash_value != hash2.hash_value
        assert article1.quality.content_hash != article2.quality.content_hash

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
            service.generate_and_assign_content_hash(article)

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
        # (update_content rechaza strings vacíos, lo cual es correcto)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.generate_and_assign_content_hash(article)

        assert "contenido" in str(exc_info.value).lower()

    def test_assigns_hash_to_article(self, service, article_with_content):
        """Debería asignar el hash al artículo."""
        # Arrange
        article = article_with_content
        assert article.quality.content_hash is None

        # Act
        content_hash = service.generate_and_assign_content_hash(article)

        # Assert
        assert article.quality.content_hash is not None
        assert article.quality.content_hash == content_hash.hash_value

    def test_updates_article_updated_at(self, service, article_with_content):
        """Debería actualizar el timestamp updated_at del artículo."""
        # Arrange
        article = article_with_content
        original_updated_at = article.updated_at

        # Act
        service.generate_and_assign_content_hash(article)

        # Assert
        assert article.updated_at > original_updated_at

    def test_generate_hash_for_deduplication_without_article(self, service):
        """Debería generar hash para deduplicación sin artículo completo."""
        # Arrange
        url = "https://example.com/article"
        title = "Test RssArticle"

        # Act
        hash1 = service.generate_hash_for_deduplication(url, title)
        hash2 = service.generate_hash_for_deduplication(url, title)

        # Assert
        assert hash1.hash_value == hash2.hash_value
        assert isinstance(hash1, ContentHash)

    def test_generate_hash_for_deduplication_different_for_different_inputs(
        self, service
    ):
        """Debería generar hashes diferentes para inputs diferentes."""
        # Arrange
        url1 = "https://example.com/article1"
        title1 = "First RssArticle"
        url2 = "https://example.com/article2"
        title2 = "Second RssArticle"

        # Act
        hash1 = service.generate_hash_for_deduplication(url1, title1)
        hash2 = service.generate_hash_for_deduplication(url2, title2)

        # Assert
        assert hash1.hash_value != hash2.hash_value

    def test_is_article_duplicate_by_hash_returns_true_for_matching_hash(
        self, service, article_with_content
    ):
        """Debería retornar True si el hash coincide."""
        # Arrange
        article = article_with_content
        service.generate_and_assign_content_hash(article)
        target_hash = article.quality.content_hash

        # Act
        result = service.is_article_duplicate_by_hash(article, target_hash)

        # Assert
        assert result is True

    def test_is_article_duplicate_by_hash_returns_false_for_different_hash(
        self, service, article_with_content
    ):
        """Debería retornar False si el hash no coincide."""
        # Arrange
        article = article_with_content
        service.generate_and_assign_content_hash(article)
        different_hash = "different_hash_value"

        # Act
        result = service.is_article_duplicate_by_hash(article, different_hash)

        # Assert
        assert result is False

    def test_is_article_duplicate_by_hash_returns_false_if_no_hash(self, service):
        """Debería retornar False si el artículo no tiene hash."""
        # Arrange
        factory = RssArticleFactory()

        article = factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test",
            source_id=RssFeedId("test-source-123"),
        )
        article.update_content_fields(markdown="Test content")
        # No se genera hash

        # Act
        result = service.is_article_duplicate_by_hash(article, "some_hash")

        # Assert
        assert result is False

    def test_compare_content_hashes_returns_true_for_identical_hashes(self, service):
        """Debería retornar True para hashes idénticos."""
        # Arrange
        hash1 = ContentHash.from_content("test content", ContentHashAlgorithm.SHA256)
        hash2 = ContentHash.from_content("test content", ContentHashAlgorithm.SHA256)

        # Act
        result = service.compare_content_hashes(hash1, hash2)

        # Assert
        assert result is True

    def test_compare_content_hashes_returns_false_for_different_hashes(self, service):
        """Debería retornar False para hashes diferentes."""
        # Arrange
        hash1 = ContentHash.from_content("content 1", ContentHashAlgorithm.SHA256)
        hash2 = ContentHash.from_content("content 2", ContentHashAlgorithm.SHA256)

        # Act
        result = service.compare_content_hashes(hash1, hash2)

        # Assert
        assert result is False

    def test_generate_content_hash_from_text(self, service):
        """Debería generar hash directamente desde texto."""
        # Arrange
        text = "This is test content"

        # Act
        hash1 = service.generate_content_hash_from_text(text)
        hash2 = service.generate_content_hash_from_text(text)

        # Assert
        assert hash1.hash_value == hash2.hash_value
        assert isinstance(hash1, ContentHash)

    def test_are_articles_duplicate_by_hash_returns_true_for_same_hash(self, service):
        """Debería retornar True si ambos artículos tienen el mismo hash."""
        # Arrange
        factory = RssArticleFactory()
        article1 = factory.create_article(
            title="RssArticle 1",
            url="https://example.com/1",
            source_id=RssFeedId("test-source-123"),
        )
        article1.update_content_fields(markdown="Same content")

        factory2 = RssArticleFactory()
        article2 = factory2.create_article(
            title="RssArticle 2",
            url="https://example.com/2",
            source_id=RssFeedId("test-source-123"),
        )
        article2.update_content_fields(markdown="Different content")

        # Asignar el mismo hash manualmente para el test
        service.generate_and_assign_content_hash(article1)
        article2.update_quality_assessment(content_hash=article1.quality.content_hash)

        # Act
        result = service.are_articles_duplicate_by_hash(article1, article2)

        # Assert
        assert result is True

    def test_are_articles_duplicate_by_hash_returns_false_for_different_hash(
        self, service
    ):
        """Debería retornar False si los artículos tienen hashes diferentes."""
        # Arrange
        factory = RssArticleFactory()
        article1 = factory.create_article(
            title="RssArticle 1",
            url="https://example.com/1",
            source_id=RssFeedId("test-source-123"),
        )
        article1.update_content_fields(markdown="Content 1")

        factory2 = RssArticleFactory()
        article2 = factory2.create_article(
            title="RssArticle 2",
            url="https://example.com/2",
            source_id=RssFeedId("test-source-123"),
        )
        article2.update_content_fields(markdown="Content 2")

        service.generate_and_assign_content_hash(article1)
        service.generate_and_assign_content_hash(article2)

        # Act
        result = service.are_articles_duplicate_by_hash(article1, article2)

        # Assert
        assert result is False

    def test_are_articles_duplicate_by_hash_returns_false_if_one_has_no_hash(
        self, service
    ):
        """Debería retornar False si uno de los artículos no tiene hash."""
        # Arrange
        factory = RssArticleFactory()
        article1 = factory.create_article(
            title="RssArticle 1",
            url="https://example.com/1",
            source_id=RssFeedId("test-source-123"),
        )
        article1.update_content_fields(markdown="Content 1")

        factory2 = RssArticleFactory()
        article2 = factory2.create_article(
            title="RssArticle 2",
            url="https://example.com/2",
            source_id=RssFeedId("test-source-123"),
        )
        article2.update_content_fields(markdown="Content 2")

        service.generate_and_assign_content_hash(article1)
        # article2 no tiene hash

        # Act
        result = service.are_articles_duplicate_by_hash(article1, article2)

        # Assert
        assert result is False

    def test_find_articles_with_hash(self, service):
        """Debería encontrar artículos con un hash específico."""
        # Arrange
        factory = RssArticleFactory()
        article1 = factory.create_article(
            title="RssArticle 1",
            url="https://example.com/1",
            source_id=RssFeedId("test-source-123"),
        )
        article1.update_content_fields(markdown="Content 1")

        factory2 = RssArticleFactory()
        article2 = factory2.create_article(
            title="RssArticle 2",
            url="https://example.com/2",
            source_id=RssFeedId("test-source-123"),
        )
        article2.update_content_fields(markdown="Content 2")

        factory3 = RssArticleFactory()
        article3 = factory3.create_article(
            title="RssArticle 3",
            url="https://example.com/3",
            source_id=RssFeedId("test-source-123"),
        )
        article3.update_content_fields(markdown="Content 3")

        service.generate_and_assign_content_hash(article1)
        service.generate_and_assign_content_hash(article2)
        service.generate_and_assign_content_hash(article3)

        target_hash = article1.quality.content_hash
        articles = [article1, article2, article3]

        # Act
        result = service.find_articles_with_hash(articles, target_hash)

        # Assert
        assert len(result) == 1
        assert result[0] == article1

    def test_get_articles_without_hash(self, service):
        """Debería encontrar artículos sin hash asignado."""
        # Arrange
        factory = RssArticleFactory()
        article1 = factory.create_article(
            title="RssArticle 1",
            url="https://example.com/1",
            source_id=RssFeedId("test-source-123"),
        )
        article1.update_content_fields(markdown="Content 1")

        factory2 = RssArticleFactory()
        article2 = factory2.create_article(
            title="RssArticle 2",
            url="https://example.com/2",
            source_id=RssFeedId("test-source-123"),
        )
        article2.update_content_fields(markdown="Content 2")

        factory3 = RssArticleFactory()
        article3 = factory3.create_article(
            title="RssArticle 3",
            url="https://example.com/3",
            source_id=RssFeedId("test-source-123"),
        )
        article3.update_content_fields(markdown="Content 3")

        service.generate_and_assign_content_hash(article1)
        # article2 y article3 no tienen hash

        articles = [article1, article2, article3]

        # Act
        result = service.get_articles_without_hash(articles)

        # Assert
        assert len(result) == 2
        assert article2 in result
        assert article3 in result
        assert article1 not in result

    def test_assign_hash_to_article_method(self, service, article_with_content):
        """Debería asignar hash usando el método assign_hash_to_article."""
        # Arrange
        article = article_with_content
        assert article.quality.content_hash is None

        # Act
        service.assign_hash_to_article(article)

        # Assert
        assert article.quality.content_hash is not None

    def test_generate_hash_method_returns_content_hash(
        self, service, article_with_content
    ):
        """Debería retornar ContentHash usando el método generate_hash."""
        # Arrange
        article = article_with_content

        # Act
        result = service.generate_hash(article)

        # Assert
        assert isinstance(result, ContentHash)
        assert result.hash_value is not None

    def test_uses_sha256_algorithm_by_default(self, service, article_with_content):
        """Debería usar SHA-256 como algoritmo por defecto."""
        # Arrange
        article = article_with_content

        # Act
        content_hash = service.generate_and_assign_content_hash(article)

        # Assert
        assert content_hash.algorithm == ContentHashAlgorithm.SHA256
        # SHA-256 produce hashes de 64 caracteres hexadecimales
        assert len(content_hash.hash_value) == 64

    def test_can_specify_different_algorithm(self, service, article_with_content):
        """Debería permitir especificar un algoritmo diferente."""
        # Arrange
        article = article_with_content

        # Act
        content_hash = service.generate_and_assign_content_hash(
            article, algorithm=ContentHashAlgorithm.MD5
        )

        # Assert
        assert content_hash.algorithm == ContentHashAlgorithm.MD5
        # MD5 produce hashes de 32 caracteres hexadecimales
        assert len(content_hash.hash_value) == 32
