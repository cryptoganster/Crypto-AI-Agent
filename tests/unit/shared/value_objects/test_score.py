"""Tests para Score Value Object."""

import pytest

from src.shared.domain.value_objects.score import Score


class TestScoreCreation:
    """Tests para creación de Score."""

    def test_create_valid_score(self):
        """Debería crear score válido."""
        score = Score(0.75)
        assert score.value == 0.75

    def test_create_with_description(self):
        """Debería crear score con descripción."""
        score = Score(0.8, description="Quality score")
        assert score.value == 0.8
        assert score.description == "Quality score"

    def test_create_at_minimum(self):
        """Debería crear score en mínimo (0.0)."""
        score = Score(0.0)
        assert score.value == 0.0

    def test_create_at_maximum(self):
        """Debería crear score en máximo (1.0)."""
        score = Score(1.0)
        assert score.value == 1.0

    def test_create_with_invalid_type_raises_error(self):
        """Debería lanzar TypeError con tipo inválido."""
        with pytest.raises(TypeError) as exc_info:
            Score("0.5")
        assert "must be numeric" in str(exc_info.value)

    def test_create_below_minimum_raises_error(self):
        """Debería lanzar ValueError si está debajo del mínimo."""
        with pytest.raises(ValueError) as exc_info:
            Score(-0.1)
        assert "between 0.0 and 1.0" in str(exc_info.value)

    def test_create_above_maximum_raises_error(self):
        """Debería lanzar ValueError si está arriba del máximo."""
        with pytest.raises(ValueError) as exc_info:
            Score(1.5)
        assert "between 0.0 and 1.0" in str(exc_info.value)


class TestScoreFactoryMethods:
    """Tests para factory methods."""

    def test_create_factory_method(self):
        """Debería crear score con factory method."""
        score = Score.create(0.6, description="Test")
        assert score.value == 0.6
        assert score.description == "Test"

    def test_zero_factory(self):
        """Debería crear score cero."""
        score = Score.zero()
        assert score.value == 0.0
        assert score.is_zero()

    def test_maximum_factory(self):
        """Debería crear score máximo."""
        score = Score.maximum()
        assert score.value == 1.0
        assert score.is_maximum()

    def test_half_factory(self):
        """Debería crear score medio."""
        score = Score.half()
        assert score.value == 0.5

    def test_low_factory(self):
        """Debería crear score bajo."""
        score = Score.low()
        assert score.value == 0.3
        assert score.is_low()

    def test_high_factory(self):
        """Debería crear score alto."""
        score = Score.high()
        assert score.value == 0.8
        assert score.is_high()


class TestScoreClassification:
    """Tests para clasificación de scores."""

    def test_is_high_returns_true_for_high_score(self):
        """Debería identificar score alto."""
        score = Score(0.75)
        assert score.is_high()

    def test_is_high_returns_false_for_low_score(self):
        """Debería identificar que no es alto."""
        score = Score(0.5)
        assert not score.is_high()

    def test_is_medium_returns_true_for_medium_score(self):
        """Debería identificar score medio."""
        score = Score(0.5)
        assert score.is_medium()

    def test_is_low_returns_true_for_low_score(self):
        """Debería identificar score bajo."""
        score = Score(0.3)
        assert score.is_low()

    def test_is_very_high_returns_true_for_very_high_score(self):
        """Debería identificar score muy alto."""
        score = Score(0.95)
        assert score.is_very_high()

    def test_is_very_low_returns_true_for_very_low_score(self):
        """Debería identificar score muy bajo."""
        score = Score(0.05)
        assert score.is_very_low()

    def test_level_property_returns_correct_level(self):
        """Debería retornar nivel correcto."""
        assert Score(0.95).level == "very_high"
        assert Score(0.75).level == "high"
        assert Score(0.5).level == "medium"
        assert Score(0.3).level == "low"
        assert Score(0.05).level == "very_low"


