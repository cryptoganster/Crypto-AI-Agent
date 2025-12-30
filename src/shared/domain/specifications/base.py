"""Base Specification Pattern para validaciones de dominio."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ValidationResult:
    """Resultado de validación con detalles del error."""

    is_valid: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    @staticmethod
    def success() -> "ValidationResult":
        """Crea resultado exitoso."""
        return ValidationResult(is_valid=True)

    @staticmethod
    def failure(message: str, code: Optional[str] = None) -> "ValidationResult":
        """Crea resultado fallido con mensaje y código."""
        return ValidationResult(is_valid=False, error_message=message, error_code=code)


class Specification(ABC, Generic[T]):
    """
    Base class para Specification Pattern.

    Encapsula reglas de validación reutilizables y componibles.

    Example:
        >>> score_spec = ScoreRangeSpecification("quality_score")
        >>> result = score_spec.is_satisfied_by(0.8)
        >>> assert result.is_valid

        >>> # Composición
        >>> combined = score_spec.and_(NonEmptyStringSpecification("category"))
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> ValidationResult:
        """
        Verifica si el candidato satisface la especificación.

        Args:
            candidate: Valor a validar

        Returns:
            ValidationResult con resultado y detalles
        """
        pass

    def and_(self, other: "Specification[T]") -> "Specification[T]":
        """Combina con otra specification usando lógica AND."""
        from .composite_specs import AndSpecification

        return AndSpecification(self, other)

    def or_(self, other: "Specification[T]") -> "Specification[T]":
        """Combina con otra specification usando lógica OR."""
        from .composite_specs import OrSpecification

        return OrSpecification(self, other)

    def not_(self) -> "Specification[T]":
        """Niega esta specification."""
        from .composite_specs import NotSpecification

        return NotSpecification(self)
