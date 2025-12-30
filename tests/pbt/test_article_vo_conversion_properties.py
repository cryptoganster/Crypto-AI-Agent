"""
Property-Based Tests para conversión a Value Objects en RssArticle.

**Feature: article-aggregate-refactor, Property 6: Value Objects validate on construction**
**Validates: Requirements 4.2, 6.5**

Estos tests verifican que los Value Objects validan correctamente sus valores
al ser construidos, rechazando valores inválidos y aceptando valores válidos.
"""

from datetime import datetime, timezone

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from src.rss.article.domain.value_objects.analysis import ReadingTime, WordCount
from src.rss.article.domain.value_objects.metadata import ArticleCategory
from src.rss.article.domain.value_objects.readability_score import ReadabilityScore
from src.rss.article.domain.value_objects.validation_info import ValidationInfo


class TestRssArticleVOConversionProperties:
    """Property tests para validación en construcción de VOs."""

    @given(
        name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        confidence=st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_article_category_validates_valid_inputs(self, name, confidence):
        """
        Property: ArticleCategory acepta nombres válidos y confidence en rango.

        Para cualquier nombre no vacío y confidence entre 0.0 y 1.0,
        ArticleCategory debe construirse exitosamente.
        """
        # Act
        category = ArticleCategory(name=name, confidence=confidence)

        # Assert
        assert category.name == name.strip().capitalize()
        assert 0.0 <= category.confidence <= 1.0

    @given(confidence=st.floats().filter(lambda x: x < 0.0 or x > 1.0))
    def test_article_category_rejects_invalid_confidence(self, confidence):
        """
        Property: ArticleCategory rechaza confidence fuera de rango.

        Para cualquier confidence < 0.0 o > 1.0,
        ArticleCategory debe lanzar ValueError.
        """
        # Arrange
        assume(not (0.0 <= confidence <= 1.0))

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ArticleCategory(name="Technology", confidence=confidence)

        assert "entre 0.0 y 1.0" in str(exc_info.value)

    @given(
        value=st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        )
    )
    def test_readability_score_validates_valid_inputs(self, value):
        """
        Property: ReadabilityScore acepta valores entre 0.0 y 1.0.

        Para cualquier valor entre 0.0 y 1.0,
        ReadabilityScore debe construirse exitosamente.
        """
        # Act
        score = ReadabilityScore(value=value)

        # Assert
        assert 0.0 <= score.value <= 1.0

    @given(value=st.floats().filter(lambda x: x < 0.0 or x > 1.0))
    def test_readability_score_rejects_invalid_values(self, value):
        """
        Property: ReadabilityScore rechaza valores fuera de rango.

        Para cualquier valor < 0.0 o > 1.0,
        ReadabilityScore debe lanzar ValueError.
        """
        # Arrange
        assume(not (0.0 <= value <= 1.0))

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ReadabilityScore(value=value)

        assert "entre 0.0 y 1.0" in str(exc_info.value)

    @given(value=st.integers(min_value=0, max_value=100000))
    def test_word_count_validates_non_negative_inputs(self, value):
        """
        Property: WordCount acepta valores no negativos.

        Para cualquier entero >= 0,
        WordCount debe construirse exitosamente.
        """
        # Act
        word_count = WordCount(value=value)

        # Assert
        assert word_count.value >= 0

    @given(value=st.integers(max_value=-1))
    def test_word_count_rejects_negative_values(self, value):
        """
        Property: WordCount rechaza valores negativos.

        Para cualquier entero < 0,
        WordCount debe lanzar ValueError.
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            WordCount(value=value)

        assert "no puede ser negativo" in str(exc_info.value)

    @given(minutes=st.integers(min_value=0, max_value=1000))
    def test_reading_time_validates_non_negative_inputs(self, minutes):
        """
        Property: ReadingTime acepta minutos no negativos.

        Para cualquier entero >= 0,
        ReadingTime debe construirse exitosamente.
        """
        # Act
        reading_time = ReadingTime(minutes=minutes)

        # Assert
        assert reading_time.minutes >= 0

    @given(minutes=st.integers(max_value=-1))
    def test_reading_time_rejects_negative_values(self, minutes):
        """
        Property: ReadingTime rechaza valores negativos.

        Para cualquier entero < 0,
        ReadingTime debe lanzar ValueError.
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ReadingTime(minutes=minutes)

        assert "no puede ser negativo" in str(exc_info.value)

    @given(
        score=st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
        validated_by=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    )
    def test_validation_info_validates_valid_inputs(self, score, validated_by):
        """
        Property: ValidationInfo acepta score válido y validador no vacío.

        Para cualquier score entre 0.0 y 1.0 y validador no vacío,
        ValidationInfo debe construirse exitosamente.
        """
        # Arrange
        validated_at = datetime.now(timezone.utc)

        # Act
        validation_info = ValidationInfo(
            score=score, validated_by=validated_by, validated_at=validated_at
        )

        # Assert
        assert 0.0 <= validation_info.score <= 1.0
        assert validation_info.validated_by.strip() != ""
        assert validation_info.validated_at.tzinfo is not None

    @given(score=st.floats().filter(lambda x: x < 0.0 or x > 1.0))
    def test_validation_info_rejects_invalid_score(self, score):
        """
        Property: ValidationInfo rechaza score fuera de rango.

        Para cualquier score < 0.0 o > 1.0,
        ValidationInfo debe lanzar ValueError.
        """
        # Arrange
        assume(not (0.0 <= score <= 1.0))
        validated_at = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ValidationInfo(
                score=score, validated_by="system", validated_at=validated_at
            )

        assert "entre 0.0 y 1.0" in str(exc_info.value)

    @given(
        word_count=st.integers(min_value=0, max_value=10000),
        wpm=st.integers(min_value=1, max_value=500),
    )
    def test_reading_time_from_word_count_property(self, word_count, wpm):
        """
        Property: ReadingTime.from_word_count calcula correctamente desde word count.

        Para cualquier word_count >= 0 y wpm > 0,
        el tiempo calculado debe ser >= 1 minuto.
        """
        # Act
        reading_time = ReadingTime.from_word_count(word_count, wpm)

        # Assert
        assert reading_time.minutes >= 1  # Mínimo 1 minuto
        if word_count > 0:
            expected_minutes = max(1, word_count // wpm)
            assert reading_time.minutes == expected_minutes

    @given(
        score=st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        )
    )
    def test_validation_info_quality_level_consistency(self, score):
        """
        Property: ValidationInfo quality level es consistente con score.

        Para cualquier score válido, el nivel de calidad debe ser consistente:
        - score >= 0.7 → high quality
        - 0.4 <= score < 0.7 → medium quality
        - score < 0.4 → low quality
        """
        # Arrange
        validation_info = ValidationInfo.create(score=score, validated_by="system")

        # Act & Assert
        if score >= 0.7:
            assert validation_info.is_high_quality()
            assert validation_info.get_quality_level() == "high"
        elif score >= 0.4:
            assert validation_info.is_medium_quality()
            assert validation_info.get_quality_level() == "medium"
        else:
            assert validation_info.is_low_quality()
            assert validation_info.get_quality_level() == "low"

    @given(value=st.integers(min_value=0, max_value=10000))
    def test_word_count_content_type_consistency(self, value):
        """
        Property: WordCount content type es consistente con valor.

        Para cualquier valor válido, el tipo de contenido debe ser consistente
        con los rangos definidos.
        """
        # Arrange
        word_count = WordCount(value=value)
        content_type = word_count.get_content_type()

        # Act & Assert
        if value == 0:
            assert content_type == "empty"
        elif value < 100:
            assert content_type == "snippet"
        elif value < 300:
            assert content_type == "short"
        elif value < 1000:
            assert content_type == "medium"
        elif value < 3000:
            assert content_type == "long"
        else:
            assert content_type == "very_long"

    @given(minutes=st.integers(min_value=0, max_value=100))
    def test_reading_time_category_consistency(self, minutes):
        """
        Property: ReadingTime category es consistente con minutos.

        Para cualquier valor válido de minutos, la categoría debe ser consistente
        con los rangos definidos.
        """
        # Arrange
        reading_time = ReadingTime(minutes=minutes)
        category = reading_time.get_reading_category()

        # Act & Assert
        if minutes <= 5:
            assert category == "quick"
        elif minutes <= 15:
            assert category == "medium"
        elif minutes <= 30:
            assert category == "long"
        else:
            assert category == "very_long"
