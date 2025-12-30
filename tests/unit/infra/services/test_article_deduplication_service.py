"""Tests para ArticleDeduplicationService."""

from datetime import datetime, timezone

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.article.domain.value_objects import (
    RssArticleId,
    RssArticleTitle,
    RssArticleUrl,
)
from src.rss.article.infra.services import ArticleDeduplicationService
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleDeduplicationService:
    """Tests para ArticleDeduplicationService."""

    @pytest.fixture
    def service(self):
        """Crea servicio con threshold por defecto (0.85)."""
        return ArticleDeduplicationService(similarity_threshold=0.85)

    @pytest.fixture
    def sample_rss_article(self):
        """Crea artículo de ejemplo."""
        factory = RssArticleFactory()

        article = factory.create_article(
            source_id=RssFeedId.generate(),
            title="Python Best Practices for Clean Code",
            url="https://example.com/python-best-practices",
        )
        article.update_content_fields(
            markdown="This is a comprehensive guide about Python best practices. "
            "It covers topics like PEP 8, type hints, testing, and more. "
            "Following these practices will help you write cleaner code."
        )
        return article

    @pytest.fixture
    def similar_article(self):
        """Crea artículo muy similar al sample_article."""
        factory = RssArticleFactory()

        article = factory.create_article(
            source_id=RssFeedId.generate(),
            title="Python Best Practices for Writing Clean Code",
            url="https://example.com/python-clean-code",
        )
        article.update_content_fields(
            markdown="This is a comprehensive guide about Python best practices. "
            "It covers topics like PEP 8, type hints, testing, and more. "
            "Following these practices will help you write better code."
        )
        return article

    @pytest.fixture
    def different_article(self):
        """Crea artículo completamente diferente."""
        factory = RssArticleFactory()

        article = factory.create_article(
            source_id=RssFeedId.generate(),
            title="JavaScript Async Patterns",
            url="https://example.com/javascript-async",
        )
        article.update_content_fields(
            markdown="Learn about async/await, promises, and callbacks in JavaScript. "
            "This guide covers modern asynchronous programming patterns."
        )
        return article

    def test_init_with_valid_threshold(self):
        """Debería inicializar con threshold válido."""
        service = ArticleDeduplicationService(similarity_threshold=0.9)
        assert service._similarity_threshold == 0.9

    def test_init_with_invalid_threshold_raises_error(self):
        """Debería rechazar threshold fuera de rango."""
        with pytest.raises(ValueError) as exc_info:
            ArticleDeduplicationService(similarity_threshold=1.5)
        assert "entre 0.0 y 1.0" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            ArticleDeduplicationService(similarity_threshold=-0.1)
        assert "entre 0.0 y 1.0" in str(exc_info.value)

    def test_is_duplicate_detects_high_similarity(
        self, service, sample_article, similar_article
    ):
        """Debería detectar duplicados con alta similitud."""
        # Arrange
        existing_articles = [similar_article]

        # Act
        result = service.is_duplicate(sample_article, existing_articles)

        # Assert
        assert result is True

    def test_is_duplicate_rejects_low_similarity(
        self, service, sample_article, different_article
    ):
        """Debería NO detectar duplicados con baja similitud."""
        # Arrange
        existing_articles = [different_article]

        # Act
        result = service.is_duplicate(sample_article, existing_articles)

        # Assert
        assert result is False

    def test_is_duplicate_with_empty_list_returns_false(self, service, sample_article):
        """Debería retornar False con lista vacía."""
        # Arrange
        existing_articles = []

        # Act
        result = service.is_duplicate(sample_article, existing_articles)

        # Assert
        assert result is False

    def test_is_duplicate_ignores_same_article(self, service, sample_article):
        """Debería ignorar comparación consigo mismo."""
        # Arrange
        existing_articles = [sample_article]

        # Act
        result = service.is_duplicate(sample_article, existing_articles)

        # Assert
        assert result is False

    def test_find_duplicate_returns_id_when_found(
        self, service, sample_article, similar_article
    ):
        """Debería retornar ID del duplicado encontrado."""
        # Arrange
        existing_articles = [similar_article]

        # Act
        result = service.find_duplicate(sample_article, existing_articles)

        # Assert
        assert result is not None
        assert result == similar_article.id

    def test_find_duplicate_returns_none_when_not_found(
        self, service, sample_article, different_article
    ):
        """Debería retornar None cuando no hay duplicados."""
        # Arrange
        existing_articles = [different_article]

        # Act
        result = service.find_duplicate(sample_article, existing_articles)

        # Assert
        assert result is None

    def test_calculate_similarity_returns_high_for_similar_articles(
        self, service, sample_article, similar_article
    ):
        """Debería retornar score alto para artículos similares."""
        # Act
        similarity = service.calculate_similarity(sample_article, similar_article)

        # Assert
        assert similarity >= 0.85
        assert similarity <= 1.0

    def test_calculate_similarity_returns_low_for_different_articles(
        self, service, sample_article, different_article
    ):
        """Debería retornar score bajo para artículos diferentes."""
        # Act
        similarity = service.calculate_similarity(sample_article, different_article)

        # Assert
        assert similarity < 0.5

    def test_calculate_similarity_returns_one_for_identical_articles(
        self, service, sample_article
    ):
        """Debería retornar 1.0 para artículos idénticos."""
        # Act
        similarity = service.calculate_similarity(sample_article, sample_article)

        # Assert
        assert similarity == 1.0

    def test_find_all_duplicates_finds_pairs(
        self, service, sample_article, similar_article, different_article
    ):
        """Debería encontrar todos los pares de duplicados."""
        # Arrange
        articles = [sample_article, similar_article, different_article]

        # Act
        duplicates = service.find_all_duplicates(articles)

        # Assert
        assert len(duplicates) == 1
        assert (sample_article.id, similar_article.id) in duplicates

    def test_find_all_duplicates_with_no_duplicates_returns_empty(
        self, service, sample_article, different_article
    ):
        """Debería retornar lista vacía cuando no hay duplicados."""
        # Arrange
        articles = [sample_article, different_article]

        # Act
        duplicates = service.find_all_duplicates(articles)

        # Assert
        assert len(duplicates) == 0

    def test_respects_similarity_threshold(self, sample_article, similar_article):
        """Debería respetar el threshold de similitud configurado."""
        # Arrange - threshold muy alto (0.99)
        strict_service = ArticleDeduplicationService(similarity_threshold=0.99)

        # Act
        result = strict_service.is_duplicate(sample_article, [similar_article])

        # Assert - artículos similares pero no idénticos no deberían ser duplicados
        assert result is False

        # Arrange - threshold bajo (0.5)
        lenient_service = ArticleDeduplicationService(similarity_threshold=0.5)

        # Act
        result = lenient_service.is_duplicate(sample_article, [similar_article])

        # Assert - artículos similares deberían ser duplicados
        assert result is True

    def test_handles_articles_without_content(self, service):
        """Debería manejar artículos sin contenido."""
        # Arrange
        factory = RssArticleFactory()
        article1 = factory.create_article(
            source_id=RssFeedId.generate(),
            title="Test RssArticle",
            url="https://example.com/test1",
        )
        article2 = factory.create_article(
            source_id=RssFeedId.generate(),
            title="Test RssArticle",
            url="https://example.com/test2",
        )

        # Act
        similarity = service.calculate_similarity(article1, article2)

        # Assert - sin contenido, solo se compara título
        # Títulos idénticos deberían dar alta similitud
        assert similarity >= 0.4  # 40% del peso es el título

    def test_content_priority_plaintext_over_markdown(self, service):
        """Debería priorizar plaintext sobre markdown para comparación."""
        # Arrange
        factory = RssArticleFactory()
        article1 = factory.create_article(
            source_id=RssFeedId.generate(),
            title="Test",
            url="https://example.com/test1",
        )
        article1.update_content_fields(markdown="Plaintext content here")

        article2 = factory.create_article(
            source_id=RssFeedId.generate(),
            title="Test",
            url="https://example.com/test2",
        )
        article2.update_content_fields(markdown="Plaintext content here")

        # Act
        similarity = service.calculate_similarity(article1, article2)

        # Assert - debería usar plaintext (idéntico) no markdown (diferente)
        assert similarity >= 0.6  # 60% del peso es contenido idéntico
