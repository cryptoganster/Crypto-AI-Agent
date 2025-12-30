"""Tests unitarios para ArticleMetadata Value Object expandido."""

import pytest

from src.rss.article.domain.value_objects import RssArticleTitle
from src.rss.article.domain.value_objects.analysis import KeywordCollection
from src.rss.article.domain.value_objects.metadata import (
    ArticleCategory,
    ArticleLanguage,
    RssArticleAuthor,
    RssArticleMetadata,
    RssArticleSummary,
    RssArticleThumbnailUrl,
)
from src.shared.domain.value_objects import TagCollection


class TestRssArticleMetadataExpanded:
    """Tests para ArticleMetadata expandido con title, summary, thumbnail_url."""

    def test_create_with_title_required_succeeds(self):
        """Debería crear ArticleMetadata con title requerido."""
        # Arrange
        title = RssArticleTitle("Mi Artículo")

        # Act
        metadata = RssArticleMetadata.create(title=title)

        # Assert
        assert metadata.title == title
        assert metadata.summary is None
        assert metadata.thumbnail_url is None
        assert metadata.author is None
        assert metadata.language is None
        assert metadata.category is None

    def test_create_without_title_raises_value_error(self):
        """Debería lanzar ValueError cuando title es None."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            RssArticleMetadata.create(title=None)

        assert "title es requerido" in str(exc_info.value)

    def test_create_with_all_fields_succeeds(self):
        """Debería crear ArticleMetadata con todos los campos."""
        # Arrange
        title = RssArticleTitle("Mi Artículo")
        summary = RssArticleSummary("Resumen corto")
        thumbnail_url = RssArticleThumbnailUrl("https://example.com/image.jpg")
        author = RssArticleAuthor("Juan Pérez")
        language = ContentLanguage(code="es", confidence=0.95)
        category = ArticleCategory("Technology")
        tags = TagCollection.empty().add("python").add("testing")
        keywords = KeywordCollection.empty().add("unit test")

        # Act
        metadata = RssArticleMetadata.create(
            title=title,
            summary=summary,
            thumbnail_url=thumbnail_url,
            author=author,
            language=language,
            category=category,
            tags=tags,
            keywords=keywords,
        )

        # Assert
        assert metadata.title == title
        assert metadata.summary == summary
        assert metadata.thumbnail_url == thumbnail_url
        assert metadata.author == author
        assert metadata.language == language
        assert metadata.category == category
        assert metadata.tags == tags
        assert metadata.keywords == keywords

    def test_with_title_returns_new_instance(self):
        """Debería retornar nueva instancia con title actualizado."""
        # Arrange
        original_title = RssArticleTitle("Título Original")
        new_title = RssArticleTitle("Título Nuevo")
        metadata = RssArticleMetadata.empty_with_title(original_title)

        # Act
        updated = metadata.with_title(new_title)

        # Assert
        assert updated.title == new_title
        assert updated is not metadata  # Nueva instancia
        assert isinstance(updated, RssArticleMetadata)

    def test_with_title_does_not_modify_original_instance(self):
        """Debería no modificar instancia original (inmutabilidad)."""
        # Arrange
        original_title = RssArticleTitle("Título Original")
        new_title = RssArticleTitle("Título Nuevo")
        metadata = RssArticleMetadata.empty_with_title(original_title)

        # Act
        updated = metadata.with_title(new_title)

        # Assert
        assert metadata.title == original_title  # Original sin cambios
        assert updated.title == new_title  # Nueva instancia actualizada

    def test_with_summary_returns_new_instance(self):
        """Debería retornar nueva instancia con summary actualizado."""
        # Arrange
        title = RssArticleTitle("Título")
        summary = RssArticleSummary("Nuevo resumen")
        metadata = RssArticleMetadata.empty_with_title(title)

        # Act
        updated = metadata.with_summary(summary)

        # Assert
        assert updated.summary == summary
        assert updated is not metadata  # Nueva instancia
        assert isinstance(updated, RssArticleMetadata)

    def test_with_thumbnail_url_returns_new_instance(self):
        """Debería retornar nueva instancia con thumbnail_url actualizado."""
        # Arrange
        title = RssArticleTitle("Título")
        thumbnail_url = RssArticleThumbnailUrl("https://example.com/image.jpg")
        metadata = RssArticleMetadata.empty_with_title(title)

        # Act
        updated = metadata.with_thumbnail_url(thumbnail_url)

        # Assert
        assert updated.thumbnail_url == thumbnail_url
        assert updated is not metadata  # Nueva instancia
        assert isinstance(updated, RssArticleMetadata)

    def test_method_chaining_works_correctly(self):
        """Debería permitir encadenamiento de with_*() correctamente."""
        # Arrange
        title = RssArticleTitle("Título")
        metadata = RssArticleMetadata.empty_with_title(title)

        # Act
        updated = (
            metadata.with_title(RssArticleTitle("Nuevo Título"))
            .with_summary(RssArticleSummary("Resumen"))
            .with_thumbnail_url(RssArticleThumbnailUrl("https://example.com/img.jpg"))
            .with_author("Juan Pérez")
            .with_language("es", 0.95)
            .with_category("Technology")
            .add_tag("python")
            .add_keyword("testing")
        )

        # Assert
        assert str(updated.title) == "Nuevo Título"
        assert str(updated.summary) == "Resumen"
        assert updated.thumbnail_url.is_present
        assert str(updated.author) == "Juan Pérez"
        assert updated.language.code == "es"
        assert str(updated.category) == "Technology"
        assert "python" in updated.tags
        assert "testing" in updated.keywords

    def test_empty_with_title_creates_minimal_metadata(self):
        """Debería crear metadata mínima con solo title."""
        # Arrange
        title = RssArticleTitle("Mi Artículo")

        # Act
        metadata = RssArticleMetadata.empty_with_title(title)

        # Assert
        assert metadata.title == title
        assert metadata.summary is None
        assert metadata.thumbnail_url is None
        assert metadata.author is None
        assert metadata.language is None
        assert metadata.category is None
        assert metadata.tags.is_empty
        assert metadata.keywords.is_empty

    def test_immutability_preserved_in_all_operations(self):
        """Debería preservar inmutabilidad en todas las operaciones."""
        # Arrange
        title = RssArticleTitle("Título")
        metadata = RssArticleMetadata.empty_with_title(title)

        # Act & Assert - Intentar modificar directamente debería fallar
        with pytest.raises(Exception):  # FrozenInstanceError o AttributeError
            metadata.title = RssArticleTitle("Otro Título")

        with pytest.raises(Exception):
            metadata.summary = RssArticleSummary("Resumen")

        with pytest.raises(Exception):
            metadata.thumbnail_url = RssArticleThumbnailUrl(
                "https://example.com/img.jpg"
            )

        with pytest.raises(Exception):
            metadata.author = RssArticleAuthor("Autor")

    def test_all_fields_optional_except_title(self):
        """Debería permitir todos los campos opcionales excepto title."""
        # Arrange
        title = RssArticleTitle("Título")

        # Act
        metadata = RssArticleMetadata.create(
            title=title,
            summary=None,
            thumbnail_url=None,
            author=None,
            language=None,
            category=None,
            tags=None,
            keywords=None,
        )

        # Assert
        assert metadata.title == title
        assert metadata.summary is None
        assert metadata.thumbnail_url is None
        assert metadata.author is None
        assert metadata.language is None
        assert metadata.category is None
        assert metadata.tags.is_empty
        assert metadata.keywords.is_empty

    def test_with_summary_preserves_other_fields(self):
        """Debería preservar otros campos al actualizar summary."""
        # Arrange
        title = RssArticleTitle("Título")
        author = RssArticleAuthor("Juan Pérez")
        metadata = RssArticleMetadata.create(title=title, author=author)

        # Act
        updated = metadata.with_summary(RssArticleSummary("Resumen"))

        # Assert
        assert updated.title == title  # Preservado
        assert updated.author == author  # Preservado
        assert str(updated.summary) == "Resumen"  # Actualizado

    def test_with_thumbnail_url_preserves_other_fields(self):
        """Debería preservar otros campos al actualizar thumbnail_url."""
        # Arrange
        title = RssArticleTitle("Título")
        summary = RssArticleSummary("Resumen")
        metadata = RssArticleMetadata.create(title=title, summary=summary)

        # Act
        updated = metadata.with_thumbnail_url(
            RssArticleThumbnailUrl("https://example.com/img.jpg")
        )

        # Assert
        assert updated.title == title  # Preservado
        assert updated.summary == summary  # Preservado
        assert updated.thumbnail_url.is_present  # Actualizado

    def test_create_with_empty_tags_and_keywords_uses_defaults(self):
        """Debería usar colecciones vacías por defecto para tags y keywords."""
        # Arrange
        title = RssArticleTitle("Título")

        # Act
        metadata = RssArticleMetadata.create(title=title)

        # Assert
        assert metadata.tags.is_empty
        assert metadata.keywords.is_empty
        assert isinstance(metadata.tags, TagCollection)
        assert isinstance(metadata.keywords, KeywordCollection)

    def test_equality_by_value_works_correctly(self):
        """Debería comparar por valor correctamente."""
        # Arrange
        title = RssArticleTitle("Título")
        summary = RssArticleSummary("Resumen")

        metadata1 = RssArticleMetadata.create(title=title, summary=summary)
        metadata2 = RssArticleMetadata.create(
            title=RssArticleTitle("Título"), summary=RssArticleSummary("Resumen")
        )
        metadata3 = RssArticleMetadata.create(
            title=RssArticleTitle("Otro Título"), summary=summary
        )

        # Act & Assert
        assert metadata1 == metadata2  # Mismos valores
        assert metadata1 != metadata3  # Diferentes title
        assert metadata1 is not metadata2  # Diferentes instancias

    def test_with_title_maintains_all_other_fields(self):
        """Debería mantener todos los otros campos al actualizar title."""
        # Arrange
        metadata = RssArticleMetadata.create(
            title=RssArticleTitle("Título Original"),
            summary=RssArticleSummary("Resumen"),
            thumbnail_url=RssArticleThumbnailUrl("https://example.com/img.jpg"),
            author=RssArticleAuthor("Juan Pérez"),
            language=ContentLanguage(code="es", confidence=0.95),
            category=ArticleCategory("Technology"),
        )

        # Act
        updated = metadata.with_title(RssArticleTitle("Nuevo Título"))

        # Assert
        assert str(updated.title) == "Nuevo Título"
        assert updated.summary == metadata.summary
        assert updated.thumbnail_url == metadata.thumbnail_url
        assert updated.author == metadata.author
        assert updated.language == metadata.language
        assert updated.category == metadata.category

    def test_multiple_with_summary_calls_create_independent_instances(self):
        """Debería crear instancias independientes en múltiples llamadas."""
        # Arrange
        title = RssArticleTitle("Título")
        metadata = RssArticleMetadata.empty_with_title(title)

        # Act
        updated1 = metadata.with_summary(RssArticleSummary("Resumen 1"))
        updated2 = metadata.with_summary(RssArticleSummary("Resumen 2"))
        updated3 = updated1.with_summary(RssArticleSummary("Resumen 3"))

        # Assert
        assert metadata.summary is None  # Original sin cambios
        assert str(updated1.summary) == "Resumen 1"
        assert str(updated2.summary) == "Resumen 2"
        assert str(updated3.summary) == "Resumen 3"
        assert updated1 is not updated2
        assert updated1 is not updated3

    def test_frozen_dataclass_prevents_modification(self):
        """Debería prevenir modificación directa (frozen=True)."""
        # Arrange
        metadata = RssArticleMetadata.empty_with_title(RssArticleTitle("Título"))

        # Act & Assert
        with pytest.raises(Exception):
            metadata.tags = TagCollection.empty()

        with pytest.raises(Exception):
            metadata.keywords = KeywordCollection.empty()
