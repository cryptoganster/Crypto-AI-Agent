"""Excepciones específicas para Article aggregate."""

from typing import Any, List

from src.shared.kernel.errors import ValidationException


class InvalidScoreException(ValidationException):
    """
    Score fuera del rango válido [0.0, 1.0].

    Usado para quality_score, readability_score, validation_score, confidence.

    Esta excepción hereda de ValidationException del shared kernel,
    proporcionando compatibilidad con el sistema de manejo de errores.
    """

    def __init__(self, message: str, score: float):
        """
        Inicializa excepción.

        Args:
            message: Mensaje de error descriptivo
            score: Valor del score inválido
        """
        super().__init__(
            message,
            errors=[{"field": "score", "message": message, "value": score}],
        )
        self.score = score


class EmptyStringException(ValidationException):
    """
    String requerido está vacío o solo contiene espacios.

    Usado para category, language_code, error_type, validated_by, etc.

    Esta excepción hereda de ValidationException del shared kernel,
    proporcionando compatibilidad con el sistema de manejo de errores.
    """

    def __init__(self, message: str, param_name: str):
        """
        Inicializa excepción.

        Args:
            message: Mensaje de error descriptivo
            param_name: Nombre del parámetro que está vacío
        """
        super().__init__(
            message,
            errors=[{"field": param_name, "message": message}],
        )
        self.param_name = param_name
