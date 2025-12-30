"""Tests para SourceReference value object."""

import pytest

from src.knowledge.domain.value_objects import SourceReference


class TestRssFeedReference:
    """Tests para SourceReference value object."""

    def test_create_valid_rss_article_reference(self):
        """Debería crear SourceReference válido para artículo RSS."""
        # Arrange & Act
        ref = SourceReference(
            source_type="rss_article",
            source_id="rss-article-123",
            source_url="https://example.com/article",
        )

        # Assert
        assert ref.source_type == "rss_article"
        assert ref.source_id == "rss-article-123"
        assert ref.source_url == "https://example.com/article"

    def test_is_rss_article_returns_true_for_rss_article(self):
        """Debería retornar True para artículo RSS."""
        # Arrange
        ref = SourceReference(
            source_type="rss_article",
            source_id="123",
            source_url="https://example.com",
        )

        # Act & Assert
        assert ref.is_rss_article() is True
        assert ref.is_tweet() is False
        assert ref.is_pdf() is False

    def test_is_tweet_returns_true_for_tweet(self):
        """Debería retornar True para tweet."""
        # Arrange
        ref = SourceReference(
            source_type="tweet",
            source_id="tweet-456",
            source_url="https://twitter.com/user/status/456",
        )

        # Act & Assert
        assert ref.is_tweet() is True
        assert ref.is_rss_article() is False
        assert ref.is_pdf() is False

    def test_is_pdf_returns_true_for_pdf(self):
        """Debería retornar True para PDF."""
        # Arrange
        ref = SourceReference(
            source_type="pdf_document",
            source_id="pdf-789",
            source_url="file:///path/to/document.pdf",
        )

        # Act & Assert
        assert ref.is_pdf() is True
        assert ref.is_rss_article() is False
        assert ref.is_tweet() is False

    def test_is_book_returns_true_for_book(self):
        """Debería retornar True para libro."""
        # Arrange
        ref = SourceReference(
            source_type="book",
            source_id="book-012",
            source_url="https://example.com/books/012",
        )

        # Act & Assert
        assert ref.is_book() is True
        assert ref.is_rss_article() is False

    def test_is_instagram_post_returns_true_for_instagram(self):
        """Debería retornar True para post de Instagram."""
        # Arrange
        ref = SourceReference(
            source_type="instagram_post",
            source_id="ig-345",
            source_url="https://instagram.com/p/345",
        )

        # Act & Assert
        assert ref.is_instagram_post() is True
        assert ref.is_rss_article() is False

    def test_is_linkedin_post_returns_true_for_linkedin(self):
        """Debería retornar True para post de LinkedIn."""
        # Arrange
        ref = SourceReference(
            source_type="linkedin_post",
            source_id="li-678",
            source_url="https://linkedin.com/posts/678",
        )

        # Act & Assert
        assert ref.is_linkedin_post() is True
        assert ref.is_rss_article() is False

    def test_get_bounded_context_returns_rss_for_rss_article(self):
        """Debería retornar 'rss' para artículo RSS."""
        # Arrange
        ref = SourceReference(
            source_type="rss_article",
            source_id="123",
            source_url="https://example.com",
        )

        # Act
        context = ref.get_bounded_context()

        # Assert
        assert context == "rss"

    def test_get_bounded_context_returns_twitter_for_tweet(self):
        """Debería retornar 'twitter' para tweet."""
        # Arrange
        ref = SourceReference(
            source_type="tweet",
            source_id="456",
            source_url="https://twitter.com/user/status/456",
        )

        # Act
        context = ref.get_bounded_context()

        # Assert
        assert context == "twitter"

    def test_get_bounded_context_returns_pdf_for_pdf_document(self):
        """Debería retornar 'pdf' para documento PDF."""
        # Arrange
        ref = SourceReference(
            source_type="pdf_document",
            source_id="789",
            source_url="file:///path/to/doc.pdf",
        )

        # Act
        context = ref.get_bounded_context()

        # Assert
        assert context == "pdf"

    def test_create_with_empty_source_type_raises_error(self):
        """Debería lanzar ValueError si source_type está vacío."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            SourceReference(
                source_type="",
                source_id="123",
                source_url="https://example.com",
            )

        assert "source_type no puede estar vacío" in str(exc_info.value)

    def test_create_with_whitespace_source_type_raises_error(self):
        """Debería lanzar ValueError si source_type es solo espacios."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            SourceReference(
                source_type="   ",
                source_id="123",
                source_url="https://example.com",
            )

        assert "source_type no puede estar vacío" in str(exc_info.value)

    def test_create_with_empty_source_id_raises_error(self):
        """Debería lanzar ValueError si source_id está vacío."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            SourceReference(
                source_type="rss_article",
                source_id="",
                source_url="https://example.com",
            )

        assert "source_id no puede estar vacío" in str(exc_info.value)

    def test_create_with_whitespace_source_id_raises_error(self):
        """Debería lanzar ValueError si source_id es solo espacios."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            SourceReference(
                source_type="rss_article",
                source_id="   ",
                source_url="https://example.com",
            )

        assert "source_id no puede estar vacío" in str(exc_info.value)

    def test_create_with_invalid_url_raises_error(self):
        """Debería lanzar ValueError si source_url no es válida."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            SourceReference(
                source_type="rss_article",
                source_id="123",
                source_url="not-a-valid-url",
            )

        assert "source_url debe ser una URL válida" in str(exc_info.value)

    def test_create_with_empty_url_raises_error(self):
        """Debería lanzar ValueError si source_url está vacía."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            SourceReference(
                source_type="rss_article",
                source_id="123",
                source_url="",
            )

        assert "source_url debe ser una URL válida" in str(exc_info.value)

    def test_create_with_invalid_source_type_raises_error(self):
        """Debería lanzar ValueError si source_type no es válido."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            SourceReference(
                source_type="invalid_type",
                source_id="123",
                source_url="https://example.com",
            )

        assert "source_type 'invalid_type' no es válido" in str(exc_info.value)
        assert "Tipos válidos:" in str(exc_info.value)

    def test_accepts_http_url(self):
        """Debería aceptar URLs con protocolo http://."""
        # Arrange & Act
        ref = SourceReference(
            source_type="rss_article",
            source_id="123",
            source_url="http://example.com/article",
        )

        # Assert
        assert ref.source_url == "http://example.com/article"

    def test_accepts_https_url(self):
        """Debería aceptar URLs con protocolo https://."""
        # Arrange & Act
        ref = SourceReference(
            source_type="rss_article",
            source_id="123",
            source_url="https://example.com/article",
        )

        # Assert
        assert ref.source_url == "https://example.com/article"

    def test_accepts_file_url(self):
        """Debería aceptar URLs con protocolo file://."""
        # Arrange & Act
        ref = SourceReference(
            source_type="pdf_document",
            source_id="123",
            source_url="file:///path/to/document.pdf",
        )

        # Assert
        assert ref.source_url == "file:///path/to/document.pdf"

    def test_is_immutable(self):
        """Debería ser inmutable (frozen dataclass)."""
        # Arrange
        ref = SourceReference(
            source_type="rss_article",
            source_id="123",
            source_url="https://example.com",
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            ref.source_type = "tweet"

        with pytest.raises(AttributeError):
            ref.source_id = "456"

        with pytest.raises(AttributeError):
            ref.source_url = "https://other.com"

    def test_equality_by_value(self):
        """Debería comparar por valor, no por identidad."""
        # Arrange
        ref1 = SourceReference(
            source_type="rss_article",
            source_id="123",
            source_url="https://example.com",
        )

        ref2 = SourceReference(
            source_type="rss_article",
            source_id="123",
            source_url="https://example.com",
        )

        ref3 = SourceReference(
            source_type="rss_article",
            source_id="456",
            source_url="https://example.com",
        )

        # Act & Assert
        assert ref1 == ref2
        assert ref1 != ref3
        assert ref1 is not ref2  # Diferentes instancias

    def test_can_be_used_as_dict_key(self):
        """Debería poder usarse como key en diccionario (hashable)."""
        # Arrange
        ref1 = SourceReference(
            source_type="rss_article",
            source_id="123",
            source_url="https://example.com",
        )

        ref2 = SourceReference(
            source_type="tweet",
            source_id="456",
            source_url="https://twitter.com/user/status/456",
        )

        # Act
        data = {
            ref1: "article_data",
            ref2: "tweet_data",
        }

        # Assert
        assert data[ref1] == "article_data"
        assert data[ref2] == "tweet_data"

    def test_can_be_used_in_set(self):
        """Debería poder usarse en set (hashable)."""
        # Arrange
        ref1 = SourceReference(
            source_type="rss_article",
            source_id="123",
            source_url="https://example.com",
        )

        ref2 = SourceReference(
            source_type="rss_article",
            source_id="123",
            source_url="https://example.com",
        )

        ref3 = SourceReference(
            source_type="tweet",
            source_id="456",
            source_url="https://twitter.com/user/status/456",
        )

        # Act
        refs = {ref1, ref2, ref3}

        # Assert
        assert len(refs) == 2  # ref1 y ref2 son iguales
        assert ref1 in refs
        assert ref3 in refs
