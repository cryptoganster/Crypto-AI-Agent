"""Property-based tests para ReadabilityScore Value Object."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.rss.article.domain.value_objects.readability_score import ReadabilityScore


class TestReadabilityScoreProperties:
    """Property-based tests para ReadabilityScore."""

    @given(score=st.floats(min_value=0.0, max_value=1.0))
    def test_property_score_bounded_between_0_and_1(self, score: float):
        """
        Property 1: Score bounded between 0.0 and 1.0.

        Feature: article-aggregate-refactor, Property 1
        Validates: Requirements 4.2

        Para cualquier score válido entre 0.0 y 1.0,
        ReadabilityScore debe aceptarlo y almacenarlo correctamente.
        """
        # Act
        readability = ReadabilityScore(value=score)

        # Assert
        assert 0.0 <= readability.value <= 1.0
        assert readability.value == score

    @given(score=st.one_of(st.floats(max_value=-0.01), st.floats(min_value=1.01)))
    def test_property_invalid_scores_rejected(self, score: float):
        """
        Property 1: Score bounded between 0.0 and 1.0.

        Feature: article-aggregate-refactor, Property 1
        Validates: Requirements 4.2

        Para cualquier score fuera del rango [0.0, 1.0],
        ReadabilityScore debe rechazarlo con ValueError.
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ReadabilityScore(value=score)

        assert "entre 0.0 y 1.0" in str(exc_info.value)

    @given(score=st.floats(min_value=0.7, max_value=1.0))
    def test_property_high_scores_are_easy_to_read(self, score: float):
        """
        Property 1: Score bounded between 0.0 and 1.0.

        Feature: article-aggregate-refactor, Property 1
        Validates: Requirements 4.2

        Para cualquier score >= 0.7,
        is_easy_to_read() debe retornar True.
        """
        # Arrange
        readability = ReadabilityScore(value=score)

        # Act & Assert
        assert readability.is_easy_to_read() is True
        assert readability.is_difficult() is False

    @given(score=st.floats(min_value=0.0, max_value=0.29))
    def test_property_low_scores_are_difficult(self, score: float):
        """
        Property 1: Score bounded between 0.0 and 1.0.

        Feature: article-aggregate-refactor, Property 1
        Validates: Requirements 4.2

        Para cualquier score < 0.3,
        is_difficult() debe retornar True.
        """
        # Arrange
        readability = ReadabilityScore(value=score)

        # Act & Assert
        assert readability.is_difficult() is True
        assert readability.is_easy_to_read() is False

    @given(score=st.floats(min_value=0.3, max_value=0.69))
    def test_property_medium_scores_are_moderate(self, score: float):
        """
        Property 1: Score bounded between 0.0 and 1.0.

        Feature: article-aggregate-refactor, Property 1
        Validates: Requirements 4.2

        Para cualquier score entre 0.3 y 0.7,
        is_moderate() debe retornar True.
        """
        # Arrange
        readability = ReadabilityScore(value=score)

        # Act & Assert
        assert readability.is_moderate() is True
        assert readability.is_easy_to_read() is False
        assert readability.is_difficult() is False

    @given(score=st.floats(min_value=0.0, max_value=1.0))
    def test_property_readability_level_consistent(self, score: float):
        """
        Property 1: Score bounded between 0.0 and 1.0.

        Feature: article-aggregate-refactor, Property 1
        Validates: Requirements 4.2

        Para cualquier score válido,
        get_readability_level() debe retornar un nivel consistente con el score.
        """
        # Arrange
        readability = ReadabilityScore(value=score)

        # Act
        level = readability.get_readability_level()

        # Assert
        assert level in ["very_easy", "easy", "moderate", "difficult", "very_difficult"]

        # Verificar consistencia
        if score >= 0.9:
            assert level == "very_easy"
        elif score >= 0.7:
            assert level == "easy"
        elif score >= 0.5:
            assert level == "moderate"
        elif score >= 0.3:
            assert level == "difficult"
        else:
            assert level == "very_difficult"
