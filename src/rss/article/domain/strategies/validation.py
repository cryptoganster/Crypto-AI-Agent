"""Validation strategies para Article aggregate.

Implementa Strategy Pattern para eliminar validación con strings mágicos.
"""

from abc import ABC, abstractmethod
from typing import Any

from src.rss.article.domain.exceptions import (
    EmptyStringException,
    InvalidScoreException,
)
from src.shared.domain.specifications.non_empty_string_spec import (
    NonEmptyStringSpecification,
)
from src.shared.domain.specifications.score_range_spec import ScoreRangeSpecification


class ValidationStrategy(ABC):
    """Strategy base para validación."""

    @abstractmethod
    def validate(self, value: Any, param_name: str) -> None:
        """
        Valida un valor.

        Args:
            value: Valor a validar
            param_name: Nombre del parámetro (para mensajes de error)

        Raises:
            DomainException: Si la validación falla
        """
        pass


class ScoreValidationStrategy(ValidationStrategy):
    """Strategy para validar scores (0.0-1.0)."""

    def validate(self, value: Any, param_name: str) -> None:
        """Valida que el valor sea un score válido entre 0 y 1."""
        spec = ScoreRangeSpecification(param_name)
        result = spec.is_satisfied_by(value)
        if not result.is_valid:
            error_msg = result.error_message or f"Invalid score for {param_name}"
            raise InvalidScoreException(error_msg, value)


class NonEmptyStringValidationStrategy(ValidationStrategy):
    """Strategy para validar strings no vacíos."""

    def validate(self, value: Any, param_name: str) -> None:
        """Valida que el valor sea un string no vacío."""
        spec = NonEmptyStringSpecification(param_name)
        result = spec.is_satisfied_by(value)
        if not result.is_valid:
            error_msg = result.error_message or f"Empty string for {param_name}"
            raise EmptyStringException(error_msg, param_name)
