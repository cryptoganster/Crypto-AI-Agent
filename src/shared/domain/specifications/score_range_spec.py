"""Specification para validar scores en rango válido."""

from .base import Specification, ValidationResult
from .constants import SCORE_MAX, SCORE_MIN


class ScoreRangeSpecification(Specification[float]):
    """
    Valida que un score esté en el rango [0.0, 1.0].

    Usado para validar quality_score, readability_score,
    validation_score, confidence, similarity_score, etc.

    Example:
        >>> spec = ScoreRangeSpecification("quality_score")
        >>> result = spec.is_satisfied_by(0.8)
        >>> assert result.is_valid

        >>> result = spec.is_satisfied_by(1.5)
        >>> assert not result.is_valid
        >>> assert result.error_code == "OUT_OF_RANGE"
    """

    def __init__(self, param_name: str = "score"):
        """
        Inicializa specification.

        Args:
            param_name: Nombre del parámetro para mensajes de error
        """
        self.param_name = param_name

    def is_satisfied_by(self, score: float) -> ValidationResult:
        """
        Verifica que score esté en rango válido.

        Args:
            score: Valor a validar

        Returns:
            ValidationResult con resultado y detalles
        """
        if not isinstance(score, (int, float)):
            return ValidationResult.failure(
                f"{self.param_name} debe ser numérico, recibido: {type(score).__name__}",
                "INVALID_TYPE",
            )

        if not (SCORE_MIN <= score <= SCORE_MAX):
            return ValidationResult.failure(
                f"{self.param_name} debe estar entre {SCORE_MIN} y {SCORE_MAX}, recibido: {score}",
                "OUT_OF_RANGE",
            )

        return ValidationResult.success()
