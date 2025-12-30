"""Tests para ArticleCategory Value Object."""

import pytest

from src.rss.article.domain.value_objects.metadata import ArticleCategory


class TestRssArticleCategory:
    """Tests para ArticleCategory Value Object."""

    def test_create_valid_category(self):
        """Debería crear una categoría válida."""
        # Act
        category = ArticleCategory(name="Technology", confidence=0.9)

        # Assert
        assert category.name == "Technology"
        assert category.confidence == 0.9

    def test_create_normalizes_name(self):
        """Debería normalizar el nombre (strip y capitalize)."""
        # Act
        category = ArticleCategory(name="  technology  ", confidence=1.0)

        # Assert
        assert category.name == "Technology"

    def test_create_with_default_confidence(self):
        """Debería usar confidence=1.0 por defecto."""
        # Act
        category = ArticleCategory(name="Business")

        # Assert
        assert category.confidence == 1.0

    def test_create_with_empty_name_raises_error(self):
        """Debería lanzar error si name está vacío."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ArticleCategory(name="")

        assert "name no puede estar vacío" in str(exc_info.value)

    def test_create_with_whitespace_name_raises_error(self):
        """Debería lanzar error si name es solo espacios."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ArticleCategory(name="   ")

        assert "name no puede estar vacío" in str(exc_info.value)

    def test_create_with_invalid_confidence_raises_error(self):
        """Debería lanzar error si confidence está fuera de rango."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ArticleCategory(name="Sports", confidence=1.5)

        assert "confidence debe estar entre 0.0 y 1.0" in str(exc_info.value)

    def test_create_with_negative_confidence_raises_error(self):
        """Debería lanzar error si confidence es negativo."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ArticleCategory(name="Sports", confidence=-0.1)

        assert "confidence debe estar entre 0.0 y 1.0" in str(exc_info.value)

    def test_factory_method_create(self):
        """Debería crear categoría usando factory method."""
        # Act
        category = ArticleCategory.create("Entertainment", confidence=0.8)

        # Assert
        assert category.name == "Entertainment"
        assert category.confidence == 0.8

    def test_is_high_confidence_returns_true(self):
        """Debería retornar True para confidence > 0.7."""
        # Arrange
        category = ArticleCategory(name="Politics", confidence=0.85)

        # Act & Assert
        assert category.is_high_confidence() is True

    def test_is_high_confidence_returns_false(self):
        """Debería retornar False para confidence <= 0.7."""
        # Arrange
        category = ArticleCategory(name="Politics", confidence=0.6)

        # Act & Assert
        assert category.is_high_confidence() is False

    def test_is_low_confidence_returns_true(self):
        """Debería retornar True para confidence < 0.3."""
        # Arrange
        category = ArticleCategory(name="Health", confidence=0.2)

        # Act & Assert
        assert category.is_low_confidence() is True

    def test_is_low_confidence_returns_false(self):
        """Debería retornar False para confidence >= 0.3."""
        # Arrange
        category = ArticleCategory(name="Health", confidence=0.5)

        # Act & Assert
        assert category.is_low_confidence() is False

    def test_str_with_full_confidence(self):
        """Debería mostrar solo nombre si confidence=1.0."""
        # Arrange
        category = ArticleCategory(name="Science", confidence=1.0)

        # Act
        result = str(category)

        # Assert
        assert result == "Science"

    def test_str_with_partial_confidence(self):
        """Debería mostrar nombre y porcentaje si confidence<1.0."""
        # Arrange
        category = ArticleCategory(name="Science", confidence=0.75)

        # Act
        result = str(category)

        # Assert
        assert "Science" in result
        assert "75" in result or "0.8" in result  # Puede ser 75.0% o similar

    def test_repr(self):
        """Debería tener representación útil para debugging."""
        # Arrange
        category = ArticleCategory(name="Finance", confidence=0.9)

        # Act
        result = repr(category)

        # Assert
        assert "ArticleCategory" in result
        assert "Finance" in result
        assert "0.9" in result

    def test_immutability(self):
        """Debería ser inmutable (frozen dataclass)."""
        # Arrange
        category = ArticleCategory(name="Travel", confidence=0.8)

        # Act & Assert
        with pytest.raises(AttributeError):
            category.name = "Food"

    def test_equality(self):
        """Dos categorías con mismo nombre y confidence deberían ser iguales."""
        # Arrange
        cat1 = ArticleCategory(name="Music", confidence=0.9)
        cat2 = ArticleCategory(name="Music", confidence=0.9)

        # Act & Assert
        assert cat1 == cat2

    def test_inequality_different_name(self):
        """Categorías con diferente nombre deberían ser diferentes."""
        # Arrange
        cat1 = ArticleCategory(name="Music", confidence=0.9)
        cat2 = ArticleCategory(name="Art", confidence=0.9)

        # Act & Assert
        assert cat1 != cat2

    def test_inequality_different_confidence(self):
        """Categorías con diferente confidence deberían ser diferentes."""
        # Arrange
        cat1 = ArticleCategory(name="Music", confidence=0.9)
        cat2 = ArticleCategory(name="Music", confidence=0.8)

        # Act & Assert
        assert cat1 != cat2

    def test_hashable(self):
        """Debería ser hashable para usar en sets/dicts."""
        # Arrange
        cat1 = ArticleCategory(name="Gaming", confidence=0.95)
        cat2 = ArticleCategory(name="Gaming", confidence=0.95)

        # Act
        category_set = {cat1, cat2}

        # Assert
        assert len(category_set) == 1  # Mismo hash, solo uno en el set
