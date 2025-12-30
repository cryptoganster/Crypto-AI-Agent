"""Property-based tests para ReadingTime Value Object."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.rss.article.domain.value_objects.analysis import ReadingTime


class TestReadingTimeProperties:
    """Property-based tests para ReadingTime."""

    @given(
        word_count=st.integers(min_value=1, max_value=10000),
        wpm=st.integers(min_value=100, max_value=400),
    )
    def test_property_reading_time_calculated_from_word_count(
        self, word_count: int, wpm: int
    ):
        """
        Property 3: Reading time calculated from word count.

        Feature: article-aggregate-refactor, Property 3
        Validates: Requirements 4.2

        Para cualquier word_count y wpm válidos,
        ReadingTime debe calcular correctamente el tiempo de lectura.
        """
        # Act
        reading_time = ReadingTime.from_word_count(word_count, wpm)

        # Assert
        expected_minutes = max(1, word_count // wpm)
        assert reading_time.minutes == expected_minutes
        assert reading_time.minutes >= 1  # Mínimo 1 minuto

    @given(minutes=st.integers(min_value=0, max_value=1000))
    def test_property_reading_time_non_negative(self, minutes: int):
        """
        Property 3: Reading time calculated from word count.

        Feature: article-aggregate-refactor, Property 3
        Validates: Requirements 4.2

        Para cualquier tiempo no negativo,
        ReadingTime debe aceptarlo.
        """
        # Act
        reading_time = ReadingTime(minutes=minutes)

        # Assert
        assert reading_time.minutes >= 0
        assert int(reading_time) == minutes

    @given(minutes=st.integers(max_value=-1))
    def test_property_negative_time_rejected(self, minutes: int):
        """
        Property 3: Reading time calculated from word count.

        Feature: article-aggregate-refactor, Property 3
        Validates: Requirements 4.2

        Para cualquier tiempo negativo,
        ReadingTime debe rechazarlo.
        """
        # Act & Assert
        with pytest.raises(ValueError):
            ReadingTime(minutes=minutes)
