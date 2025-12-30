"""Property-based tests para WordCount Value Object."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.rss.article.domain.value_objects.analysis import WordCount


class TestWordCountProperties:
    """Property-based tests para WordCount."""

    @given(count=st.integers(min_value=0, max_value=100000))
    def test_property_word_count_is_non_negative(self, count: int):
        """
        Property 2: Word count is non-negative.

        Feature: article-aggregate-refactor, Property 2
        Validates: Requirements 4.2

        Para cualquier conteo no negativo,
        WordCount debe aceptarlo y almacenarlo correctamente.
        """
        # Act
        word_count = WordCount(value=count)

        # Assert
        assert word_count.value >= 0
        assert word_count.value == count
        assert int(word_count) == count

    @given(count=st.integers(max_value=-1))
    def test_property_negative_counts_rejected(self, count: int):
        """
        Property 2: Word count is non-negative.

        Feature: article-aggregate-refactor, Property 2
        Validates: Requirements 4.2

        Para cualquier conteo negativo,
        WordCount debe rechazarlo con ValueError.
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            WordCount(value=count)

        assert "no puede ser negativo" in str(exc_info.value)

    @given(count=st.integers(min_value=1000, max_value=100000))
    def test_property_high_counts_are_long_form(self, count: int):
        """
        Property 2: Word count is non-negative.

        Feature: article-aggregate-refactor, Property 2
        Validates: Requirements 4.2

        Para cualquier conteo >= 1000,
        is_long_form() debe retornar True.
        """
        # Arrange
        word_count = WordCount(value=count)

        # Act & Assert
        assert word_count.is_long_form() is True
        assert word_count.is_short_form() is False

    @given(count=st.integers(min_value=0, max_value=299))
    def test_property_low_counts_are_short_form(self, count: int):
        """
        Property 2: Word count is non-negative.

        Feature: article-aggregate-refactor, Property 2
        Validates: Requirements 4.2

        Para cualquier conteo < 300,
        is_short_form() debe retornar True.
        """
        # Arrange
        word_count = WordCount(value=count)

        # Act & Assert
        assert word_count.is_short_form() is True
        assert word_count.is_long_form() is False

    @given(count=st.integers(min_value=300, max_value=999))
    def test_property_medium_counts_are_medium_form(self, count: int):
        """
        Property 2: Word count is non-negative.

        Feature: article-aggregate-refactor, Property 2
        Validates: Requirements 4.2

        Para cualquier conteo entre 300 y 999,
        is_medium_form() debe retornar True.
        """
        # Arrange
        word_count = WordCount(value=count)

        # Act & Assert
        assert word_count.is_medium_form() is True
        assert word_count.is_short_form() is False
        assert word_count.is_long_form() is False
