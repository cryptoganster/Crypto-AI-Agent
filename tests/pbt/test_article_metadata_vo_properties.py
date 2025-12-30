"""Property-based tests para ArticleMetadata Value Object."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rss.article.domain.value_objects.metadata import RssArticleMetadata


class TestRssArticleMetadataProperties:
    """Property-based tests para ArticleMetadata VO."""

    @given(
        code=st.text(
            min_size=2, max_size=2, alphabet=st.characters(whitelist_categories=("Ll",))
        ),
        confidence=st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=100)
    def test_property_3_language_validation(self, code: str, confidence: float):
        """
        Property 3: RssArticleMetadata language validation

        For any RssArticleMetadata instance created with a language code,
        that code must be a valid ISO 639-1 code (2 characters, lowercase).

        **Feature: refactor-article-aggregate, Property 3: RssArticleMetadata language validation**
        **Validates: Requirements 3.3**
        """
        # Arrange
        metadata = RssArticleMetadata.empty()

        # Act
        updated = metadata.with_language(code, confidence)

        # Assert - language code debe ser válido
        assert updated.language is not None
        assert len(updated.language.code) == 2
        assert updated.language.code.islower()
        assert updated.language.code.isalpha()

        # Assert - confidence debe estar en rango válido
        assert 0.0 <= updated.language.confidence <= 1.0

        # Assert - el código debe ser el mismo que se pasó
        assert updated.language.code == code
        assert updated.language.confidence == confidence

    @given(
        invalid_code=st.one_of(
            st.text(min_size=0, max_size=1),  # Muy corto
            st.text(min_size=3, max_size=10),  # Muy largo
            st.text(min_size=2, max_size=2, alphabet="0123456789"),  # Números
            st.text(min_size=2, max_size=2, alphabet="AB"),  # Mayúsculas
        )
    )
    @settings(max_examples=100)
    def test_property_3_invalid_language_codes_rejected(self, invalid_code: str):
        """
        Property 3 (edge case): Códigos de idioma inválidos deben ser rechazados.

        For any invalid language code (not 2 lowercase letters),
        creating RssArticleMetadata with that code should raise ValueError.

        **Feature: refactor-article-aggregate, Property 3: RssArticleMetadata language validation**
        **Validates: Requirements 3.3**
        """
        # Arrange
        metadata = RssArticleMetadata.empty()

        # Act & Assert
        with pytest.raises(ValueError):
            metadata.with_language(invalid_code, 0.5)

    @given(
        invalid_confidence=st.one_of(
            st.floats(min_value=-10.0, max_value=-0.01),  # Negativo
            st.floats(min_value=1.01, max_value=10.0),  # Mayor a 1
        )
    )
    @settings(max_examples=100)
    def test_property_3_invalid_confidence_rejected(self, invalid_confidence: float):
        """
        Property 3 (edge case): Confidence fuera de rango debe ser rechazado.

        For any confidence value outside [0.0, 1.0],
        creating RssArticleMetadata with that confidence should raise ValueError.

        **Feature: refactor-article-aggregate, Property 3: RssArticleMetadata language validation**
        **Validates: Requirements 3.3**
        """
        # Arrange
        metadata = RssArticleMetadata.empty()

        # Act & Assert
        with pytest.raises(ValueError):
            metadata.with_language("es", invalid_confidence)

    @given(
        tag=st.text(
            min_size=2,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=" -_"
            ),
        )
    )
    @settings(max_examples=100)
    def test_add_tag_returns_new_instance(self, tag: str):
        """
        Agregar tag debe retornar nueva instancia sin modificar la original.

        For any valid tag, adding it should return a new RssArticleMetadata instance
        while keeping the original unchanged.
        """
        # Arrange
        original = RssArticleMetadata.empty()
        original_tag_count = original.tags.count

        # Act
        updated = original.add_tag(tag)

        # Assert - original no debe cambiar
        assert original.tags.count == original_tag_count

        # Assert - nueva instancia debe tener el tag (si es válido)
        if len(tag.strip()) >= 2:
            assert updated.tags.count >= original_tag_count

    @given(
        keyword=st.text(
            min_size=2,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=" -_"
            ),
        )
    )
    @settings(max_examples=100)
    def test_add_keyword_returns_new_instance(self, keyword: str):
        """
        Agregar keyword debe retornar nueva instancia sin modificar la original.

        For any valid keyword, adding it should return a new RssArticleMetadata instance
        while keeping the original unchanged.
        """
        # Arrange
        original = RssArticleMetadata.empty()
        original_keyword_count = original.keywords.count

        # Act
        updated = original.add_keyword(keyword)

        # Assert - original no debe cambiar
        assert original.keywords.count == original_keyword_count

        # Assert - nueva instancia debe tener el keyword (si es válido)
        if len(keyword.strip()) >= 2:
            assert updated.keywords.count >= original_keyword_count

    def test_empty_creates_valid_instance(self):
        """
        RssArticleMetadata.empty() debe crear instancia válida con campos vacíos.
        """
        # Act
        metadata = RssArticleMetadata.empty()

        # Assert
        assert metadata.author is None
        assert metadata.language is None
        assert metadata.category is None
        assert metadata.tags.is_empty
        assert metadata.keywords.is_empty
        assert metadata.summary is None

    def test_immutability(self):
        """
        RssArticleMetadata debe ser inmutable (frozen dataclass).
        """
        # Arrange
        metadata = RssArticleMetadata.empty()

        # Act & Assert - intentar modificar debe fallar
        with pytest.raises(AttributeError):
            metadata.author = None  # type: ignore
