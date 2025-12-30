"""Tests para el método update_content_fields() de RssArticle aggregate.

Tests para Fase 2 del refactor: Consolidación de Setters Adicionales.
"""

import pytest

from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.factories.article_factory import RssArticleFactory
from src.rss.feed.domain.value_objects import RssFeedId


class TestRssArticleUpdateContentFields:
    """Tests para el método update_content_fields() del Article aggregate."""

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

    def test_update_content_fields_updates_markdown_only(self, sample_article):
        """Debería actualizar solo el campo markdown."""
        # Arrange
        initial_plaintext = sample_article.content_vo.plaintext
        initial_scrapped = sample_article.content_vo.scrapped

        # Act
        sample_article.update_content_fields(markdown="# New Title\n\nNew content")

        # Assert
        assert sample_article.content_vo.markdown == "# New Title\n\nNew content"
        assert sample_article.content_vo.plaintext == initial_plaintext
        assert sample_article.content_vo.scrapped == initial_scrapped

    def test_update_content_fields_updates_plaintext_only(self, sample_article):
        """Debería actualizar solo el campo plaintext."""
        # Arrange
        initial_markdown = sample_article.content_vo.markdown
        initial_scrapped = sample_article.content_vo.scrapped

        # Act
        sample_article.update_content_fields(plaintext="Plain text content")

        # Assert
        assert sample_article.content_vo.plaintext == "Plain text content"
        assert sample_article.content_vo.markdown == initial_markdown
        assert sample_article.content_vo.scrapped == initial_scrapped

    def test_update_content_fields_updates_scrapped_only(self, sample_article):
        """Debería actualizar solo el campo scrapped."""
        # Arrange
        initial_markdown = sample_article.content_vo.markdown
        initial_plaintext = sample_article.content_vo.plaintext

        # Act
        sample_article.update_content_fields(
            scrapped="<html><body>Content</body></html>"
        )

        # Assert
        assert sample_article.content_vo.scrapped == "<html><body>Content</body></html>"
        assert sample_article.content_vo.markdown == initial_markdown
        assert sample_article.content_vo.plaintext == initial_plaintext

    # Tests de actualización batch de múltiples campos

    def test_update_content_fields_updates_all_fields(self, sample_article):
        """Debería actualizar múltiples campos en batch."""
        # Act
        sample_article.update_content_fields(
            markdown="# Title\n\nContent",
            plaintext="Title Content",
            scrapped="<html><body>Content</body></html>",
        )

        # Assert
        assert sample_article.content_vo.markdown == "# Title\n\nContent"
        assert sample_article.content_vo.plaintext == "Title Content"
        assert sample_article.content_vo.scrapped == "<html><body>Content</body></html>"

    def test_update_content_fields_updates_plaintext_and_scrapped(self, sample_article):
        """Debería actualizar plaintext y scrapped juntos."""
        # Act
        sample_article.update_content_fields(
            plaintext="Plain text version", scrapped="<div>HTML version</div>"
        )

        # Assert
        assert sample_article.content_vo.plaintext == "Plain text version"
        assert sample_article.content_vo.scrapped == "<div>HTML version</div>"

    # Tests que solo campos proporcionados cambian

    def test_update_content_fields_preserves_unprovided_fields(self, sample_article):
        """Debería preservar campos no proporcionados."""
        # Arrange - Establecer valores iniciales
        sample_article.update_content_fields(
            markdown="# Initial",
            plaintext="Initial text",
            scrapped="<html>Initial</html>",
        )

        # Act - Actualizar solo markdown
        sample_article.update_content_fields(markdown="# Updated")

        # Assert - Otros campos deben permanecer sin cambios
        assert sample_article.content_vo.markdown == "# Updated"
        assert sample_article.content_vo.plaintext == "Initial text"
        assert sample_article.content_vo.scrapped == "<html>Initial</html>"

    def test_update_content_fields_with_no_parameters_does_nothing(
        self, sample_article
    ):
        """Debería no hacer nada si no se proporcionan parámetros."""
        # Arrange
        initial_markdown = sample_article.content_vo.markdown
        initial_plaintext = sample_article.content_vo.plaintext
        initial_scrapped = sample_article.content_vo.scrapped

        # Act
        sample_article.update_content_fields()

        # Assert
        assert sample_article.content_vo.markdown == initial_markdown
        assert sample_article.content_vo.plaintext == initial_plaintext
        assert sample_article.content_vo.scrapped == initial_scrapped

    # Tests de manejo de valores None

    def test_update_content_fields_sets_markdown_to_none(self, sample_article):
        """Debería establecer markdown a None cuando se pasa None."""
        # Arrange
        sample_article.update_content_fields(markdown="# Initial")
        assert sample_article.content_vo.markdown is not None

        # Act
        sample_article.update_content_fields(markdown=None)

        # Assert
        assert sample_article.content_vo.markdown is None

    def test_update_content_fields_sets_plaintext_to_none(self, sample_article):
        """Debería establecer plaintext a None cuando se pasa None."""
        # Arrange
        sample_article.update_content_fields(plaintext="Initial text")
        assert sample_article.content_vo.plaintext is not None

        # Act
        sample_article.update_content_fields(plaintext=None)

        # Assert
        assert sample_article.content_vo.plaintext is None

    def test_update_content_fields_sets_scrapped_to_none(self, sample_article):
        """Debería establecer scrapped a None cuando se pasa None."""
        # Arrange
        sample_article.update_content_fields(scrapped="<html>Initial</html>")
        assert sample_article.content_vo.scrapped is not None

        # Act
        sample_article.update_content_fields(scrapped=None)

        # Assert
        assert sample_article.content_vo.scrapped is None

    # Tests de actualización de timestamp

    def test_update_content_fields_updates_timestamp(self, sample_article):
        """Debería actualizar el timestamp updated_at."""
        # Arrange
        initial_updated_at = sample_article.updated_at

        # Act
        sample_article.update_content_fields(markdown="# New content")

        # Assert
        assert sample_article.updated_at > initial_updated_at