class TestScoreConversions:
    """Tests para conversiones."""

    def test_percentage_property(self):
        """Debería convertir a porcentaje."""
        score = Score(0.75)
        assert score.percentage == 75.0

    def test_percentage_str_property(self):
        """Debería formatear como string de porcentaje."""
        score = Score(0.756)
        assert score.percentage_str == "75.6%"

    def test_to_float_method(self):
        """Debería convertir a float explícitamente."""
        score = Score(0.8)
        assert score.to_float() == 0.8
        assert isinstance(score.to_float(), float)

    def test_float_conversion(self):
        """Debería convertir a float implícitamente."""
        score = Score(0.6)
        assert float(score) == 0.6


class TestScoreMathOperations:
    """Tests para operaciones matemáticas."""

    def test_adjust_by_positive_amount(self):
        """Debería ajustar por cantidad positiva."""
        score = Score(0.5)
        adjusted = score.adjust_by(0.2)
        assert adjusted.value == 0.7

    def test_adjust_by_negative_amount(self):
        """Debería ajustar por cantidad negativa."""
        score = Score(0.5)
        adjusted = score.adjust_by(-0.2)
        assert adjusted.value == 0.3

    def test_adjust_by_clamped_at_maximum(self):
        """Debería limitar al máximo."""
        score = Score(0.9)
        adjusted = score.adjust_by(0.5)
        assert adjusted.value == 1.0

    def test_adjust_by_clamped_at_minimum(self):
        """Debería limitar al mínimo."""
        score = Score(0.2)
        adjusted = score.adjust_by(-0.5)
        assert adjusted.value == 0.0

    def test_multiply_by_factor(self):
        """Debería multiplicar por factor."""
        score = Score(0.5)
        multiplied = score.multiply_by(1.5)
        assert multiplied.value == 0.75

    def test_multiply_by_clamped_at_maximum(self):
        """Debería limitar al máximo al multiplicar."""
        score = Score(0.8)
        multiplied = score.multiply_by(2.0)
        assert multiplied.value == 1.0

    def test_multiply_by_negative_raises_error(self):
        """Debería lanzar error con factor negativo."""
        score = Score(0.5)
        with pytest.raises(ValueError) as exc_info:
            score.multiply_by(-1.0)
        assert "non-negative" in str(exc_info.value)

    def test_combine_with_equal_weight(self):
        """Debería combinar con peso igual (promedio)."""
        score1 = Score(0.6)
        score2 = Score(0.8)
        combined = score1.combine_with(score2)
        assert combined.value == 0.7

    def test_combine_with_custom_weight(self):
        """Debería combinar con peso personalizado."""
        score1 = Score(0.6)
        score2 = Score(0.8)
        combined = score1.combine_with(score2, weight=0.75)
        assert combined.value == pytest.approx(0.75)

    def test_combine_with_invalid_weight_raises_error(self):
        """Debería lanzar error con peso inválido."""
        score1 = Score(0.5)
        score2 = Score(0.7)
        with pytest.raises(ValueError) as exc_info:
            score1.combine_with(score2, weight=1.5)
        assert "between 0.0 and 1.0" in str(exc_info.value)

    def test_average_with_multiple_scores(self):
        """Debería calcular promedio con múltiples scores."""
        score1 = Score(0.5)
        score2 = Score(0.7)
        score3 = Score(0.9)
        avg = score1.average_with(score2, score3)
        assert avg.value == pytest.approx(0.7)

    def test_average_with_single_score(self):
        """Debería calcular promedio con un solo score."""
        score1 = Score(0.6)
        score2 = Score(0.8)
        avg = score1.average_with(score2)
        assert avg.value == 0.7

    def test_invert_score(self):
        """Debería invertir score."""
        score = Score(0.3)
        inverted = score.invert()
        assert inverted.value == 0.7


