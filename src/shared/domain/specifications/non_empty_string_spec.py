"""Specification para validar strings no vacíos."""

from .base import Specification, ValidationResult


class NonEmptyStringSpecification(Specification[str]):
    """
    Valida que un string no esté vacío (incluyendo whitespace).

    Usado para validar category, language_code, error_type,
    error_message, validated_by, author, title, etc.

    Example:
        >>> spec = NonEmptyStringSpecification("category")
        >>> result = spec.is_satisfied_by("Technology")
        >>> assert result.is_valid

        >>> result = spec.is_satisfied_by("")
        >>> assert not result.is_valid
        >>> assert result.error_code == "EMPTY_STRING"

        >>> result = spec.is_satisfied_by("   ")
        >>> assert not result.is_valid
    """

    def __init__(self, param_name: str):
        """
        Inicializa specification.

        Args:
            param_name: Nombre del parámetro para mensajes de error
        """
        self.param_name = param_name

    def is_satisfied_by(self, value: str) -> ValidationResult:
        """
        Verifica que string no esté vacío.

        Args:
            value: String a validar

        Returns:
            ValidationResult con resultado y detalles
        """
        if not isinstance(value, str):
            return ValidationResult.failure(
                f"{self.param_name} debe ser string, recibido: {type(value).__name__}",
                "INVALID_TYPE",
            )

        if not value or not value.strip():
            return ValidationResult.failure(
                f"{self.param_name} no puede estar vacío", "EMPTY_STRING"
            )

        return ValidationResult.success()