class TestRssArticleContentSettersAsWrappers:
    """Tests para verificar que los setters son wrappers de update_content_fields()."""

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

    def test_set_scrapped_content_is_equivalent_to_update_content_fields(
        self, sample_article
    ):
        """set_scrapped_content() debería ser equivalente a update_content_fields(scrapped=...)."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_content_fields(scrapped="<html><body>Test</body></html>")
        article2.update_content_fields(scrapped="<html><body>Test</body></html>")

        # Assert
        assert article1.content_vo.scrapped == article2.content_vo.scrapped

    def test_set_plaintext_content_is_equivalent_to_update_content_fields(
        self, sample_article
    ):
        """set_plaintext_content() debería ser equivalente a update_content_fields(plaintext=...)."""
        # Arrange
        article1 = sample_article
        article_factory = RssArticleFactory()
        article2 = article_factory.create_article(
            title="Test RssArticle",
            url="https://example.com/test2",
            source_id=RssFeedId("test-source-123"),
        )

        # Act
        article1.update_content_fields(plaintext="Plain text content")
        article2.update_content_fields(plaintext="Plain text content")

        # Assert
        assert article1.content_vo.plaintext == article2.content_vo.plaintext

    def test_set_scrapped_content_preserves_other_fields(self, sample_article):
        """set_scrapped_content() debería preservar otros campos de content."""
        # Arrange
        sample_article.update_content_fields(
            markdown="# Title",
            plaintext="Title",
        )
        initial_markdown = sample_article.content_vo.markdown
        initial_plaintext = sample_article.content_vo.plaintext

        # Act
        sample_article.update_content_fields(
            scrapped="<html><body>New HTML</body></html>"
        )

        # Assert
        assert (
            sample_article.content_vo.scrapped == "<html><body>New HTML</body></html>"
        )
        assert sample_article.content_vo.markdown == initial_markdown
        assert sample_article.content_vo.plaintext == initial_plaintext

    def test_set_plaintext_content_preserves_other_fields(self, sample_article):
        """set_plaintext_content() debería preservar otros campos de content."""
        # Arrange
        sample_article.update_content_fields(
            markdown="# Title",
            scrapped="<html>Title</html>",
        )
        initial_markdown = sample_article.content_vo.markdown
        initial_scrapped = sample_article.content_vo.scrapped

        # Act
        sample_article.update_content_fields(plaintext="New plain text")

        # Assert
        assert sample_article.content_vo.plaintext == "New plain text"
        assert sample_article.content_vo.markdown == initial_markdown
        assert sample_article.content_vo.scrapped == initial_scrapped