class TestScoreComparisons:
    """Tests para comparaciones."""

    def test_meets_threshold_returns_true_when_above(self):
        """Debería cumplir umbral cuando está arriba."""
        score = Score(0.8)
        assert score.meets_threshold(0.7)

    def test_meets_threshold_returns_true_when_equal(self):
        """Debería cumplir umbral cuando es igual."""
        score = Score(0.7)
        assert score.meets_threshold(0.7)

    def test_meets_threshold_returns_false_when_below(self):
        """Debería no cumplir umbral cuando está debajo."""
        score = Score(0.6)
        assert not score.meets_threshold(0.7)

    def test_meets_threshold_with_invalid_threshold_raises_error(self):
        """Debería lanzar error con umbral inválido."""
        score = Score(0.5)
        with pytest.raises(ValueError):
            score.meets_threshold(1.5)

    def test_less_than_comparison(self):
        """Debería comparar menor que."""
        score1 = Score(0.5)
        score2 = Score(0.7)
        assert score1 < score2
        assert not score2 < score1

    def test_less_than_or_equal_comparison(self):
        """Debería comparar menor o igual."""
        score1 = Score(0.5)
        score2 = Score(0.7)
        score3 = Score(0.5)
        assert score1 <= score2
        assert score1 <= score3

    def test_greater_than_comparison(self):
        """Debería comparar mayor que."""
        score1 = Score(0.7)
        score2 = Score(0.5)
        assert score1 > score2
        assert not score2 > score1

    def test_greater_than_or_equal_comparison(self):
        """Debería comparar mayor o igual."""
        score1 = Score(0.7)
        score2 = Score(0.5)
        score3 = Score(0.7)
        assert score1 >= score2
        assert score1 >= score3

    def test_equality_comparison(self):
        """Debería comparar igualdad."""
        score1 = Score(0.5)
        score2 = Score(0.5)
        score3 = Score(0.7)
        assert score1 == score2
        assert not score1 == score3

    def test_inequality_comparison(self):
        """Debería comparar desigualdad."""
        score1 = Score(0.5)
        score2 = Score(0.7)
        assert score1 != score2


class TestScoreImmutability:
    """Tests para inmutabilidad."""

    def test_score_is_immutable(self):
        """Debería ser inmutable."""
        score = Score(0.5)
        with pytest.raises(AttributeError):
            score.value = 0.7  # type: ignore

    def test_operations_return_new_instances(self):
        """Operaciones deberían retornar nuevas instancias."""
        original = Score(0.5)
        adjusted = original.adjust_by(0.2)

        assert original.value == 0.5
        assert adjusted.value == 0.7
        assert original is not adjusted


class TestScoreHashability:
    """Tests para hashability."""

    def test_score_is_hashable(self):
        """Debería ser hashable."""
        score = Score(0.5)
        hash_value = hash(score)
        assert isinstance(hash_value, int)

    def test_can_use_in_set(self):
        """Debería poder usarse en set."""
        score1 = Score(0.5)
        score2 = Score(0.7)
        score3 = Score(0.5)

        score_set = {score1, score2, score3}
        assert len(score_set) == 2  # score1 y score3 son iguales

    def test_can_use_as_dict_key(self):
        """Debería poder usarse como key de dict."""
        score1 = Score(0.5)
        score2 = Score(0.7)

        score_dict = {score1: "low", score2: "high"}
        assert score_dict[score1] == "low"
        assert score_dict[score2] == "high"


class TestScoreStringRepresentation:
    """Tests para representaciones string."""

    def test_str_without_description(self):
        """Debería formatear string sin descripción."""
        score = Score(0.756)
        assert str(score) == "75.6%"

    def test_str_with_description(self):
        """Debería formatear string con descripción."""
        score = Score(0.8, description="Quality")
        assert str(score) == "Quality: 80.0%"

    def test_repr_without_description(self):
        """Debería formatear repr sin descripción."""
        score = Score(0.75)
        assert repr(score) == "Score(value=0.75)"

    def test_repr_with_description(self):
        """Debería formatear repr con descripción."""
        score = Score(0.8, description="Quality")
        assert repr(score) == "Score(value=0.80, description='Quality')"
