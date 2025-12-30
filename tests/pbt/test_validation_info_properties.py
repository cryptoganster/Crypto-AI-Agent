"""Property-based tests para ValidationInfo Value Object."""

from datetime import datetime, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.rss.article.domain.value_objects.validation_info import ValidationInfo


class TestValidationInfoProperties:
    """Property-based tests para ValidationInfo."""

    @given(
        score=st.floats(min_value=0.0, max_value=1.0),
        validated_by=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    )
    def test_property_validation_info_is_immutable(
        self, score: float, validated_by: str
    ):
        """
        Property 5: Validation info is immutable.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 4.2

        Para cualquier ValidationInfo creado,
        sus campos no deben poder modificarse (inmutabilidad).
        """
        # Arrange
        validation_info = ValidationInfo.create(score=score, validated_by=validated_by)

        # Act & Assert - Intentar modificar debe fallar
        with pytest.raises(AttributeError):
            validation_info.score = 0.5  # type: ignore

        with pytest.raises(AttributeError):
            validation_info.validated_by = "other"  # type: ignore

        with pytest.raises(AttributeError):
            validation_info.validated_at = datetime.now(timezone.utc)  # type: ignore

    @given(score=st.floats(min_value=0.0, max_value=1.0))
    def test_property_score_bounded(self, score: float):
        """
        Property 5: Validation info is immutable.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 4.2

        Para cualquier score válido,
        ValidationInfo debe aceptarlo.
        """
        # Act
        validation_info = ValidationInfo.create(
            score=score, validated_by="test_validator"
        )

        # Assert
        assert 0.0 <= validation_info.score <= 1.0
        assert validation_info.score == score

    @given(score=st.one_of(st.floats(max_value=-0.01), st.floats(min_value=1.01)))
    def test_property_invalid_score_rejected(self, score: float):
        """
        Property 5: Validation info is immutable.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 4.2

        Para cualquier score fuera del rango [0.0, 1.0],
        ValidationInfo debe rechazarlo.
        """
        # Act & Assert
        with pytest.raises(ValueError):
            ValidationInfo.create(score=score, validated_by="test_validator")

    @given(score=st.floats(min_value=0.7, max_value=1.0))
    def test_property_high_scores_are_high_quality(self, score: float):
        """
        Property 5: Validation info is immutable.

        Feature: article-aggregate-refactor, Property 5
        Validates: Requirements 4.2

        Para cualquier score >= 0.7,
        is_high_quality() debe retornar True.
        """
        # Arrange
        validation_info = ValidationInfo.create(
            score=score, validated_by="test_validator"
        )

        # Act & Assert
        assert validation_info.is_high_quality() is True
        assert validation_info.get_quality_level() == "high"
